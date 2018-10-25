import rpyc
import threading

class PollingServerUtil:
    """
    Call init before starting your rpyc server
    Call close before stopping your rpyc server
    """
    # Tuple of (connection,data)
    _data_to_dispatch = None
    _dispatch_lock = None

    @classmethod
    def set_data_to_dispatch_and_wait(cls, connection, data):
        if not cls._dispatch_lock:
            # We are closing
            return
        
        with cls._dispatch_lock:
            cls._data_to_dispatch = (connection, data)
            
            # Block until the main thread dispatches the data
            cls._dispatch_lock.wait()
            
    @classmethod
    def dispatch_data(cls):
        # Should be called from the main thread
        if not cls._dispatch_lock:
            # We are closing
            return

        with cls._dispatch_lock:
            if cls._data_to_dispatch:
                try:
                    (connection, data) = cls._data_to_dispatch
                    connection._dispatch(data)
                except EOFError:
                    print('Connection error while dispatching data. Ignoring')

                # Reset, ready for new data 
                cls._data_to_dispatch = None
            
            # Wake the blocked thread
            cls._dispatch_lock.notify()
            
    @classmethod
    def init(cls):
        cls._data_to_dispatch = None
        cls._dispatch_lock = threading.Condition()

    @classmethod
    def close(cls):
        cls._data_to_dispatch = None
        cls._dispatch_lock = None
       
class PollingServer(rpyc.utils.server.OneShotServer):
    pass

class PollingConnection(rpyc.core.service.Connection):
    def _dispatch(self, data):
        # We got data to dispatch on a thread, it needs to be dispatched from 
        # the main thread
        PollingServerUtil.set_data_to_dispatch_and_wait(super(PollingConnection,self), data)

class PollingSlaveService(rpyc.core.service.SlaveService):
    _protocol = PollingConnection