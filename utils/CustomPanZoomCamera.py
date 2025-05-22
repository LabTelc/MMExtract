from vispy.scene.cameras import PanZoomCamera


class CustomPanZoomCamera(PanZoomCamera):
    def viewbox_mouse_event(self, event):
        event.handled = True
        super().viewbox_mouse_event(event)