//#define DEBUG
using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using System.IO;
using Python.Runtime;

public class Bootstrap
{
    static string ImportServerString = @"
from unity_rpyc import unity_server as unity_server
";

    public static void RunPythonCodeOnClient(string pythonCodeToExecute)
    {
        string serverCode = ImportServerString + string.Format(
@"
unity_server.run_python_code_on_client('{0}')
",pythonCodeToExecute);

        UnityEngine.Debug.Log(string.Format("Running Python: {0}",pythonCodeToExecute));
        PythonRunner.RunString(serverCode);
        UnityEngine.Debug.Log("  Done running Python on Client");
    }

    public static void RunPythonFileOnClient(string pythonFileToExecute)
    {
        string serverCode = ImportServerString + string.Format(
@"
unity_server.run_python_file_on_client('{0}')
",pythonFileToExecute);

        UnityEngine.Debug.Log(string.Format("Running Python File: {0}",pythonFileToExecute));
        PythonRunner.RunString(serverCode);
        UnityEngine.Debug.Log("  Done running Python File on Client");
    }

    public static void CallStartServer(string clientInitPath = null)
    {
        string clientInitPathString;
        if (clientInitPath != null)
        {
            clientInitPath = clientInitPath.Replace("\\","/");
            clientInitPathString = string.Format("'{0}'",clientInitPath);
        }
        else
        {
            clientInitPathString = "None";
        }


        string serverCode = ImportServerString +
string.Format(@"
unity_server.start({0})
", clientInitPathString);

        UnityEngine.Debug.Log("Starting rpyc server...");
        PythonRunner.RunString(serverCode);
        UnityEngine.Debug.Log("rpyc server started");
    }

    public static void CallStopServer()
    {
        string serverCode = ImportServerString +
@"
unity_server.stop()
";

        UnityEngine.Debug.Log("Stopped rpyc server...");
        PythonRunner.RunString(serverCode);
        UnityEngine.Debug.Log("rpyc server stopped");
    }

    public static void CallBootstrap()
    {
        // Use the engine's rpyc client script
        string clientInitPath = System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION");
        clientInitPath = Path.GetDirectoryName(clientInitPath);
        clientInitPath = Path.Combine(clientInitPath,"sg_client_init.py");

        // First start the rpyc server
        CallStartServer(clientInitPath);

        string bootstrapScript = System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION");
        bootstrapScript = bootstrapScript.Replace(@"\","/");

        string serverCode = ImportServerString + string.Format(
@"
unity_server.call_remote_service('bootstrap_shotgun','{0}')
",bootstrapScript);

        UnityEngine.Debug.Log("Invoking Shotgun Toolkit bootstrap");
        PythonRunner.RunString(serverCode);

        PythonEngine.AddShutdownHandler(OnPythonShutdown);
    }

    [UnityEditor.Callbacks.DidReloadScripts]
    public static void OnReload()
    {
        CallBootstrap();
    }

    public static void OnPythonShutdown()
    {
        UnityEngine.Debug.Log("In Bootstrap.OnPythonShutdown");
        CallStopServer();
        PythonEngine.RemoveShutdownHandler(OnPythonShutdown);
    }

#if DEBUG

#if UNITY_EDITOR_OSX
    const string ProjectRoot = "/Volumes/shotgun_s_drive/imgspc";
#else
    const string ProjectRoot = "S:/imgspc";
#endif

    [MenuItem("Shotgun/Debug/Bootstrap Engine")]
    public static void CallBootstrapEngine()
    {
        CallBootstrap();
    }

    [MenuItem("Shotgun/Debug/Manually Start Engine")]
    public static void CallStartEngine()
    {
        // TODO (fix) : PythonException: TankError : Missing required script user in config '/Users/inwoods/Library/Caches/Shotgun/imaginaryspaces/p120c45.basic.desktop/cfg/config/core/shotgun.yml'
        string pyScript = @"
import sgtk
tk = sgtk.sgtk_from_path('{0}')
ctx = tk.context_empty()
engine = sgtk.platform.start_engine('tk-unity', tk, ctx)
        ";

        pyScript = string.Format(pyScript,ProjectRoot);

        PythonRunner.RunString(pyScript);
    }

    [MenuItem("Shotgun/Debug/Restart Engine")]
    public static void CallRestartEngine()
    {
        string pyScript = @"
import sgtk
sgtk.platform.restart()
        ";

        PythonRunner.RunString(pyScript);
    }

    [MenuItem("Shotgun/Debug/Print Engine Envs")]
    public static void CallPrintEnv()
    {
        string[] envs = { "SHOTGUN_UNITY_BOOTSTRAP_LOCATION","BOOTSTRAP_SG_ON_UNITY_STARTUP",};

        foreach(string env in envs)
        {
            UnityEngine.Debug.Log(env + ": " + System.Environment.GetEnvironmentVariable(env));
        }
    }
#endif

}
