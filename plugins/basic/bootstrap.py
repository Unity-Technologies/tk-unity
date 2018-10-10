import os
import sys
import clr


# Here is the content of my bootstrap.cs inside my Unity project.
# using System.Collections;
# using System.Collections.Generic;
# using UnityEditor;
# using UnityEngine;
# using Python.Runtime;
# using System.IO;
# class Bootstrap{
#     static void Startup()
#     {
#         UnityEngine.Debug.Log("Invoking Shotgun Toolkit bootstrap script.");
#         PythonRunner.RunFile(System.Environment.GetEnvironmentVariable("SHOTGUN_UNITY_BOOTSTRAP_LOCATION"));
#     }
#     [MenuItem("Shotgun/Restart engine...")]
#     public static void CallRestartEngine()
#     {
#         PythonRunner.RunString("import sgtk; sgtk.platform.restart()");
#     }
# }

def plugin_startup():
    """
    Initializes the Toolkit plugin for Unity.
    """
    clr.AddReference("UnityEngine")
    import UnityEngine
    try:
        # the plugin python path will be just below the root level. add it to
        # sys.path
        plugin_root_path = os.path.dirname(os.environ["SHOTGUN_UNITY_BOOTSTRAP_LOCATION"])

        if plugin_root_path not in sys.path:
            sys.path.insert(0, plugin_root_path)
            
        # now that the path is there, we can import the plugin bootstrap logic
        import tk_unity_basic
        tk_unity_basic.plugin_bootstrap(plugin_root_path)

        # make sure there is a QApplication. We need to wait after the call to 
        # plugin_bootstrap in order for sgtk.platform.qt to be properly 
        # populated
        from sgtk.platform.qt import QtGui
        if not QtGui.QApplication.instance():
            QtGui.QApplication(sys.argv)

        import sgtk
        sgtk.platform.current_engine()._initialize_dark_look_and_feel()

    except Exception, e:
        import traceback
        stack_trace = traceback.format_exc()

        message = "Shotgun Toolkit Error: %s" % (e,)
        details = "Error stack trace:\n\n%s" % (stack_trace)

        UnityEngine.Debug.LogError(message)
        UnityEngine.Debug.LogError(details)


# Invoked on startup while Nuke is walking NUKE_PATH.
plugin_startup()
