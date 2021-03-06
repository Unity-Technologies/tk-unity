import os
from collections import defaultdict

class MenuItemGenerator(object):
    """
    The MenuItemGenerator takes a list of command names and callbacks to create a C# script that will populate a
    Unity menu with the commands. Selecting a command in the Unity menu will then call the appropriate callback in Python.
    """

    def __init__(
        self, projectPath, cmdItems, contextName, callbackName, settings
    ):
        self._cSharpClass = "ShotgunMenuItems"
        self._cmdItems = cmdItems
        self._callbackName = callbackName
        self._projectPath = projectPath
        self._contextName = contextName # name for context menu item folder
        self._contextMenuFormat = self._contextName + "/{0}"
        self._settings = settings

        # The difference in priorities will add separators between the three menu sections
        # as a priority increase of 10 or more creates a separator.
        # Note: default dict will use 22 as the default value if the key doesn't match any of the other keys
        self._priorities = defaultdict(lambda:22, context_menu=0, favorite=11)
        
        self._functionList = []
        self._functionTemplate ="""        [MenuItem("Shotgun/{menuName}", false, {priority})] 
        public static void MenuItem{count}()
        {{
            Service.Call("execute_menu_item", "{submenuName}");
        }}"""

        self._fileContentsTemplate = """
namespace UnityEditor.Integrations.Shotgun
{{
    class {className}
    {{
        {functions}
    }}
}}
        """
        
        self._assemblyTemplate = """
{{
    "name": "{className}",
    "references": [
        "Unity.Integrations.Shotgun",
        "Unity.Scripting.Python.Editor"
    ],
    "optionalUnityReferences": [],
    "includePlatforms": [],
    "excludePlatforms": [],
    "allowUnsafeCode": false,
    "overrideReferences": false,
    "precompiledReferences": [],
    "autoReferenced": true,
    "defineConstraints": []
}}
"""
        
    def CreateCSharpFile(self):
        functionStr = "\n\n".join(self._functionList)
        fileContents = self._fileContentsTemplate.format(className = self._cSharpClass, functions = functionStr)
        
        # make sure directory already exists
        if not os.path.isdir(self._projectPath):
            os.makedirs(self._projectPath)
        
        cSharpFile = None
        assembly = None
        try:
            cSharpFile = open(os.path.join(self._projectPath, "{0}.cs".format(self._cSharpClass)), "w+")
            cSharpFile.write(fileContents)
            
            # also create assembly to access the Bootstrap code
            assembly = open(os.path.join(self._projectPath, "{0}.asmdef".format(self._cSharpClass)), "w+")
            assembly.write(self._assemblyTemplate.format(className = self._cSharpClass))
        finally:
            if cSharpFile:
                cSharpFile.close()
            if assembly:
                assembly.close()
    
    def GenerateMenuItem(self, cmdName, cmdType):
        count = len(self._functionList) + 1
        
        menuName = cmdName
        
        # Same as menuName but without the context (the name as known by toolkit)
        submenuName = menuName
        if cmdType == "context_menu":
            menuName = self._contextMenuFormat.format(cmdName)

        if cmdName == 'Publish...':
            # Should we hide the Publish menu? With the default config, we do
            # not want the "Publish..." menu item in Unity. Users should use
            # the "Publish Recording..." menu item instead
            if self._settings.get('hide_publish_menu', True):
                return

        self._functionList.append(
            self._functionTemplate.format(
                count = count, menuName = menuName, submenuName = submenuName, callbackName = self._callbackName, priority = self._priorities[cmdType]
                )
            )

    def GenerateMenuItems(self):
        for (key, value) in self._cmdItems.items():
            type = value["properties"].get("type", "default")
            self.GenerateMenuItem(key, type)
        self.CreateCSharpFile()
