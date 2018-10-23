import rpyc
import UnityEditor
import UnityEngine
import threading
import time
import subprocess

rpyc_server = None
rpyc_server_thread = None
client_connection = None
client_connection_lock = threading.Condition()

client_thread = None

# list of tuples: (function_name, args)
to_execute_on_client = []

process_qt_events = False

# in seconds
delay_between_process_events = 0.5
last_process_events_time = 0

class PollingServer(rpyc.utils.server.OneShotServer):
    def __init__(self, service, hostname = "", ipv6 = False, port = 0,
            backlog = 10, reuse_addr = True, authenticator = None, registrar = None,
            auto_register = None, protocol_config = {}, logger = None, listener_timeout = 0.5,
            socket_path = None):
        
        # Tuple of (OneShotServer instance, data)
        self._to_dispatch = None
        
#        self._lock = threading.Lock()
        self._dispatch_lock = threading.Condition()
        
        super(PollingServer,self).__init__( service=service, 
                                        hostname = hostname,
                                        ipv6 = ipv6, 
                                        port = port,
                                        backlog = backlog, 
                                        reuse_addr = reuse_addr, 
                                        authenticator = authenticator,
                                        registrar = registrar,
                                        auto_register = auto_register, 
                                        protocol_config = protocol_config, 
                                        logger = logger, 
                                        listener_timeout = listener_timeout,
                                        socket_path = socket_path)

    def _accept_method(self, sock):
        super(PollingServer,self)._accept_method(sock)

class PollingConnection(rpyc.core.service.Connection):
    def _dispatch(self, data):
        global rpyc_server
        
        # This needs to be dispatched from the main thread
        with rpyc_server._dispatch_lock:
            # Save the data
            rpyc_server._to_dispatch = (super(PollingConnection,self), data)
            rpyc_server._dispatch_lock.wait()

class MyService(rpyc.core.service.SlaveService):
    _protocol = PollingConnection
    
    def stop_server(self):
        UnityEngine.Debug.Log('[rpyc-server] Got request to stop server from client')
        stop()

def onApplicationUpdate():
    # We need to give the Python interpreter some time to run the server thread
    # TODO: See if we can determine whether there is a rpc-call in progress in 
    # the server thread before doing so
    # Is there something to dispatch from the client to our main thread?
    if rpyc_server:
        with rpyc_server._dispatch_lock:
            if rpyc_server._to_dispatch:
                try:
                    # dispatch
                    (server,data) = rpyc_server._to_dispatch
                    server._dispatch(data)
                except:
                    pass
                finally:
                    rpyc_server._to_dispatch = None
            
            rpyc_server._dispatch_lock.notify()
            
    if process_qt_events:
        process_events_on_client()
            
    time.sleep(0.01)
    
def start():
    # We will "pump" the Python interpreter from this callback
    # TODO: Is this only adding our "delegate" or replacing them all with 
    # only ours
    global rpyc_server
    global rpyc_server_thread
    UnityEngine.Debug.Log("[rpyc-server] (%s) Starting server"%threading._get_ident())
    rpyc_server = PollingServer(MyService, port=18861)
    rpyc_server_thread = threading.Thread(target = rpyc_server.start, name = "rpyc_server")
    rpyc_server_thread.start()
    UnityEngine.Debug.Log("[rpyc-server] (%s) Server started"%threading._get_ident())
    
    UnityEditor.EditorApplication.update = UnityEditor.EditorApplication.CallbackFunction(onApplicationUpdate)
    

def stop():
    global rpyc_server
    global rpyc_server_thread
    global client_connection
    global client_thread

    if rpyc_server:
        rpyc_server.close()
        UnityEngine.Debug.Log('[rpyc-server] (%s) Server stopped'%threading._get_ident())
    rpyc_server = None
    rpyc_server_thread = None

    if client_connection:    
        client_connection.close()
        UnityEngine.Debug.Log('[rpyc-server] (%s) Disconnected from client'%threading._get_ident())
    client_connection = None
    client_thread = None
    
    process_qt_events = False
    
def client_thread_loop():
    """ 
    This function sends requests to the client. It is ran on a separated 
    thread so we do not block the server main thread on the client
    (would easily result in deadlocks as the client is often blocked on 
    the server main thread
    """
    global client_connection
    global client_connection_lock

    UnityEngine.Debug.Log('[rpyc-server] [client_thread] Started client_thread_loop')
    while True:
        function_name = None
        args = None
        with client_connection_lock:
            if not to_execute_on_client:
                client_connection_lock.wait()
            
            # do not keep that lock while waiting on the client. Create a copy of the data instead
            (function_name, args) = to_execute_on_client.pop(0)

        client_func = eval('client_connection.root.%s'%function_name)
        client_func(args);
            

def queue_client_func(func, args):
    ensure_client_connection()
    
    with client_connection_lock:
        to_execute_on_client.append((func,args))
        client_connection_lock.notify()            

def ensure_client_connection():
    global client_connection
    global client_thread
    
    with client_connection_lock:
        # Is the client alive?
        if not client_connection:
            UnityEngine.Debug.Log('[rpyc-server] Starting client process')            
            
            # start the client process (will create the client rpyc server
            subprocess.Popen(["python", "D:/GoogleDrive/ImgSpc/ut/Uni-67748 Brainstorm ideas SG integration, artist can use SG 247/rpyc/pollingServer/startClient_unity.py"], close_fds=True)
            
            UnityEngine.Debug.Log('[rpyc-server] Client process started')
    
            UnityEngine.Debug.Log('[rpyc-server] Connecting to client')
            try:
                client_connection = rpyc.connect('localhost', 18862)
                UnityEngine.Debug.Log('[rpyc-server] Connected to client')
                UnityEngine.Debug.Log('[rpyc-server] Starting client_thread')
                client_thread = threading.Thread(target = client_thread_loop, name = "client_connection")
                client_thread.start()
            except:
                UnityEngine.Debug.Log('[rpyc-server] Unable to connect to client')
                
        if not client_connection:
            client_thread = None

def run_python_code_on_client(python_code):
    """
    Queues a script to execute. We will execute it next time unity calls back into 
    the server 
    """
    queue_client_func('execute', python_code)
    
def run_python_file_on_client(python_file):
    """
    Queues a file to execute. We will execute it next time unity calls back into 
    the server 
    """
    queue_client_func('execute', 'execfile(\"%s\")'%python_file)

def process_events_on_client():
    global client_connection
    global last_process_events_time
    global rpyc_server

    curr_time = time.time()
    if (curr_time - last_process_events_time) < delay_between_process_events:
        return

    with client_connection_lock:
        for (function_name,_) in to_execute_on_client:
            if function_name == 'process_qt_events':
                # Do not accumulate process qt events messages
                return  

    queue_client_func('process_qt_events', None)
    
def start_processing_qt_events():
    global process_qt_events
    process_qt_events = True;    
    
def stop_processing_qt_events():
    global process_qt_events
    process_qt_events = False;    

def process_qt_events_once():
    process_events_on_client()
        