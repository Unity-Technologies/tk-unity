"""
The Unity client init module for Shotgun. Responsible of customizing the client 
process in order to serve the Shotgun integration:
- Overrides the default rpyc service with one that adds an explicit bootstrap 
  function
- Installs an idle callback that will process Qt events
"""

######### Coverage, used for testing #########
# Set TK_UNITY_WANT_COVERAGE to enable coverage
import os
import tempfile

want_coverage = os.environ.has_key('TK_UNITY_WANT_COVERAGE')
coverage_object = None
coverage_directory = None

if want_coverage:
    import coverage
######### Coverage, used for testing #########

from unity_client import log
from unity_client_service import UnityClientService

# We only initialize Shotgun once in the client process
_shotgun_is_initialized = False    

def on_init_client(client):
    """
    Registers the custom rpyc service and the idle callback
    """
    global want_coverage
    
    log('[sg] In on_init_client')
    
    if want_coverage:
        global coverage_object
        global coverage_directory
        coverage_directory = tempfile.mkdtemp(suffix='-tk-unity-coverage')
        log('Coverage results will be located in %s when the client terminates'%coverage_directory)
        
        coverage_object = coverage.Coverage(data_file=os.path.join(coverage_directory,'tk-unity.coverage'))
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
        log('[sg] Got bootstrap_shotgun')
        if _shotgun_is_initialized:
            log('[sg] Shotgun is already initialized in the client process')
            return

        log('[sg] Invoking bootstrap script ("%s")'%path_to_bootstrap)        
        execfile(path_to_bootstrap)
        _shotgun_is_initialized = True

        log('[sg] Shotgun has been initialized in the client process')

    def on_server_stop(self, terminate_client):
        global want_coverage
        super(ShotgunClientService, self).on_server_stop(terminate_client)
        
        if terminate_client and want_coverage:
            global coverage_object
            global coverage_directory
            
            coverage_object.stop()
            coverage_object.save()
            
            log('Writing coverage results, this could take a moment')
            coverage_object.html_report(directory=coverage_directory)
