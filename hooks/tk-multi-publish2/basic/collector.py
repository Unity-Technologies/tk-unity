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

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Maya and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """
        
        import UnityEngine
        import UnityEditor
        session_item = parent_item.create_item(
            "unity.scene",
            "Unity Scene",
            UnityEngine.SceneManagement.SceneManager.GetActiveScene().name
        )
        session_item.properties["project_root"] = UnityEngine.Application.dataPath
        
        # find all timelines in the scene and create items for them
        playable_directors = UnityEngine.Object.FindObjectsOfType[UnityEngine.Playables.PlayableDirector]()
        for pd in playable_directors:
            timeline_path = UnityEditor.AssetDatabase.GetAssetPath(pd.playableAsset)
            timeline_item = session_item.create_item(
                "unity.timeline",
                "Timeline Asset",
                pd.playableAsset.name
            )
            timeline_item.properties["path"] = timeline_path
            timeline_item.properties["asset"] = pd.playableAsset
            timeline_item.properties["gameobject"] = pd.gameObject
