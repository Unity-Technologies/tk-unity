using UnityEditor;
using UnityEngine;
using Python.Runtime;
using System.Reflection;
using System.IO;

class RPyC
{
    [MenuItem("Python/Start RPyC server")]
    public static void CallStartServer()
    {
        UnityEngine.Debug.Log("Starting rpyc server...");
        string pythonFilePath = Directory.GetParent(Application.dataPath).ToString() + "/PythonScripts/startServer.py";
        PythonRunner.RunFile(pythonFilePath);
        UnityEngine.Debug.Log("rpyc server started");
    }
    [MenuItem("Python/Stop RPyC server")]
    public static void CallStopServer()
    {
        UnityEngine.Debug.Log("Stopping rpyc server...");
        string pythonFilePath = Directory.GetParent(Application.dataPath).ToString() + "/PythonScripts/stopServer.py";
        PythonRunner.RunFile(pythonFilePath);
        UnityEngine.Debug.Log("rpyc server stopped");
    }

    [MenuItem("Python/Process Qt Events Once")]
    public static void CallProcessingQtEventsOnce()
    {
        UnityEngine.Debug.Log("Processing Qt Events...");
        string pythonFilePath = Directory.GetParent(Application.dataPath).ToString() + "/PythonScripts/processQtEventsOnce.py";
        PythonRunner.RunFile(pythonFilePath);
    }

    [MenuItem("Python/Start Processing Qt Events")]
    public static void CallStartProcessingQtEvents()
    {
        UnityEngine.Debug.Log("Starting Qt event processing...");
        string pythonFilePath = Directory.GetParent(Application.dataPath).ToString() + "/PythonScripts/startProcessingQtEvents.py";
        PythonRunner.RunFile(pythonFilePath);
    }
    [MenuItem("Python/Stop Processing Qt Events")]
    public static void CallStopProcessingQtEvents()
    {
        UnityEngine.Debug.Log("Stopping Qt event processing...");
        string pythonFilePath = Directory.GetParent(Application.dataPath).ToString() + "/PythonScripts/stopProcessingQtEvents.py";
        PythonRunner.RunFile(pythonFilePath);
    }
}