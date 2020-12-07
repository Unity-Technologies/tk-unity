"""
The Unity client module for Shotgun. Responsible of customizing the client 
process in order to serve the Shotgun integration
"""

import importlib.util
import os
import sys
import time
import traceback

# Logging
_log_to_file = os.environ.get('UNITY_SHOTGUN_CLIENT_LOGFILE')
def log(msg):
    message = '[ShotgunClient] {}\n'.format(msg)
    if _log_to_file:
        with open(_log_to_file, 'a') as f:
            f.write(message)

    print(message)

# We only initialize Shotgun once in the client process
_shotgun_is_initialized = False

# Number of attempts to reconnect to the server
_nb_connection_attempts = 100

### Unity API access
def GetUnityEngine():
    import UnityEngine
    return UnityEngine

def GetUnityEditor():
    import UnityEditor
    return UnityEditor
    
#### FUNCTIONS PREVIOUSLY IN CLIENT
def test_invoke_post_init_hook():
    """
    Invokes the post init hook
    """
    try:
        import sgtk
        sgtk.platform.current_engine().execute_hook_method('post_init_hook', 'on_post_init')
    except:
        import traceback
        log('Got exception while invoking the post init hook:')
        log('Exception stack trace:\n\n{}'.format(traceback.format_exc()))

def test_tk_unity_version():
    """
    Returns a string representing the version of tk-unity, e.g. "v0.9"
    """
    import sgtk
    version = sgtk.platform.current_engine().version
    return version
    
def test_execute_menu_item(menu_item):
    """
    Calls the menu item callback
    """
    try:
        import sgtk
        sgtk.platform.current_engine().call_menu_item_callback(menu_item)
    except:
        import traceback
        log('Got exception while executing menu item "{}"'.format(menu_item))
        log('Exception stack trace:\n\n{}'.format(traceback.format_exc()))
#### --------------------    

def bootstrap_shotgun():
    """
    Checks if Shotgun is already initialized. If not, executes the 
    bootstrap script.
    """
    global _shotgun_is_initialized
    if _shotgun_is_initialized:
        log('Shotgun is already initialized in the client process')
        return

    log('Requesting bootstrap')
    path_to_bootstrap = os.environ.get('SHOTGUN_UNITY_BOOTSTRAP_LOCATION')
    if not path_to_bootstrap:
        raise EnvironmentError('Unity was not launched from Shotgun (SHOTGUN_UNITY_BOOTSTRAP_LOCATION is not defined in the environment). Cannot bootstrap toolkit.')

    path_to_bootstrap = os.path.normpath(path_to_bootstrap)
    
    try:
        # Use the imp module to bootstrap in order to get a return value
        (dir_name, file_name) = os.path.split(path_to_bootstrap)
        module_name = file_name.split('.')[0]
        
        log('Invoking bootstrap script ("{}")'.format(path_to_bootstrap))
        spec = importlib.util.spec_from_file_location("bootstrap", path_to_bootstrap)
        bootstrap_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bootstrap_module)
        _shotgun_is_initialized = True if bootstrap_module.plugin_startup() == 0 else False
    except:
        import traceback
        log('Got an exception while bootstrapping:')
        log('Exception stack trace:\n\n{}'.format(traceback.format_exc()))
    
    if _shotgun_is_initialized:
        log('Shotgun has been initialized in the client process')
    else:
        log('Shotgun has not been initialized in the client process')
        
    # Clear the progress bar in case we never got to 100%
    try:
        GetUnityEditor().EditorUtility.ClearProgressBar()
    except Exception:
        # It is possible that the progress bar is not displayed anymore, 
        # in which case we get an exception here
        pass

qapp = None
def main_loop():            
    """
    Processes the Qt events and jobs that were dispatched from other threads
    """
    global qapp
    if not qapp:
        from sgtk.util.qt_importer import QtImporter
        qt = QtImporter()
        qapp = qt.QtGui.QApplication.instance()
    if qapp:
        qapp.processEvents()

if __name__ == '__main__':
    import UnityEngine
    UnityEngine.Debug.Log("entering main")
    # Avoid working in the main module
    import sg_client
    #sg_client.main()
    sg_client.bootstrap_shotgun()
