using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using System.IO;

public class Bootstrap
{
    public static void CallBootstrap()
    {
        UnityEngine.Debug.Log("Invoking Shotgun Toolkit bootstrap script.");
        PythonRunner.RunFile(System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION"));
    }

    [UnityEditor.Callbacks.DidReloadScripts]
    public static void OnReload()
    {
        // check environment variable to see if we want to bootstrap
        var bootstrap = System.Environment.GetEnvironmentVariable("BOOTSTRAP_SG_ON_UNITY_STARTUP");
        if (bootstrap == null)
        {
            return;
        }
        CallBootstrap();
    }
}
