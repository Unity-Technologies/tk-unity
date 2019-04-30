import pprint
import json

def get_metadata(logger, required_env):
    import sgtk
    engine = sgtk.platform.current_engine()
    sg = engine.shotgun
    
    entity_type = required_env['SHOTGUN_ENTITY_TYPE']
    entity_id   = int(required_env['SHOTGUN_ENTITY_ID'])
    
    metadata_json = None
    if entity_type == "Note":
        metadata_json = get_metadata_from_version(logger, sg, get_version_from_note(sg, entity_type, entity_id))
    else:
        metadata_json = get_metadata_from_version(logger, sg, {"type" : entity_type, "id" : entity_id})
        
    required_env = set_context_from_entity(sg, required_env)    
    
    metadata = None
    if metadata_json:
        frame_number = get_frame_from_note(sg, {"type" : entity_type, "id" : entity_id})
        if frame_number:
            temp_metadata = json.loads(metadata_json)
            temp_metadata["frameNumber"] = frame_number
            metadata_json = json.dumps(temp_metadata)
        
        logger.debug('Found metadata on the entity: ' + pprint.pformat(metadata_json))
        
        # Add the metadata to the environment for later, faster access
        required_env["SHOTGUN_UNITY_METADATA"] = metadata_json
        
        # Extract the dict
        try:
            metadata = json.loads(metadata_json)
        except Exception, e:
            logger.warning('Exception while parsing the sg_unity_metadata field: {}. The JSON data is probably invalid and will be ignored'.format(e))
    else:
        logger.debug('Could not find a "sg_unity_metadata" field for the context entity')
        
    return metadata

def get_metadata_from_version(logger, sg, version_entity):
    unity_metadata_json = None
    try:
        metadata_entity = sg.find_one(version_entity["type"],[["id", "is", version_entity["id"]]], ['sg_unity_metadata', 'description'])
        logger.debug('The context entity is ' + str(metadata_entity))
        unity_metadata_json = metadata_entity['sg_unity_metadata']
    except:
        # No metadata for this entity
        return None
        
    if unity_metadata_json and type(unity_metadata_json) != str:
        logger.warning('The sg_unity_metadata field is expected to be of type "str". It is "{}" instead. Its value will be ignored'.format(type(unity_metadata_json)))
        return None

    return unity_metadata_json

def get_frame_from_note(sg, note_entity):
    #   'attachments': [{'type': 'Attachment', 'id': 1668, 'name': 'annot_version_7199.107.png'}], 
    entity = sg.find_one(note_entity["type"], [["id", "is", note_entity["id"]]], ["attachments"])
    
    attachments = entity.get("attachments", None)
    if not attachments:
        return None
        
    name = attachments[0]["name"]
    tokens = name.split(".")
    if len(tokens) < 3:
        return None
    return tokens[1] # frame number

def set_context_from_entity(sg, required_env):
    entity_type = required_env['SHOTGUN_ENTITY_TYPE']
    entity_id   = int(required_env['SHOTGUN_ENTITY_ID'])
    
    def set_entity(entity_dict):
        required_env['SHOTGUN_ENTITY_TYPE'] = entity_dict["type"]
        required_env['SHOTGUN_ENTITY_ID'] = str(entity_dict["id"])
    
    # The context for version and note entities do not by themselves contain
    # enough information to get a useful context in Unity.
    # Therefore if this entity is a Version or Note, then do the following:
    # - If linked to a task, set the task as the context
    # - Else if linked to an asset/shot, set this as the context
    # - Else set the context to be the project
    if entity_type != "Note" and entity_type != "Version":
        return required_env
    
    entity = None
    if entity_type == "Note":
        # Example Note:
        # {
        #   'tasks': [{'type': 'Task', 'id': 5893, 'name': 'Layout'}], 
        #   'note_links': [{'type': 'Shot', 'id': 1216, 'name': 'DavidShot'}, {'type': 'Version', 'id': 7199, 'name': 'DavidShot-Layout.mp4'}],
        #   'project': {'type': 'Project', 'id': 86, 'name': 'Adagio'}, 'type': 'Note', 'id': 6464}
        entity = sg.find_one(entity_type, [["id", "is", entity_id]], ["tasks", "note_links", "project"])
    else:
        # Example Version:
        # {
        #   'project': {'type': 'Project', 'id': 86, 'name': 'Adagio'},
        #   'entity': {'type': 'Shot', 'id': 1216, 'name': 'DavidShot'},
        #   'type': 'Version', 'sg_task': {'type': 'Task', 'id': 5893, 'name': 'Layout'}, 'id': 7199}
        entity = sg.find_one(entity_type, [["id", "is", entity_id]], ["sg_task", "entity", "project"])
    
    # if something goes wrong, don't fail just keep the same context
    if not entity:
        return required_env
        
    # extract task
    tasks = entity.get("tasks")
    if tasks:
        set_entity(tasks[0]) # just take the first task
        return required_env
    
    task = entity.get("sg_task")
    if task:
        set_entity(task)
        return required_env
    
    if entity_type == "Note":
        # try getting shot or asset context
        note_links = entity.get("note_links")
        if note_links:
            for i in range(0, len(note_links)):
                if note_links[i]["type"] == "Asset" or note_links[i]["type"] == "Shot":
                    set_entity(note_links[i])
                    return required_env
    else:
        link = entity.get("entity")
        if link:
            set_entity(link)
            return required_env
    
    # settle with project context
    project = entity.get("project")
    if project:
        set_entity(project)
    return required_env


def get_version_from_note(sg, entity_type, entity_id):
    # 'note_links': [{'type': 'Shot', 'id': 1216, 'name': 'DavidShot'}, {'type': 'Version', 'id': 7199, 'name': 'DavidShot-Layout.mp4'}], 
    entity = sg.find_one(entity_type, [["id", "is", entity_id]], ["note_links"])
    note_links = entity.get("note_links", None)
    if not note_links:
        return None
    
    for i in range(0, len(note_links)):
        if note_links[i]["type"] == "Version":
            return note_links[i]
    return None
    
