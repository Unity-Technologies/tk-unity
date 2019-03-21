import os
import pprint
import sys
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class UnitySessionUploadVersionPlugin(HookBaseClass):
    """
    Plugin for sending .mp4 images to Shotgun for review.
    """

    # Public interface    
    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        publisher = self.parent

        shotgun_url = publisher.sgtk.shotgun_url

        media_page_url = "%s/page/media_center" % (shotgun_url,)
        review_url = "https://www.shotgunsoftware.com/features/#review"

        return """
        Upload the file to Shotgun for review.<br><br>

        A <b>Version</b> entry will be created in Shotgun and a transcoded
        copy of the file will be attached to it. The file can then be reviewed
        via the project's <a href='%s'>Media</a> page, <a href='%s'>RV</a>, or
        the <a href='%s'>Shotgun Review</a> mobile app.
        """ % (media_page_url, review_url, review_url)

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

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
        return {
            "File Extensions": {
                "type": "str",
                "default": "mp4",
                "description": "File Extensions of files to include"
            },
            "Upload": {
                "type": "bool",
                "default": True,
                "description": "Upload content to Shotgun?"
            },
            "Link Local File": {
                "type": "bool",
                "default": True,
                "description": "Should the local file be referenced by Shotgun"
            },
        }

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patterns such as *, for example
        ["unity.*", "unity.video"]
        """

        # we use "video" since that's the mimetype category.
        return ["unity.video"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """

        publisher = self.parent
        file_path = item.properties["path"]

        file_info = publisher.util.get_file_path_components(file_path)
        extension = file_info["extension"].lower()

        valid_extensions = []

        for ext in settings["File Extensions"].value.split(","):
            ext = ext.strip().lstrip(".")
            valid_extensions.append(ext)

        self.logger.debug("Valid extensions: %s" % valid_extensions)

        if extension in valid_extensions:
            # log the accepted file and display a button to reveal it in the fs
            self.logger.info(
                "Version upload plugin accepted: %s" % (file_path,),
                extra={
                    "action_show_folder": {
                        "path": file_path
                    }
                }
            )

            # return the accepted info
            return {"accepted": True}
        else:
            self.logger.debug(
                "%s is not in the valid extensions list for Version creation" %
                (extension,)
            )
            return {"accepted": False}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        In this implementation we validate that the video recording file (.mp4) exists.

        Returns a boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: True if item is valid, False otherwise.
        """
        full_file_name = item.properties['path']
        file_exists = os.path.isfile(full_file_name)
        if not file_exists:
            self.logger.error('Could not find file "{}"'.format(full_file_name))
            
        return file_exists

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        
        publisher = self.parent
        path = item.properties["path"]
        
        directory = os.path.dirname(path)
        
        task_name = item.context.task["name"] if item.context.task else None
        link_name = item.context.entity["name"] if item.context.entity else None
        
        new_file_name = None
        if task_name and link_name:
            new_file_name = "{0}-{1}.mp4".format(link_name, task_name)
        if link_name and not task_name:
            new_file_name = "{0}.mp4".format(link_name)
        
        if new_file_name:
            new_path = os.path.join(directory, new_file_name)
            from shutil import move
            move(path, new_path)
            path = new_path
        
        # allow the publish name to be supplied via the item properties. this is
        # useful for collectors that have access to templates and can determine
        # publish information about the item that doesn't require further, fuzzy
        # logic to be used here (the zero config way)
        publish_name = item.properties.get("publish_name")
        if not publish_name:

            self.logger.debug("Using path info hook to determine publish name.")

            # use the path's filename as the publish name
            path_components = publisher.util.get_file_path_components(path)
            publish_name = path_components["filename"]

        self.logger.debug("Publish name: %s" % (publish_name,))

        self.logger.info("Creating Version...")
        version_data = {
            "project": item.context.project,
            "code": publish_name,
            "description": item.description,
            "entity": self._get_version_entity(item),
            "sg_task": item.context.task
        }

        if "sg_publish_data" in item.properties:
            publish_data = item.properties["sg_publish_data"]
            version_data["published_files"] = [publish_data]

        if settings["Link Local File"].value:
            version_data["sg_path_to_movie"] = path

        # log the version data for debugging
        self.logger.debug(
            "Populated Version data...",
            extra={
                "action_show_more_info": {
                    "label": "Version Data",
                    "tooltip": "Show the complete Version data dictionary",
                    "text": "<pre>%s</pre>" % (pprint.pformat(version_data),)
                }
            }
        )

        # Create the version
        version = publisher.shotgun.create("Version", version_data)
        self.logger.info("Version created!")

        # stash the version info in the item just in case
        item.properties["sg_version_data"] = version

        thumb = item.get_thumbnail_as_path()

        if settings["Upload"].value:
            self.logger.info("Uploading content...")

            # on windows, ensure the path is utf-8 encoded to avoid issues with
            # the shotgun api
            if sys.platform.startswith("win"):
                upload_path = path.decode("utf-8")
            else:
                upload_path = path

            self.parent.shotgun.upload(
                "Version",
                version["id"],
                upload_path,
                "sg_uploaded_movie"
            )
        elif thumb:
            # only upload thumb if we are not uploading the content. with
            # uploaded content, the thumb is automatically extracted.
            self.logger.info("Uploading thumbnail...")
            self.parent.shotgun.upload_thumbnail(
                "Version",
                version["id"],
                thumb
            )

        self.logger.info("Upload complete!")

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        path = item.properties["path"]
        version = item.properties["sg_version_data"]

        self.logger.info(
            "Version uploaded for file: %s" % (path,),
            extra={
                "action_show_in_shotgun": {
                    "label": "Show Version",
                    "tooltip": "Reveal the version in Shotgun.",
                    "entity": version
                }
            }
        )
        
        # Delete the temporary .mp4
        full_file_name = item.properties['path']
        if os.path.isfile(full_file_name):
            try:
                os.remove(full_file_name)
            except Exception, e:
                import traceback
                self.logger.error('Exception while trying to delete temporary render file "{}":{}'.format(full_file_name,e))
                self.logger.error('Stack trace:\n\n{}'.format(traceback.format_exc()))

    # Private interface
    def _get_version_entity(self, item):
        """
        Returns the best entity to link the version to.
        """

        if item.context.entity:
            return item.context.entity
        elif item.context.project:
            return item.context.project
        else:
            return None