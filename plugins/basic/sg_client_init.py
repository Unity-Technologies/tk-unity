"""
The Unity client init module for Shotgun. Responsible of customizing the client 
process in order to serve the Shotgun integration:
- Overrides the default rpyc service with one that adds an explicit bootstrap 
  function
- Installs an idle callback that will process Qt events
"""

import unity_client

######### Coverage, used for testing #########
# Set WANT_UNITY_PYTHON_COVERAGE to enable coverage
import os
import imp
import tempfile

want_coverage = os.environ.has_key('WANT_UNITY_PYTHON_COVERAGE')
coverage_object = None
coverage_directory = None

if want_coverage:
    import coverage
######### Coverage, used for testing #########

from unity_client_service import UnityClientService

# We only initialize Shotgun once in the client process
_shotgun_is_initialized = False    

def log(msg):
    unity_client.log('[sg] {}'.format(msg))

def on_init_client(client):
    """
    Registers the custom rpyc service and the idle callback
    """
    global want_coverage
    
    log('In on_init_client')
    
    if want_coverage:
        global coverage_object
        global coverage_directory
        coverage_directory = tempfile.mkdtemp(suffix='-tk-unity-coverage')
        log('Coverage results will be located in %s when the client terminates'%coverage_directory)
        
        # Use the temp folder name in the coverage file name to make it unique
        coverage_file_name = os.path.split(coverage_directory)[-1]

        coverage_object = coverage.Coverage(data_file=os.path.join(coverage_directory,coverage_file_name))
        coverage_object.start()
    
    client.register_idle_callback(on_idle)
    client.register_service(ShotgunClientService)
    
def on_idle():
    """
    Processes the Qt events, if there is an application
    """
    try:
        from sgtk.platform.qt import QtGui
        QtGui.QApplication.instance().processEvents() 
    except:
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

    def on_server_stop(self, terminate_client):
        global want_coverage
        super(ShotgunClientService, self).on_server_stop(terminate_client)
        
        if terminate_client and want_coverage:
            global coverage_object
            global coverage_directory
            
            coverage_object.stop()
            coverage_object.save()
            
            log('Writing coverage results, this could take a moment')
            coverage_object.html_report(directory=coverage_directory, ignore_errors=True)
