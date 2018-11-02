from unity_client import DefaultUnityClientService,log

_shotgun_is_initialized = False    

# The entry point, called by the client init script
def on_init_client(client):
    """
    client is an instance of UnityClient
    """
    log('[sg] In on_init_client')
    client.register_idle_callback(on_idle)
    client.register_service(ShotgunClientService)
    
def on_idle():
    try:
        from sgtk.platform.qt import QtGui
        QtGui.QApplication.instance().processEvents() 
    except:
        pass

class ShotgunClientService(DefaultUnityClientService):
    def bootstrap_shotgun(self,path_to_bootstrap):
        global _shotgun_is_initialized
        log('[sg] Got bootstrap_shotgun ("%s"). _shotgun_is_initialized = %s'%(path_to_bootstrap,_shotgun_is_initialized))
        if _shotgun_is_initialized:
            return
        
        execfile(path_to_bootstrap)
        _shotgun_is_initialized = True

        log('[sg] Shotgun has been initialized')
