import os
import sys
import clr


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
    except Exception, e:
        import traceback
        stack_trace = traceback.format_exc()

        message = "Shotgun Toolkit Error: %s" % (e,)
        details = "Error stack trace:\n\n%s" % (stack_trace)

        UnityEngine.Debug.LogError(message)
        UnityEngine.Debug.LogError(details)


# Invoked on startup while Nuke is walking NUKE_PATH.
plugin_startup()
