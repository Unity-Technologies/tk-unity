# This script takes a list of cmd names and functions, and generates a C# script
# that then populates a Unity menu with the cmd names, and calling the functions in python.

import os

class MenuItemGenerator(object):
    def __init__(self, projectPath, cmdItems, callbackName):
        self._cSharpClass = "ShotgunMenuItems"
        self._cmdItems = cmdItems
        self._callbackName = callbackName
        self._projectPath = projectPath
        self._functionList = []
        self._functionTemplate = """
            [MenuItem("Shotgun/{menuName}")]
            public static void MenuItem{count}(){{
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().{callbackName}(\\\"{menuName}\\\")");
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
    
    def GenerateMenuItem(self, cmdName):
        count = len(self._functionList) + 1
        self._functionList.append(
            self._functionTemplate.format(
                count = count, menuName = cmdName, callbackName = self._callbackName
                )
            )

    def GenerateMenuItems(self):
        for key in self._cmdItems:
            self.GenerateMenuItem(key)
        self.CreateCSharpFile()
