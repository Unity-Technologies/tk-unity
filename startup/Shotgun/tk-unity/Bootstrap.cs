//#define DEBUG
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

        pyScript = string.Format(pyScript, ProjectRoot);

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
        string[] envs = { "SHOTGUN_UNITY_BOOTSTRAP_LOCATION", "BOOTSTRAP_SG_ON_UNITY_STARTUP", };

        foreach (string env in envs)
        {
            UnityEngine.Debug.Log(env + ": " + System.Environment.GetEnvironmentVariable(env));
        }
    }
#endif

}
