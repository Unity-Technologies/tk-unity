# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import glob
import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class UnitySessionCollector(HookBaseClass):
    """
    Collector that operates on the Unity session. Should inherit from the basic
    collector hook.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """

        # grab any base class settings
        collector_settings = super(UnitySessionCollector, self).settings or {}

        return collector_settings

    def _collect_file(self, parent_item, path):
        """
        Process the supplied file path.

        :param parent_item: parent item instance
        :param path: Path to analyze
        :param frame_sequence: Treat the path as a part of a sequence
        :returns: The item that was created
        """

        # make sure the path is normalized. no trailing separator, separators
        # are appropriate for the current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(path)

        publisher = self.parent

        # get info for the extension
        item_info = self._get_item_info(path)
        item_type = item_info["item_type"]
        type_display = item_info["type_display"]
        evaluated_path = path
        is_sequence = False

        display_name = publisher.util.get_publish_name(
            path, sequence=is_sequence)

        # create and populate the item
        file_item = parent_item.create_item(
            "unity.video", type_display, "Session Recording")
        file_item.set_icon_from_path(item_info["icon_path"])

        # all we know about the file is its path. set the path in its
        # properties for the plugins to use for processing.
        file_item.properties["path"] = evaluated_path

        self.logger.info("Collected file: %s" % (evaluated_path,))

        return file_item    
        
    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Maya and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """
        
        import UnityEngine
        session_item = parent_item.create_item(
            "unity.session",
            "Unity Session",
            UnityEngine.Application.productName
        )
        session_item.properties["project_root"] = UnityEngine.Application.dataPath
        import tempfile
        item = self._collect_file(
                session_item,
                os.path.join(tempfile.gettempdir(), UnityEngine.Application.productName + ".mp4")
            )
