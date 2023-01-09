from ursina import *
import openvr
from panda3d.core import ExecutionEnvironment
from p3dopenvr.p3dopenvr import *
from ursina.prefabs.trail_renderer import TrailRenderer
app = Ursina()

ovr = P3DOpenVR()
ovr.init()

def update():
    pass

class Pistol(Entity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(model="gun",scale= 0.01,add_to_scene_entities=add_to_scene_entities, **kwargs)
        self.rotation = (-90,90,10)
    def shoot(self):
        bullet = Bullet()
        bullet.position = self.world_position
        bullet.rotation = self.world_rotation
        
class Bullet(Entity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(model="sphere",scale= 0.01,add_to_scene_entities=add_to_scene_entities, **kwargs)
        self.rotation = (-90,90,10)
        TrailRenderer(parent=self, x=.1, thickness=1, color=color.orange)

    def update(self):
        self.position += self.forward * time.dt *-500

def process_vr_event(event):
    if event.eventType == 200:
        print("shoot")
        pistol.shoot()

def new_tracked_device(device_index, device_anchor):
    """
    Attach a trivial model to the anchor or the detected device
    """

    print("Adding new device", device_anchor.name)
    device_class = ovr.vr_system.getTrackedDeviceClass(device_index)
    if device_class == openvr.TrackedDeviceClass_Controller:
        pistol.parent = device_anchor
    else:
        model = loader.loadModel("camera")
        model.reparent_to(device_anchor)
        model.set_scale(0.1)


pistol = Pistol()
# Register a general event handler
ovr.register_event_handler(process_vr_event)

Text(text="Press 'h' to hide the controllers", scale=0.05, parent=camera.ui, position=(0, 0.1))

ovr.set_new_tracked_device_handler(new_tracked_device)
app.run()