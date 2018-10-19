# This script takes a list of cmd names and functions, and generates a C# script
# that then populates a Unity menu with the cmd names, and calling the functions in python.

import os
from collections import defaultdict

class MenuItemGenerator(object):
    def __init__(self, projectPath, cmdItems, contextName, callbackName):
        self._cSharpClass = "ShotgunMenuItems"
        self._cmdItems = cmdItems
        self._callbackName = callbackName
        self._projectPath = projectPath
        self._contextName = contextName # name for context menu item folder
        self._contextMenuFormat = self._contextName + "/{0}"
        
        # The difference in priorities will add separators between the three menu sections
        # as a priority increase of 10 or more creates a separator.
        # Note: default dict will use 22 as the default value if the key doesn't match any of the other keys
        self._priorities = defaultdict(lambda:22, context_menu=0, favorite=11)
        
        self._functionList = []
        self._functionTemplate = """
            [MenuItem("Shotgun/{menuName}", false, {priority})]
            public static void MenuItem{count}(){{
                PythonRunner.RunString("import sgtk\\nsgtk.platform.current_engine().{callbackName}('{menuName}')");
            }}
        """
        self._fileContentsTemplate = """
        using UnityEditor;
        using UnityEngine;
        using System.IO;
        
        class {className}{{
            {functions}
        }}
        """
        
    def CreateCSharpFile(self):
        functionStr = "\n\n".join(self._functionList)
        fileContents = self._fileContentsTemplate.format(className = self._cSharpClass, functions = functionStr)
        cSharpFile = None
        try:
            cSharpFile = open(os.path.join(self._projectPath, "{0}.cs".format(self._cSharpClass)), "w+")
            cSharpFile.write(fileContents)
        finally:
            if cSharpFile:
                cSharpFile.close()
    
    def GenerateMenuItem(self, cmdName, cmdType):
        count = len(self._functionList) + 1
        
        menuName = cmdName
        if cmdType == "context_menu":
            menuName = self._contextMenuFormat.format(cmdName)
        
        self._functionList.append(
            self._functionTemplate.format(
                count = count, menuName = menuName, callbackName = self._callbackName, priority = self._priorities[cmdType]
                )
            )

    def GenerateMenuItems(self):
        for (key, value) in self._cmdItems.items():
            type = value["properties"].get("type", "default")
            self.GenerateMenuItem(key, type)
        self.CreateCSharpFile()
