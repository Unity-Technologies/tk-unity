from .sg_client import GetUnityEditor

# This script module is executed by Unity to bootstrap Shotgun
def plugin_startup():
    import os
    import sys
    """
    Initializes the Toolkit plugin for Unity.
    Returns  0 on success 
    Returns -1 on failure
    """
    try:
        # Ensure that we can find PySide on MacOS
        # TODO: move this to part of the Python installation steps.
        # Notes from discussions with the SG team:
        #   In the past, we have taken one of two different approaches:
        #
        #   We raise an intelligible error that makes it clear that PySide 
        #   needs to be made available (PYTHONPATH being the easiest route 
        #   to setup) if it can't be imported.
        #
        #   We include a build of Qt and PySide in a framework that accompanies 
        #   the engine. This is what we do for our old Softimage integration, as 
        #   an example. You can find that here 
        #   (https://github.com/shotgunsoftware/tk-framework-softimageqt)
        
        # Start by creating the QApplication object
        from sgtk.util.qt_importer import QtImporter
        qt = QtImporter()
        if not qt.QtGui.QApplication.instance():
            # Tell QApplication that we're running as a plugin and not to muck with Native menus
            if "darwin" == sys.platform:
                qt.QtGui.QApplication.setAttribute(qt.QtCore.Qt.AA_DontUseNativeMenuBar,False);
                qt.QtGui.QApplication.setAttribute(qt.QtCore.Qt.AA_MacPluginApplication,True);
    
            qApp = qt.QtGui.QApplication(["Shotgun Engine for Unity"])
        
        if "darwin" in sys.platform:
            site_packages_path = '/Applications/Shotgun.app/Contents/Resources/Python/lib/python2.7/site-packages'
            if site_packages_path not in sys.path:
                sys.path.append(site_packages_path)

        # the plugin python path will be just below the root level. 
        # add it to sys.path
        plugin_root_path = os.path.dirname(os.environ["SHOTGUN_UNITY_BOOTSTRAP_LOCATION"])

        if plugin_root_path not in sys.path:
            sys.path.insert(0, plugin_root_path)

        # Make sure there is no running engine before bootstrapping
        import sgtk
        engine = sgtk.platform.current_engine()
        if engine:
            engine.destroy()

        # now that the path is there, we can import the plugin bootstrap logic
        from . import tk_unity_basic
        tk_unity_basic.plugin_bootstrap(plugin_root_path)

        import sgtk
        sgtk.platform.current_engine()._initialize_dark_look_and_feel()

        # Engine is fully initialized. Let Unity know
        GetUnityEditor().Integrations.Shotgun.Bootstrap.OnEngineInitialized()

    except:
        import traceback
        
        # Only log in the client as we might have gotten a "connection reset" 
        # exception
        from . import sg_client
        sg_client.log('Shotgun Toolkit Error:')
        sg_client.log('Exception stack trace:\n\n{}'.format(traceback.format_exc()))
        
        # Clean-up the engine
        import sgtk
        engine = sgtk.platform.current_engine()
        if engine:
            engine.destroy()

        # Failure to bootstrap
        return -1

    # Success
    return 0