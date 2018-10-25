import rpyc
import time

connection = None

class UnityConnection:
    def __init__(self):
        self._connection = None
    
    def connect(self):
        try:
            self._connection.ping()
        except:
            self._connection = None
            
        while not self._connection:
            # Wait until
            print('Trying to connect to Unity')
            try:
                self._connection = rpyc.connect('localhost', 18861)
                print('  Connected')
            except:
                print('  Unable to connect. Trying again in 1 second')

            time.sleep(1)

    def ensure_connect(func):
        def func_wrapper(*args, **kwargs):
            # Expect a valid "self"
            while True:
                try:
                    args[0].connect()
                except:
                    raise TypeError

                try:                
                    # connect might succeed, but the actual func might still fail
                    return func(*args, **kwargs)
                except:
                    print('  Call to Func failed. Trying to connect again in 1 second')
                    time.sleep(1)
        
        return func_wrapper

    @ensure_connect
    def execute(self, string_to_execute):
        self._connection.root.execute(string_to_execute) 

    @ensure_connect
    def getmodule(self, module_name):
        the_module = self._connection.root.getmodule(module_name)
        return the_module
        
    
    @ensure_connect
    def call_module_method(self, module_name, method_name, *args, **kwargs):
        exec('%s = self._connection.root.getmodule("%s")'%(module_name, module_name))
        method = eval('%s.%s'%(module_name, method_name))
        method(*args, **kwargs)

    def stop_server(self):
        try:
            return self._connection.root.stop_server()
        except:
            pass

def get_unity_connection():
    global connection
    if not connection:
        connection = UnityConnection()
        connection.connect()
    
    return connection

def reset_unity_connection():
    global connection
    
    # Should we also explicitly disconnect the rpyc connection?
    connection = None
    