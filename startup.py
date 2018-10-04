import os
import pprint
from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation


class UnityLauncher(SoftwareLauncher):
    """
    Handles launching Unity executables. Automatically starts up
    a tk-unity engine with the current context in the new session
    of Unity.
    """
    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2018.2.9f1"

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch Unity in that will automatically
        load Toolkit and the tk-unity engine when Unity starts.

        :param str exec_path: Path to Maya executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        # Add std context and site info to the env. This will add stuff like which site to
        # connect to, what context to load, etc.
        required_env.update(self.get_standard_plugin_environment())

        # This will be read by bootstrap.cs from the C# plugin in UI to know where to pick up the
        # Toolkit code.
        required_env["SHOTGUN_UNITY_BOOTSTRAP_LOCATION"] = os.path.join(
            self.disk_location,
            "plugins",
            "basic",
            "bootstrap.py"
        )

        # Signals which engine instance from the environment is going to be used.
        required_env["SHOTGUN_ENGINE"] = self.engine_name

        if file_to_open:
            # Add the file name to open to the launch environment
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        self.logger.debug("Launch environment: %s", pprint.pformat(required_env))
        self.logger.debug("Launch arguments: %s", args)

        args += '-importPackage "{0}/{1}/{2}"'.format(self.disk_location, "startup", "shotgunBootstrap.unitypackage")

        return LaunchInformation(exec_path, args, required_env)

    ##########################################################################################
    # private methods

    def scan_software(self):
        """
        Scan the filesystem for maya executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """
        self.logger.debug("Scanning for Unity executables...")

        # This piece of boiler-plate code scans for software based and for every version
        # returned checks if the engine actually supports it.
        #
        # You can look at other engines, which do pretty much the same thing.
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

    def _find_software(self):
        """
        Find executables in the default install locations.
        """
        # TODO:
        # I do not know how multiple builds of Unity live of the same computer. I suspect asking
        # the registry would be the most sensible way to do this on Windows.
        # On Linux/macOS, we generally scan on disk using templates to glob for files. It's hard to
        # give a proof of concept here because the build number is not in the install path.
        #
        # When people install software in the non-default install location, they generally configure
        # Software entities in Shotgun.
        #
        # So instead I'm just testing for file existence.
        builds = [
            "/Applications/Unity/Unity.app",
            "C:/Program Files/Unity/Editor/Unity.exe"
        ]

        for executable_path in builds:
            self.logger.debug("Searching for %s", executable_path)
            if os.path.exists(executable_path):
                self.logger.debug("Software was found!")
                yield SoftwareVersion(
                    # This would be retrieved from the registry or a file.
                    # /Applications/Unity/Unity.app/Contents/Info.plist on macOS actually has this information.
                    # So does HKEY_CURRENT_USER\Software\Unity Technologies\Installer\Unity\Version on Windows.
                    "2018.2.9f1",
                    "Unity",
                    executable_path,
                    os.path.join(self.disk_location, "icon_256.png")
                )
