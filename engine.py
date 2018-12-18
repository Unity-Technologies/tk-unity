"""
A Unity Editor engine for Sgtk.
"""

# Note that the VFX Plaform states that in 2019 all DCCs need to support Python 3,
# since Python 2.7 will be EOL in 2020. So it's a good idea to start writing your
# engine with a Python 3 compatible syntax. Note that at the moment Toolkit
# is not Python 3 compatible.

import pprint
from sgtk.platform import Engine

import unity_connection

###############################################################################################
# The Shotgun Unity engine


class UnityEditorEngine(Engine):
    """
    Toolkit engine for Unity.

    Note that when the engine starts up a log file is created at

    Windows: %APPDATA%/Shotgun/logs/tk-Unity.log
    macOS: ~/Library/Logs/Shotgun/tk-Unity.log
    Linux: ~/.shotgun/logs/tk-Unity.log

    and that all logging calls to Toolkit logging methods will be forwarded there.
    It all uses the Python's logger under the hood.
    """

    @property
    def context_change_allowed(self):
        """
        Whether the engine allows a context change without the need for a restart.
        """
        return False

    @property
    def host_info(self):
        """
        :returns: A dictionary with information about the application hosting this engine.

        The returned dictionary is of the following form on success:

            {
                "name": "Unity",
                "version": "4.9",
            }

        The returned dictionary is of following form on an error preventing
        the version identification.

            {
                "name": "Unity",
                "version: "unknown"
            }
        """
        host_info = {"name": "Unity", "version": "unknown"}
        return host_info

    ##########################################################################################
    # init and destroy

    def init_engine(self):
        """
        Initializes the engine.
        """
        self.logger.debug("%s: Initializing...", self)

    def post_app_init(self):
        """
        Called when all apps have initialized
        """

        # Create the Shotgun menu based on the actions available as well as any dockable views in the UI.
        #
        # Traditionally, the menu is built the following way:
        #
        # - First create the Context menu, which is a folder that has a bunch of actions
        #   in it like showing the About box and adding actions to reload Toolkit.
        # - Then there's a separator and a list of favorites.
        # - Finally, there's a separator and a list of folders for each Toolkit application that
        #   has more than one command. If an app has a single command, then there is single entry
        #   instead of a folder.
        #
        # Building the menu is done by performing three passes on the list of commands:
        #
        # - The first pass takes every context actions, removes them from the list and adds them to the
        #   Context menu.
        # - Add a separator.
        # - The second pass takes every favorites and, removes them from the list of commands
        #   and lists them in the Shotgun menu.
        # - Add a separator.
        # - Sort the remaining actions into sub-menus, one per application. If an application
        #   has a single action, then you have a single item instead of a sub-menu.        
        #
        # Not all commands are part of an app. For example, the Restart Engine and
        # Toggle Debug commands.
        #
        # The first entry of the Shotgun menu is a sub-menu named after
        # the current context (calling str on self.context will generate a human readable string),
        # and contains all commands that don't have an app or whose properties
        # key have the type set to context_menu.
        #
        # Then each app has its folder with all its commands inserted inside it, unless
        # there is a single command for that app. In that case the menu
        # entry will be placed at the root level of the menu.
        #

        self.logger.info("Here are the available Toolkit commands:")
        
        # store the menu cmds so that we can access them later from C#
        self._menu_cmd_items = {}
        for (cmd_name, cmd_details) in self.commands.items():
            # Prints out the name of the Toolkit commands that can be invoked
            # and the method to invoke to launch them. The callbacks
            # do not take any parameters.
            # This prints the application's name, the command name and the callback method.

            self.logger.debug("-" * len(cmd_name))
            self.logger.debug("Command name: " + cmd_name)
            self.logger.debug("Command properties:")
            self.logger.debug(pprint.pformat(cmd_details["properties"]))
            
            self._menu_cmd_items[cmd_name] = cmd_details
        
        # Check for favorites
        for fav in self.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]

            if menu_name not in self.commands:
                self.logger.warning("Unknown command: %s/%s", app_instance_name, menu_name)
                continue

            command = self.commands[menu_name]

            if command["properties"]["app"].instance_name != app_instance_name:
                # The same action can be registered for different app instance
                # so skip it.
                continue

            self.logger.debug("Favorite found: ", menu_name)
            self._menu_cmd_items[menu_name]["properties"]["type"] = "favorite"
        
        from tk_create_menus.generateMenuItems import MenuItemGenerator
        context_name = str(self.context).decode("utf-8")
        
        UnityEngine = unity_connection.get_unity_connection().getmodule('UnityEngine')
        generator = MenuItemGenerator(UnityEngine.Application.dataPath + "/Shotgun", self._menu_cmd_items, context_name, "call_menu_item_callback")
        generator.GenerateMenuItems()

        UnityEditor = unity_connection.get_unity_connection().getmodule('UnityEditor')
        UnityEditor.AssetDatabase.Refresh()

    # call this function to then call the callbacks, so we can debug
    def call_menu_item_callback(self, name):
        if not self._menu_cmd_items or (not name in self._menu_cmd_items):
            self.logger.error("Missing menu command {0}".format(name))
            return
        self._menu_cmd_items[name]["callback"]()

    @property
    def has_ui(self):
        """
        Detect and return if Unity is running in batch mode
        """
        return True

    ##########################################################################################
    # logging

    def _emit_log_message(self, handler, record):
        """
        Called by the engine to log messages in Unity script editor.
        All log messages from the toolkit logging namespace will be passed to this method.

        :param handler: Log handler that this message was dispatched from.
                        Its default format is "[levelname basename] message".
        :type handler: :class:`~python.logging.LogHandler`
        :param record: Standard python logging record.
        :type record: :class:`~python.logging.LogRecord`
        """
        msg = handler.format(record)
        
        import logging
        UnityEngine = unity_connection.get_unity_connection().getmodule('UnityEngine')
        
        if record.levelno >= logging.ERROR:
            UnityEngine.Debug.LogError(msg)
        elif record.levelno >= logging.WARNING:
            UnityEngine.Debug.LogWarning(msg)
        else:
            UnityEngine.Debug.Log(msg)

    ##########################################################################################
    # panel support

    def show_panel(self, panel_id, title, bundle, widget_class, *args, **kwargs):
        """
        Docks an app widget in a panel.

        :param panel_id: Unique identifier for the panel, as obtained by register_panel().
        :param title: The title of the panel
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: the created widget_class instance
        """
        self.log_warning("Panel functionality not implemented. Falling back to showing "
                         "panel '%s' in a modeless dialog" % panel_id)
        dialog = self.show_dialog(title, bundle, widget_class, *args, **kwargs)
        
        # TODO: make a custom hook for this so the shotgun panel code is not linked to the engine
        if panel_id == "tk_multi_shotgunpanel_main":
            
            # get the Unity selection
            UnityEditor = unity_connection.get_unity_connection().getmodule('UnityEditor')
            mainAsset = UnityEditor.Selection.activeObject
            if not mainAsset:
                return dialog
            
            # make sure to get the main asset in order to get the path
            if not UnityEditor.AssetDatabase.IsMainAsset(mainAsset):
                mainAsset = UnityEditor.EditorUtility.GetPrefabParent(mainAsset)
                
            assetPath = UnityEditor.AssetDatabase.GetAssetPath(mainAsset)
            if not assetPath:
                return dialog
            
            # get user data from model importer
            modelImporter = UnityEditor.AssetImporter.GetAtPath(assetPath)
            if not modelImporter:
                return dialog
                
            shotgunPath = modelImporter.userData
            if not shotgunPath: 
                return dialog
            
            # get publish entity from asset if possible
            import tank
            sg_data = tank.util.find_publish(bundle.tank, [shotgunPath], fields=["entity"])
            if not sg_data:
                return dialog
                
            entity = sg_data[shotgunPath].get("entity", None)
            if not entity:
                return dialog
            
            dialog.navigate_to_entity(entity["type"], entity["id"])
            return dialog
        
        return dialog
