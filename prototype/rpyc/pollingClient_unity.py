import rpyc
import time

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
#                self._connection = rpyc.classic.connect('localhost')
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
    def execute(self, stringToExecute):
        self._connection.root.execute(stringToExecute) 

if __name__ == "__main__":
    conn = UnityConnection()
    conn.connect()
    
    cnt = 0
    while True:
        print("sending print('Cnt = %s')"%cnt)
        conn.execute("import UnityEngine")
        conn.execute("UnityEngine.Debug.Log('Cnt = %s')"%cnt)
        time.sleep(1)
        cnt += 1
    
    print('Bye')

