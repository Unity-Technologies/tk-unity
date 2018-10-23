import rpyc
import threading
import sys
import os
import time


class MyClientSlaveService(rpyc.core.service.SlaveService):
    def execute(self, text):
        print('[rpyc-client] Executing %s'%text)
        try:
            super(MyClientSlaveService, self).execute(text)
        except:
            import traceback
            traceback.print_exc()

    def process_qt_events(self, text):
        try:
            from sgtk.platform.qt import QtGui
            QtGui.QApplication.instance().processEvents() 
        except:
            pass

if __name__ == "__main__":
    print("[rpyc-client] Starting the rpyc client")
    try:
        rpyc_client = rpyc.utils.server.OneShotServer(MyClientSlaveService, port=18862)

        print("[rpyc-client] rpyc_client = %s"%rpyc_client)
       
        # This will block the client in slave mode
        rpyc_client.start()
    except e:
        print("[rpyc-client] Got an exception %s"%e)
        
    print("[rpyc-client] Bye")
        
