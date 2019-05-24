import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class UnityPostBootstrap(HookBaseClass):
    def on_post_init(self, engine):
        """
        This method is invoked when tk-unity has successfully initialized
        """
        pass
