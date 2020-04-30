import json
import os
import sys
import pprint
import getpass
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation

class UnityLauncher(SoftwareLauncher):
    """
    Handles launching Unity executables. Automatically starts up
    a tk-unity engine with the current context in the new session
    of Unity.
    """
    
    # Named regex strings to insert into the executable template paths when
    # matching against supplied versions and products. Similar to the glob
    # strings, these allow us to alter the regex matching for any of the
    # variable components of the path in one place
    COMPONENT_REGEX_LOOKUP = {
        "version": "[\d]+[\d.\[a-z\]]+",
        "username" : getpass.getuser()
    }

    # This dictionary defines a list of executable template strings for each
    # of the supported operating systems. The templates are used for both
    # globbing and regex matches by replacing the named format placeholders
    # with an appropriate glob or regex string.
    EXECUTABLE_TEMPLATES = {
        "darwin": [
            "/Applications/Unity/Unity.app/Contents/MacOS/Unity",
            "/Applications/Unity/Hub/Editor/{version}/Unity.app/Contents/MacOS/Unity",
            "/Applications/{version}/Unity.app/Contents/MacOS/Unity",
        ],
        "win32": [
            "C:/Program Files/Unity/Editor/Unity.exe",
            "C:/Program Files/Unity{version}/Editor/Unity.exe",
            "C:/Program Files/Unity {version}/Editor/Unity.exe",
            "C:/Program Files/Unity/{version}/Editor/Unity.exe",
            "C:/Program Files/Unity/Hub/Editor/{version}/Editor/Unity.exe",            
            "D:/Program Files/{version}/Editor/Unity.exe",
            "D:/Program Files/Unity {version}/Editor/Unity.exe",
            "D:/Program Files/Unity{version}/Editor/Unity.exe",
            "D:/Program Files/Unity/{version}/Editor/Unity.exe",
            "D:/Unity Editors/{version}/Editor/Unity.exe"
        ],
        "linux2": [
            "/opt/Unity/Hub/Editor/Unity-{version}/Editor/Unity",
            "/opt/Unity/{version}/Editor/Unity",
            "/mnt/opt/Unity/{version}/Editor/Unity",
            "/mnt/opt/Unity/Hub/Editor/Unity-{version}/Editor/Unity",
            "/home/{username}/Unity/{version}/Editor/Unity",
            "/home/{username}/Unity/Hub/Editor/{version}/Editor/Unity"
        ]
    }
    
    HUB_EXECUTABLES = {
        "darwin": [
            # TODO
        ],
        "win32": [
            "C:/Users/{username}/AppData/Roaming/UnityHub/editors.json"
        ],
        "linux2": [
            # TODO
        ]
    }

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2018.2"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Unity in that will automatically
        load Toolkit and the tk-unity engine when Unity starts.

        :param str exec_path: Path to Unity executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        # Add std context and site info to the env. This will add stuff like which site to
        # connect to, what context to load, etc.
        required_env.update(self.get_standard_plugin_environment())

        # This will be read by Bootstrap.cs (com.unity.integrations.shotgun) 
        # from the C# plugin in UI to know where to pick up the
        # Toolkit code.
        required_env["SHOTGUN_UNITY_BOOTSTRAP_LOCATION"] = os.path.join(
            self.disk_location,
            "plugins",
            "basic",
            "bootstrap.py"
        )

        # Signals which engine instance from the environment is going to be used.
        required_env["SHOTGUN_ENGINE"] = self.engine_name

        # We do not support the file_to_open logic. Its value comes from the 
        # launch plug-in when users launch DCCs from a published file.
        # https://github.com/shotgunsoftware/tk-shotgun-launchpublish
        # https://github.com/shotgunsoftware/tk-config-default2/blob/master/env/publishedfile.yml#L27
        # https://github.com/shotgunsoftware/tk-config-default2/blob/master/env/includes/settings/tk-shotgun-launchpublish.yml


        self.logger.debug("Launch environment: %s", pprint.pformat(required_env))
        self.logger.debug("Launch arguments: %s", args)

        return LaunchInformation(exec_path, args, required_env)

    def scan_software(self):
        """
        Scan the file system for Unity executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for Unity executables...")

        # This piece of boiler-plate code scans for software based on the supported versions, and for every version
        # returned checks if the engine actually supports it.
        supported_sw_versions = []
        for sw_version in self._find_software():
            (supported, reason) = self._is_supported(sw_version)
            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" %
                    (sw_version, reason)
                )

        return supported_sw_versions

    ##########################################################################################
    # private methods

    def _find_software(self):
        """
        Find executables in the default install locations.
        
        Three different ways to find versions:
            1. If Unity Hub is installed, get versions from editors.json file
            2. Use default install location templates to glob for executable filesystem
            3. Try to get paths from UNITY_EDITOR_PATH environment variable if set
        """
        
        # all the discovered executables
        sw_versions = []
        
        # If Unity Hub is installed then try to get some of the versions from there
        editor_jsons = self.HUB_EXECUTABLES.get(sys.platform, [])
        username = getpass.getuser()
        for editor_json in [j.format(username=username) for j in editor_jsons]:
            if os.path.exists(editor_json):
                with open(editor_json, "r") as f:
                    data = json.load(f)
                    if not data:
                        continue
                    
                    for vals in list(data.values()):
                        version = vals["version"]
                        exec_paths = vals["location"] # list of locations
                        if len(exec_paths) < 1:
                            continue
                        exec_path = exec_paths[0]
                        
                        sw_versions.append(
                            SoftwareVersion(
                                version,
                                "Unity",
                                exec_path,
                                os.path.join(self.disk_location, "icon_256.png")
                            )
                        )
        
        # all the executable templates for the current OS
        executable_templates = self.EXECUTABLE_TEMPLATES.get(sys.platform, [])

        for executable_template in executable_templates:

            self.logger.debug("Processing template %s.", executable_template)

            executable_matches = self._glob_and_match(
                executable_template,
                self.COMPONENT_REGEX_LOOKUP
            )

            # Extract all products from that executable.
            for (executable_path, key_dict) in executable_matches:

                # extract the matched keys form the key_dict (default to None if
                # not included)
                executable_version = key_dict.get("version", "Unknown")
               
                self.logger.debug("Software was found: " + executable_path + ", " + executable_version)

                sw_versions.append(
                    SoftwareVersion(
                        executable_version,
                        "Unity",
                        executable_path,
                        os.path.join(self.disk_location, "icon_256.png")
                    )
                )
                
        # also try to get from environment variable
        environ_paths = os.environ.get("UNITY_EDITOR_PATH")
        if not environ_paths:
            return sw_versions
        
        environ_paths = environ_paths.split(";")
        for executable_path in environ_paths:
            sw_versions.append(
                    SoftwareVersion(
                        "Unknown",
                        "Unity",
                        executable_path,
                        os.path.join(self.disk_location, "icon_256.png")
                    )
                )
                
        return sw_versions