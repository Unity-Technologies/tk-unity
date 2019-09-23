"""
The Unity client module for Shotgun. Responsible of customizing the client 
process in order to serve the Shotgun integration
"""

import unity_python.client.unity_client as unity_client

import imp
import os
import unity_python.common.scheduling as scheduling
import sys
import threading
import time
import traceback

# Fix threading
if sys.version_info.major < 3:
    import Queue as queue
    def fix_threading():
        # thread.get_ident moved to threading.get_ident in py3.3
        import thread
        threading.get_ident = thread.get_ident
    fix_threading()
else:
    import queue

# Logging
_log_to_file = os.environ.get('UNITY_SHOTGUN_CLIENT_LOGFILE')
def log(msg):
    message = '[ShotgunClient] {}\n'.format(msg)
    if _log_to_file:
        with open(_log_to_file, 'a') as f:
            f.write(message)

    print(message)

# Keep a reference on the connection
_connection = None

# We only initialize Shotgun once in the client process
_shotgun_is_initialized = False

# The Shotgun service class and its instance
_service = None

# Number of attempts to reconnect to the server
_nb_connection_attempts = 100

### Unity API access
def GetUnityEngine():
    return _service.UnityEngine

def GetUnityEditor():
    return _service.UnityEditor

class ShotgunClientService(unity_client.UnityClientService):
    """
    The RPyC service class. Exposes all the services that are required for the 
    Shotgun integration
    """
    def exposed_client_name(self):
        return 'com.unity.integrations.shotgun'
    
    def exposed_on_server_shutdown(self, invite_retry):
        global _connection
        _connection.close()
        _connection = None

        if invite_retry:
            connect_to_unity(wait_for_server=True)
        else:
            super(ShotgunClientService, self).exposed_on_server_shutdown(invite_retry)
    
    @scheduling.exec_on_main_thread
    def exposed_execute_menu_item(self,menu_item):
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

    @scheduling.exec_on_main_thread
    def exposed_invoke_post_init_hook(self):
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

    def exposed_tk_unity_version(self):
        import sgtk
        return sgtk.platform.current_engine().version

        """
        Returns a string representing the version of tk-unity, e.g. "v0.9"
        """
        import sgtk
        return sgtk.platform.current_engine().version

@scheduling.exec_on_main_thread
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
        (module_file, module_path, module_desc) = imp.find_module(module_name, [dir_name])
        bootstrap_module = imp.load_module(module_name, module_file, module_path, module_desc)
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

def connect_to_unity(wait_for_server = False):
    global _connection

    if _connection:
        return

    if wait_for_server:
        time.sleep(2)

    # Try 10 times
    for i in range(_nb_connection_attempts):
        try:
            log('Trying to connect ({}/{})'.format(i+1, _nb_connection_attempts))
            _connection = unity_client.connect(_service)
        except:
            # Give the server time to restart
            import traceback
            log('Got Exception while connecting. Waiting for 1 second before trying again'.format())
            log('Exception stack trace:\n\n{}'.format(traceback.format_exc()))
            time.sleep(1)
        else:
            log('Connected')
            break
        
    if not _connection:
        log('Could not connect to Unity')
        return

    # Bootstrap Shotgun if not done already.
    bootstrap_shotgun()

def main_loop():            
    """
    Processes the Qt events and jobs that were dispatched from other threads
    """
    qapp = None
    while True:
        if not qapp:
            from sgtk.util.qt_importer import QtImporter
            qt = QtImporter()
            qapp = qt.QtGui.QApplication.instance()
        if qapp:
            qapp.processEvents()

        # Process jobs scheduled for the main thread
        scheduling.process_jobs()
        time.sleep(0.001) 

def main(service_class = ShotgunClientService):
    global _service

    # Initialize scheduling
    scheduling.initialize()

    # The service instance
    _service  = service_class()
    connect_to_unity(wait_for_server=False)    
    main_loop()

if __name__ == '__main__':
    # Avoid working in the main module
    import sg_client
    sg_client.main()
