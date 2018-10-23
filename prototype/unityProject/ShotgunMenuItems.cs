
        using UnityEditor;
        using UnityEngine;
        using System.IO;
        
        class ShotgunMenuItems{
            
            [MenuItem("Shotgun/Scene Breakdown...")]
            public static void MenuItem1(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Scene Breakdown...\")");
            }
        


            [MenuItem("Shotgun/Toggle Debug Logging")]
            public static void MenuItem2(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Toggle Debug Logging\")");
            }
        


            [MenuItem("Shotgun/Load...")]
            public static void MenuItem3(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Load...\")");
            }
        


            [MenuItem("Shotgun/Work Area Info...")]
            public static void MenuItem4(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Work Area Info...\")");
            }
        


            [MenuItem("Shotgun/Shotgun Panel...")]
            public static void MenuItem5(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Shotgun Panel...\")");
            }
        


            [MenuItem("Shotgun/Publish...")]
            public static void MenuItem6(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Publish...\")");
            }
        


            [MenuItem("Shotgun/Shotgun Python Console...")]
            public static void MenuItem7(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Shotgun Python Console...\")");
            }
        


            [MenuItem("Shotgun/Open Log Folder")]
            public static void MenuItem8(){
                Bootstrap.RunPythonCodeOnClient("import sgtk");
                Bootstrap.RunPythonCodeOnClient("sgtk.platform.current_engine().call_menu_item_callback(\"Open Log Folder\")");
            }
        
        }
        