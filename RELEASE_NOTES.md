RELEASE NOTES

**Version**: 0.7

NEW FEATURES
* A progress bar is displayed in Unity on engine bootstrap
* Better logs when starting Unity outside of Shotgun Desktop

FIXES
* Engine bootstrap now survives Unity domain reloads

**Version**: 0.6

NEW FEATURES
* Now using the Package Manager Recorder package instead of the asset store one

**Version**: 0.5

NEW FEATURES
* The Shotgun integration is not installed as a unitypackage anymore, but as a Package Manager package

**Version**: 0.4

FIXES
* Shotgun now initializes on startup
* The Shotgun menu is now refreshed after Shotgun initializes
* Fixed a problem when importing UnityEditor/UnityEngine from engine.py after domain reload

**Version**: 0.3

NEW FEATURES
* Now using the Unity.Scripting.Python rpyc architecture so Shotgun runs in a separate process and survives domain unload
  
FIXES  
* Shotgun now survives Unity's domain reload after reconnecting to a new server
* Fixed scenarios where user data was not saved properly on loaded assets
  
**Version**: 0.2

NEW FEATURES
* The Shotgun Panel will now focus on selected objects

FIXES

* Fixed problem launching apps that are under submenus

**Version**: 0.1

NEW FEATURES

* Initial support for Shotgun toolkit apps
* Loader: import fbx files into Unity project
* Publish: publish playblasts recorded using the recorder
* Breakdown: view and update assets in the project


