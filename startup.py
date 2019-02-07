import json
import os
import sys
import pprint
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation

class UnityLauncher(SoftwareLauncher):
    """
    Handles launching Unity executables. Automatically starts up
    a tk-unity engine with the current context in the new session
    of Unity.
    """
    
    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {
        "version": "[\d]+[\d.\[a-z\]]+"
    }

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string.
    EXECUTABLE_TEMPLATES = {
        "darwin": [
            "/Applications/Unity/Unity.app/Contents/MacOS/Unity",
            "/Applications/Unity/Hub/Editor/{version}/Unity.app/Contents/MacOS/Unity",
            "/Applications/{version}/Unity.app/Contents/MacOS/Unity",
        ],
        "win32": [
            "C:/Program Files/Unity/Editor/Unity.exe",
            "C:/Program Files/Unity{version}/Editor/Unity.exe",
            "C:/Program Files/Unity {version}/Editor/Unity.exe",
            "C:/Program Files/Unity/{version}/Editor/Unity.exe",
            "C:/Program Files/Unity/Hub/Editor/{version}/Editor/Unity.exe",            
            "D:/Program Files/{version}/Editor/Unity.exe",
            "D:/Program Files/Unity {version}/Editor/Unity.exe",
            "D:/Program Files/Unity{version}/Editor/Unity.exe",
            "D:/Program Files/Unity/{version}/Editor/Unity.exe",
            "D:/Unity Editors/{version}/Editor/Unity.exe"
        ],
        "linux2": [
            # TODO
        ]
    }
    
    HUB_EXECUTABLES = {
        "darwin": [
            # TODO
        ],
        "win32": [
            "C:/Users/{username}/AppData/Roaming/UnityHub/editors.json"
        ],
        "linux2": [
            # TODO
        ]
    }

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2018.2"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Unity in that will automatically
        load Toolkit and the tk-unity engine when Unity starts.

        :param str exec_path: Path to Unity executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}
        
        # Add std context and site info to the env. This will add stuff like which site to
        # connect to, what context to load, etc.
        required_env.update(self.get_standard_plugin_environment())

        # This will be read by Bootstrap.cs (com.unity.integrations.shotgun) 
        # from the C# plugin in UI to know where to pick up the
        # Toolkit code.
        required_env["SHOTGUN_UNITY_BOOTSTRAP_LOCATION"] = os.path.join(
            self.disk_location,
            "plugins",
            "basic",
            "bootstrap.py"
        )

        # Signals which engine instance from the environment is going to be used.
        required_env["SHOTGUN_ENGINE"] = self.engine_name

        # We do not support the file_to_open logic. Its value comes from the 
        # launch plug-in when users launch DCCs from a published file.
        # https://github.com/shotgunsoftware/tk-shotgun-launchpublish
        # https://github.com/shotgunsoftware/tk-config-default2/blob/master/env/publishedfile.yml#L27
        # https://github.com/shotgunsoftware/tk-config-default2/blob/master/env/includes/settings/tk-shotgun-launchpublish.yml

        # Here we try to find unity metadata on the context entity.
        # If the field exists and specifies a Unity project to open on startup,
        # We skip the project selection dialog
        import sgtk
        engine = sgtk.platform.current_engine()
        sg = engine.shotgun
        
        required_env = self.set_context_from_entity(required_env)
        
        entity_type = required_env['SHOTGUN_ENTITY_TYPE']
        entity_id   = int(required_env['SHOTGUN_ENTITY_ID'])
        try:
            entity = sg.find_one(entity_type,[["id", "is", entity_id]], ['sg_unity_metadata', 'description'])
            self.logger.debug('The context entity is ' + str(entity))
            unity_metadata_json = entity['sg_unity_metadata']
        except:
            # No metadata for this entity
            unity_metadata_json = None

        if unity_metadata_json and type(unity_metadata_json) != str:
            self.logger.warning('The sg_unity_metadata field is expected to be of type "str". It is "{}" instead. Its value will be ignored'.format(type(unity_metadata_json)))
            unity_metadata_json = None
            
        unity_metadata = None
        if unity_metadata_json:
            self.logger.debug('Found metadata on the entity: ' + pprint.pformat(unity_metadata_json))
            
            # Add the metadata to the environment for later, faster access
            required_env["SHOTGUN_UNITY_METADATA"] = unity_metadata_json
            
            # Extract the dict
            try:
                unity_metadata = json.loads(unity_metadata_json)
            except Exception, e:
                self.logger.warning('Exception while parsing the sg_unity_metadata field: {}. The JSON data is probably invalid and will be ignored'.format(e))
        else:
            self.logger.debug('Could not find a "sg_unity_metadata" field for the context entity')

        if unity_metadata and unity_metadata.has_key('projectPath'):
            args += ' -projectPath "{}"'.format(unity_metadata['projectPath'])

        self.logger.debug("Launch environment: %s", pprint.pformat(required_env))
        self.logger.debug("Launch arguments: %s", args)

        return LaunchInformation(exec_path, args, required_env)

    def set_context_from_entity(self, required_env):
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
        
        import sgtk
        engine = sgtk.platform.current_engine()
        sg = engine.shotgun
        
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
        tasks = entity.get("tasks", None)
        if tasks:
            set_entity(tasks[0]) # just take the first task
            return required_env
        
        task = entity.get("sg_task", None)
        if task:
            set_entity(task)
            return required_env
        
        if entity_type == "Note":
            # try getting shot or asset context
            note_links = entity.get("note_links", None)
            if note_links:
                for i in range(0, len(note_links)):
                    if note_links[i]["type"] == "Asset" or note_links[i]["type"] == "Shot":
                        set_entity(note_links[i])
                        return required_env
        else:
            link = entity.get("entity", None)
            if link:
                set_entity(link)
                return required_env
        
        # settle with project context
        project = entity.get("project", None)
        if project:
            set_entity(project)
        return required_env
        
    def scan_software(self):
        """
        Scan the file system for Unity executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for Unity executables...")

        # This piece of boiler-plate code scans for software based on the supported versions, and for every version
        # returned checks if the engine actually supports it.
        supported_sw_versions = []
        for sw_version in self._find_software():
            (supported, reason) = self._is_supported(sw_version)
            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" %
                    (sw_version, reason)
                )

        return supported_sw_versions

    ##########################################################################################
    # private methods

    def _find_software(self):
        """
        Find executables in the default install locations.
        
        Three different ways to find versions:
            1. If Unity Hub is installed, get versions from editors.json file
            2. Use default install location templates to glob for executable filesystem
            3. Try to get paths from UNITY_EDITOR_PATH environment variable if set
        """
        
        # all the discovered executables
        sw_versions = []
        
        # If Unity Hub is installed then try to get some of the versions from there
        editor_jsons = self.HUB_EXECUTABLES.get(sys.platform, [])
        import getpass
        username = getpass.getuser()
        for i in range(len(editor_jsons)):
            editor_json = editor_jsons[i].format(username = username)
            if os.path.exists(editor_json):
                with open(editor_json, "r") as f:
                    import json
                    data = json.load(f)
                    if not data:
                        continue
                    
                    for vals in data.values():
                        version = vals["version"]
                        exec_paths = vals["location"] # list of locations
                        if len(exec_paths) < 1:
                            continue
                        exec_path = exec_paths[0]
                        
                        sw_versions.append(
                            SoftwareVersion(
                                version,
                                "Unity",
                                exec_path,
                                os.path.join(self.disk_location, "icon_256.png")
                            )
                        )
        
        # all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_TEMPLATES.get(sys.platform, [])

        for executable_template in executable_templates:

            self.logger.debug("Processing template %s.", executable_template)

            executable_matches = self._glob_and_match(
                executable_template,
                self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all products from that executable.
            for (executable_path, key_dict) in executable_matches:

                # extract the matched keys form the key_dict (default to None if
                # not included)
                executable_version = key_dict.get("version")
                
                if not executable_version:
                    executable_version = "Unknown"
                
                self.logger.warning("Software was found: " + executable_path + ", " + executable_version)

                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        "Unity",
                        executable_path,
                        os.path.join(self.disk_location, "icon_256.png")
                    )
                )
                
        # also try to get from environment variable
        environ_paths = os.environ.get("UNITY_EDITOR_PATH")
        if not environ_paths:
            return sw_versions
        
        environ_paths = environ_paths.split(";")
        for executable_path in environ_paths:
            sw_versions.append(
                    SoftwareVersion(
                        "Unknown",
                        "Unity",
                        executable_path,
                        os.path.join(self.disk_location, "icon_256.png")
                    )
                )
                
        return sw_versions