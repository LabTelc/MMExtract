from vispy.scene.cameras import PanZoomCamera


class CustomPanZoomCamera(PanZoomCamera):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)


    def viewbox_mouse_event(self, event):
        event.handled = True
        super().viewbox_mouse_event(event)