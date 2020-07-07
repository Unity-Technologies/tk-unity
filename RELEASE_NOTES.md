RELEASE NOTES

**Version**: 1.0
This versions requires:
* Shotgun for Unity 1.0

NEW FEATURES
* Porting tk-unity to Python 3
* Python 2 is no longer supported

**Version**: 0.10

This version requires:
* Shotgun for Unity 0.10 (com.unity.integrations.shotgun)

**Version**: 0.9

This version requires:
* Python for Unity 2.0.0
* Shotgun for Unity 0.9.0

**Version**: 0.8

NEW FEATURES
* Toolkit app dialogs are now shown "always on top"
* Addition of an engine `post_init_hook`, called when Unity is done initializing 
toolkit
* More flexible ModelImporter.userData (now using a JSON dictionary)
* Renamed Shotgun menu item "Record Timeline..." to "Publish Recording..."
* Removed Shotgun menu item "Publish..."
* Credentials are now asked using the standard UI Shotgun login dialogs
* Added discovery paths for Unity on CentOS

FIXES
- Fixed an edge case where the engine would not initialize on domain reload

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


