# This script module is executed by Unity to bootstrap Shotgun
def plugin_startup():
    import os
    import sys
    """
    Initializes the Toolkit plugin for Unity.
    Returns  0 on success 
    Returns -1 on failure
    """
    import unity_connection
    UnityEngine = unity_connection.get_module('UnityEngine')
    try:
        # Ensure that we can find PySide on MacOS
        # TODO: move this to part of the Python installation steps.
        if "darwin" in sys.platform:
            site_packages_path = '/Applications/Shotgun.app/Contents/Resources/Python/lib/python2.7/site-packages'
            if site_packages_path not in sys.path:
                sys.path.append(site_packages_path)

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
        UnityEngine.Debug.LogError('Shotgun Toolkit Error: {}'.format(e))
        UnityEngine.Debug.LogError('Error stack trace:\n\n{}'.format(traceback.format_exc()))
        
        # Failure to bootstrap
        return -1

    # Success
    return 0