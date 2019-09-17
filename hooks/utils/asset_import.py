from sg_client import GetUnityEditor, GetUnityEngine

import sgtk

import json
import os
import shutil

log = sgtk.LogManager.get_logger(__name__)


############# METADATA VERSION ################
# In case we need to write backward-compatible code, we store the userData
# version number along with the userData
_userdata_version = '1.0'

def import_file(src_file, asset_name, dst_dir):
    """
    src_file: Full file path, e.g. S:/imgspc/production/adagio/assets/Character/Ghost/MDL/publish/maya/Ghost.v002.fbx
    asset_name: The name of the asset, in Unity, e.g. Ghost
    dst_dir: The destination folder, e.g.  D:/projects/com.unity.integrations.shotgun/Shotgun/Assets
    """
    src_file = os.path.normpath(src_file)
    dst_dir = os.path.normpath(dst_dir)
    
    dst_file_path = os.path.join(dst_dir, '{}.fbx'.format(asset_name))

    try:
        shutil.copy2(src_file, dst_file_path)
    except IOError as e:
        import traceback, pprint
        log.error("IOError: {}".format(str(e)))
        log.error('Stack trace:\n\n{}'.format(pprint.pformat(traceback.format_stack())))
        
    log.info("importing asset {} ({} --> {}".format(asset_name, src_file, dst_file_path))

    GetUnityEditor().AssetDatabase.Refresh()
    
    project_path = GetUnityEngine().Application.dataPath

    # Store the src_file in the meta file
    # We use a json dictionary in order to allow studios to augment the metadata
     
    # get the src_file relative to assets. e.g. Assets/test.fbx instead of C:/src_file/to/Assets/test.fbx
    asset = os.path.join("Assets", os.path.relpath(dst_file_path, project_path))
    model_importer = GetUnityEditor().AssetImporter.GetAtPath(asset)
    if not model_importer:
        log.warning("Shotgun: Could not find importer for asset {}. Cannot add userData".format(asset))
        return

    userData = {
        'path'              : src_file,
        'userdata_version'  : _userdata_version
        }        
    
    model_importer.userData = json.dumps(userData)
    model_importer.SaveAndReimport()
