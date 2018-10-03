using System.Collections;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using System.IO;

[InitializeOnLoad]
class Bootstrap
{
    static Bootstrap()
    {
        UnityEngine.Debug.Log("Invoking Shotgun Toolkit bootstrap script.");
        PythonRunner.RunFile(System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION"));
    }
}
