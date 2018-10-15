using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using System.IO;

[InitializeOnLoad]
public class Bootstrap
{
    static bool SGIsInitialized = false;
    static Bootstrap()
    {
        // static ctor, install a delegate for EditorApplication.
        // hierarchyChanged, which is the most reliable callback
        // we found which is called on startup
        // Ref: https://answers.unity.com/questions/283191/how-do-i-detect-if-a-scene-is-being-loaded-during.html
        EditorApplication.hierarchyChanged += OnReload;
    }

    public static void CallBootstrap()
    {
        if (SGIsInitialized == false)
        {
            UnityEngine.Debug.Log("Invoking Shotgun Toolkit bootstrap script.");
            PythonRunner.RunFile(System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION"));

            SGIsInitialized = true;
        }
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
