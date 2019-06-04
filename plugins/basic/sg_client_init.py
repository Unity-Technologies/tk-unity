"""
The Unity client init module for Shotgun. Responsible of customizing the client 
process in order to serve the Shotgun integration:
- Overrides the default rpyc service with one that adds an explicit bootstrap 
  function
- Installs an idle callback that will process Qt events
"""
import imp
import os
import unity_client

from unity_client_service import UnityClientService

# We only initialize Shotgun once in the client process
_shotgun_is_initialized = False    

def log(msg):
    unity_client.log('[sg] {}'.format(msg))

def on_init_client(client):
    """
    Registers the custom rpyc service and the idle callback
    """
    log('In on_init_client')
    
    client.register_idle_callback(on_idle)
    client.register_service(ShotgunClientService)
    
def on_idle():
    """
    Processes the Qt events, if there is an application
    """
    try:
        from sgtk.util.qt_importer import QtImporter
        qt = QtImporter()
        qt.QtGui.QApplication.instance().processEvents() 
    except Exception:
        pass

class ShotgunClientService(UnityClientService):
    """
    Custom rpyc service that overrides the default Unity client service
    """
    def bootstrap_shotgun(self,path_to_bootstrap):
        """
        Checks if Shotgun is already initialized. If not, executes the 
        bootstrap script
        """
        global _shotgun_is_initialized
        log('Got bootstrap_shotgun')
        if _shotgun_is_initialized:
            log('Shotgun is already initialized in the client process')
            return
        
        ret_val = -1
        try:
            # Use the imp module to bootstrap in order to get a return value
            (dir_name, file_name) = os.path.split(path_to_bootstrap)
            module_name = file_name.split('.')[0]
            
            log('Invoking bootstrap script ("{}")'.format(path_to_bootstrap))        
            (module_file, module_path, module_desc) = imp.find_module(module_name, [dir_name])
            bootstrap_module = imp.load_module(module_name, module_file, module_path, module_desc)
            ret_val = bootstrap_module.plugin_startup()
        except Exception, e:
            import traceback
            log('Got an exception while bootstrapping: {}'.format(e))
            log('Stack trace:\n\n{}'.format(traceback.format_exc()))
        
        if ret_val == 0:
            _shotgun_is_initialized = True
            log('Shotgun has been initialized in the client process')
        else:
            log('Shotgun has not been initialized in the client process')
            
        # Clear the progress bar in case we never got to 100%
        try:
            UnityEditor.EditorUtility.ClearProgressBar()
        except Exception:
            # It is possible that the progress bar is not displayed anymore, 
            # in which case we get an exception here
            pass
            