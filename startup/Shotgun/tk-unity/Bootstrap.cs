//#define DEBUG
using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using System.IO;
using Python.Runtime;

public class Bootstrap
{
    const string ClientInitModuleFileName = "sg_client_init.py";
    
    /// <summary>
    /// Starts the Unity server, then bootstraps Shotgun on the Unity client
    /// </summary>
    public static void CallBootstrap()
    {
        // Use the engine's rpyc client script
        string bootstrapScript = System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION");
        bootstrapScript = bootstrapScript.Replace(@"\","/");

        string clientInitModulePath = Path.GetDirectoryName(bootstrapScript);
        clientInitModulePath = Path.Combine(clientInitModulePath,ClientInitModuleFileName);

        // First start the rpyc server
        PythonRunner.StartServer(clientInitModulePath);

        // Then bootstrap Shotgun on the client
        PythonRunner.CallServiceOnClient("bootstrap_shotgun", "'" + bootstrapScript + "'");
    }

    /// <summary>
    /// Bootstraps Shotgun when the domain is reloaded
    /// </summary>
    [UnityEditor.Callbacks.DidReloadScripts]
    public static void OnReload()
    {
        CallBootstrap();
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
