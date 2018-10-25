import rpyc
import threading
import sys
import os
import time
import polling_server

_shotgun_is_initialized = False    
class MyClientSlaveService(polling_server.PollingSlaveService):
    def execute(self, text):
        print('[rpyc-client] Executing %s'%text)
        
        try:
            super(MyClientSlaveService, self).execute(text)
        except:
            import traceback
            traceback.print_exc()
        print('[rpyc-client] Done executing %s'%text)
        
    def on_server_stop(self):
        print('[rpyc-client] Got on_server_stop. Resetting the connection')

        import unity_connection
        unity_connection.reset_unity_connection()

    def bootstrap_shotgun(self,path_to_bootstrap):
        global _shotgun_is_initialized
        print('[rpyc-client] Got bootstrap_shotgun ("%s"). _shotgun_is_initialized = %s'%(path_to_bootstrap,_shotgun_is_initialized))
        if _shotgun_is_initialized:
            return
        
        execfile(path_to_bootstrap)
        _shotgun_is_initialized = True

        print('[rpyc-client] Shotgun has been initialized')

if __name__ == "__main__":
    rpyc_client = polling_server.PollingServer(MyClientSlaveService, port=18862)
    polling_server.PollingServerUtil.init()
    
    rpyc_client_thread = threading.Thread(target = rpyc_client.start, name = "rpyc_client")
    rpyc_client_thread.start()
    
    while True:
        time.sleep(0.001)
        polling_server.PollingServerUtil.dispatch_data()
        
        try:
            from sgtk.platform.qt import QtGui
            QtGui.QApplication.instance().processEvents() 
        except:
            pass
        
    print("[rpyc-client] Bye")
        
