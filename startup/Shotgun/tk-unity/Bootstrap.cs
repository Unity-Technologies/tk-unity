using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using System.IO;

class Bootstrap
{
    [UnityEditor.Callbacks.DidReloadScripts]
    public static void OnReload()
    {
        UnityEngine.Debug.Log("Invoking Shotgun Toolkit bootstrap script.");
        PythonRunner.RunFile(System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION"));
    }
}
