from ursina import *
import openvr
from panda3d.core import ExecutionEnvironment
from p3dopenvr.p3dopenvr import *
from ursina.prefabs.trail_renderer import TrailRenderer
app = Ursina()

ovr = P3DOpenVR()
ovr.init()

shoot=Audio('shot.ogg',autoplay=False)

def update():
    pass

class Pistol(Entity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(model="gun",color=color.dark_gray,scale= 0.01,add_to_scene_entities=add_to_scene_entities, **kwargs)
        self.rotation = (-90,90,10)
    def shoot(self):
        bullet = Bullet(position=self.world_position+self.back*20, rotation=self.world_rotation)
        if not shoot.playing:
            shoot.play()
        if shoot.playing:
            shoot.stop()
            shoot.play()
        
class Bullet(Entity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(model="sphere",scale= 0.01,add_to_scene_entities=add_to_scene_entities, **kwargs)
        TrailRenderer(parent=self, x=.1, thickness=5, color=color.orange)
    
    def update(self):
        ray = raycast(self.world_position, self.forward, distance=0.1, ignore=[self],debug=True )
        if ray.hit:
            destroy(self)
            if hasattr(ray.entity, 'hit'):
                ray.entity.hit()
        else:
            self.position += self.forward * time.dt *-500
            dist=distance_2d(self.position, pistol.position)
            self.position += self.forward * time.dt *-500
            if dist>12:
                destroy(self)
    
class Target(Entity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(model="cube",texture="target",scale= 0.3,add_to_scene_entities=add_to_scene_entities, **kwargs)
        self.collider = 'box'
    
    def hit(self):
        destroy(self)
    
    
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


def changez():
    pistol.rotation_z = zslider.value
def changey():
    pistol.rotation_y = yslider.value
def changex():
    pistol.rotation_x = xslider.value

xslider = Slider(parent=camera.ui, min=-180, max=180, step=1, text="x", dynamic=True, origin=(-.5, .5), y=-.1, value=-90,on_value_changed=changex)
yslider = Slider(parent=camera.ui, min=-180, max=180, step=1, text="y", dynamic=True, origin=(-.5, .5), y=0, value=90,on_value_changed=changey)
zslider = Slider(parent=camera.ui, min=-180, max=180, step=1, text="z", dynamic=True, origin=(-.5, .5), y=.1, value=10,on_value_changed=changez)

pistol = Pistol()

Entity(model="plane", scale=100, texture="grass",texture_scale=(4,4), double_sided=True, collider="box", color=color.green)

targets = [Target(position=(random.randint(-5,5),1, random.randint(1,10))) for _ in range(10)]

# Register a general event handler
ovr.register_event_handler(process_vr_event)


ovr.set_new_tracked_device_handler(new_tracked_device)
app.run()