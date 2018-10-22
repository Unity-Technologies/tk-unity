import os
import sys
import pprint

def plugin_startup():
    """
    Initializes the Toolkit plugin for Unity.
    """
    # Make sure we can import from our own location
    bootstrap_location = 'D:/projects/tk-unity/plugins/basic'
    if bootstrap_location not in sys.path:
        sys.path.append(bootstrap_location)
        
    import unity_connection

    #############dltrace#################
    print('Retrieving UnityEngine')
    #############dltrace#################
    UnityEngine = unity_connection.get_unity_connection().getmodule('UnityEngine')
    try:
        # Ensure that we can find PySide on MacOS
        # TODO: move this to part of the python installation steps.
        if "darwin" in sys.platform:
            try:
                sys.path.index('/Applications/Shotgun.app/Contents/Resources/Python/lib/python2.7/site-packages')
            except ValueError:
                sys.path.append('/Applications/Shotgun.app/Contents/Resources/Python/lib/python2.7/site-packages')

        # the plugin python path will be just below the root level. 
        # add it to sys.path
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
            from sgtk.util.qt_importer import QtImporter
            importer = QtImporter()

            # Tell QApplication that we're running as a plugin and not to muck with Native menus
            if "darwin" == sys.platform:
                importer.QtGui.QApplication.setAttribute(importer.QtCore.Qt.AA_DontUseNativeMenuBar,False);
                importer.QtGui.QApplication.setAttribute(importer.QtCore.Qt.AA_MacPluginApplication,True);

            qApp = importer.QtGui.QApplication(["Shotgun Engine for Unity"])

        import sgtk
        sgtk.platform.current_engine()._initialize_dark_look_and_feel()

    except Exception, e:
        import traceback
        stack_trace = traceback.format_exc()

        message = "Shotgun Toolkit Error: %s" % (e,)
        details = "Error stack trace:\n\n%s" % (stack_trace)

#        UnityEngine.Debug.LogError(message)
#        UnityEngine.Debug.LogError(details)

        print(message)
        print(details)

plugin_startup()
