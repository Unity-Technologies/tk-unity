import rpyc
import UnityEditor
import UnityEngine
import threading
import time
import subprocess
import polling_server
import os

rpyc_server = None
rpyc_server_thread = None
client_connection = None
client_connection_lock = None 

client_thread = None
finish_client_thread = False

# list of tuples: (function_name, args)
to_execute_on_client = []

# in seconds
delay_between_process_events = 0.5
last_process_events_time = 0

class MyService(polling_server.PollingSlaveService):
    def stop_server(self):
        UnityEngine.Debug.Log('[rpyc-server] Got request to stop server from client')
        stop()

def onApplicationUpdate():
    # It seems like this callback is not invoked frequently enough to get a good message pump rate.
    # TODO: See if there is a higher-frequency / more reliable callback we can get 
    polling_server.PollingServerUtil.dispatch_data()
            
    time.sleep(0.01)
    
def start():
    # We will "pump" the Python interpreter from this callback
    # TODO: Is this only adding our "delegate" or replacing them all with 
    # only ours
    global rpyc_server
    global rpyc_server_thread
    UnityEngine.Debug.Log("[rpyc-server] (%s) Starting server"%threading._get_ident())
    rpyc_server = polling_server.PollingServer(MyService, port=18861)
    polling_server.PollingServerUtil.init()

    rpyc_server_thread = threading.Thread(target = rpyc_server.start, name = "rpyc_server")
    rpyc_server_thread.start()
    
    UnityEngine.Debug.Log("[rpyc-server] (%s) Server started"%threading._get_ident())
    
    UnityEditor.EditorApplication.update = UnityEditor.EditorApplication.update.Combine(UnityEditor.EditorApplication.update,UnityEditor.EditorApplication.CallbackFunction(onApplicationUpdate))

def stop():
    global rpyc_server
    global rpyc_server_thread
    global client_connection
    global client_connection_lock
    global client_thread
    global finish_client_thread
    
    # Deal with the client connection first
    finish_client_thread = True
    
    if client_connection_lock:
        # Let the client thread exit first

        with client_connection_lock:
            # Unblock the client thread if required. It should finish since 
            # the connection has been closed and set to none
            client_connection_lock.notify()
        
        UnityEngine.Debug.Log('[rpyc-server] Finishing client thread')
        while client_thread.is_alive():
            UnityEngine.Debug.Log('[rpyc-server] Client thread is still alive. Waiting')
            # Could probably use a wait/notify here
            time.sleep(0.1)

        UnityEngine.Debug.Log('[rpyc-server] Client thread finished')

        # Notify the client process that we are leaving
        UnityEngine.Debug.Log('[rpyc-server] Notifying client process')
        client_connection.root.on_server_stop()

        UnityEngine.Debug.Log('[rpyc-server] Closing the connection to the client')
        client_connection.close()
        
        UnityEngine.Debug.Log('[rpyc-server] (%s) Disconnected from client'%threading._get_ident())
                
                
        UnityEngine.Debug.Log('[rpyc-server] client thread finished')
    
        client_connection = None
        client_thread = None
        client_connection_lock = None
    
    polling_server.PollingServerUtil.close()

    if rpyc_server:
        rpyc_server.close()
        rpyc_server = None
        UnityEngine.Debug.Log('[rpyc-server] Server stopped')
    
    while rpyc_server_thread.is_alive():
        UnityEngine.Debug.Log('[rpyc-server] Server thread is still alive. Waiting')
        time.sleep(1)
   
    rpyc_server_thread = None
    UnityEngine.Debug.Log('[rpyc-server] Server thread finished')
   

def client_thread_loop():
    """ 
    This function sends requests to the client. It is ran on a separated 
    thread so we do not block the server main thread on the client
    (would easily result in deadlocks as the client is often blocked on 
    the server main thread
    """
    global client_connection
    global client_connection_lock
    global to_execute_on_client
    global finish_client_thread
    
    # start fresh
    to_execute_on_client = []
    finish_client_thread = False

    UnityEngine.Debug.Log('[rpyc-server] [client_thread] Started client_thread_loop')
    while not finish_client_thread:
        function_name = None
        args = None
        with client_connection_lock:
            if not to_execute_on_client:
                client_connection_lock.wait()
            
            # do not keep that lock while waiting on the client. Create a copy of the data instead
            (function_name, args) = to_execute_on_client.pop(0)

        client_func = eval('client_connection.root.%s'%function_name)
        client_func(args);
        
    UnityEngine.Debug.Log('[rpyc-server] [client_thread] Exiting client thread')

def queue_client_func(func, args):
    ensure_client_connection()
    
    with client_connection_lock:
        to_execute_on_client.append((func,args))
        client_connection_lock.notify()            

def ensure_client_connection():
    global client_connection
    global client_thread
    global client_connection_lock

    if not client_connection_lock:
        client_connection_lock = threading.Condition()
    
    with client_connection_lock:
        # Is the client alive?
        if not client_connection:
            # Having a running thread without a connection does not make sense.
            # Start fresh
            client_thread = None
            
            UnityEngine.Debug.Log('[rpyc-server] Trying to connect to client')            
            try:
                client_connection = rpyc.connect('localhost', 18862)
                UnityEngine.Debug.Log('[rpyc-server] Connected to client')
            except:
                pass
            
            if not client_connection:
                UnityEngine.Debug.Log('[rpyc-server] Starting client process')            
            
                # start the client process (will create the client rpyc server
                unity_client_path = os.path.join(os.path.dirname(os.environ['SHOTGUN_UNITY_BOOTSTRAP_LOCATION']),"unity_client.py")
                subprocess.Popen(["python", unity_client_path], close_fds=True)
            
                UnityEngine.Debug.Log('[rpyc-server] Client process started')
                UnityEngine.Debug.Log('[rpyc-server] Connecting to client')
            try:
                client_connection = rpyc.connect('localhost', 18862)
                UnityEngine.Debug.Log('[rpyc-server] Connected to client')
            except:
                UnityEngine.Debug.Log('[rpyc-server] Unable to connect to client')

            if client_connection:    
                UnityEngine.Debug.Log('[rpyc-server] Starting client_thread')
                client_thread = threading.Thread(target = client_thread_loop, name = "client_connection")
                client_thread.start()

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

def bootstrap_shotgun_on_client(path_to_bootstrap):
    queue_client_func('bootstrap_shotgun', path_to_bootstrap)
