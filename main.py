from ursina import *
from panda3d.core import Camera as PandaCamera
from p3dopenvr.p3dopenvr import *
from ursina.prefabs.trail_renderer import TrailRenderer
from direct.actor.Actor import Actor
"""
- dynamic pickup both does and doesn't work cant really explain it
"""
app = Ursina()

ovr = P3DOpenVR()
ovr.init()


shoot_sound=Audio('shot.ogg',autoplay=False)

current_weapon = None
right, left = None, None
right_hand, left_hand = None, None


class PhysicsEntity(Entity):
    def __init__(self,mass=1,gravity=4, add_to_scene_entities=True, **kwargs):
        super().__init__(add_to_scene_entities=add_to_scene_entities, **kwargs)
        self.held = False
        self.held_by = None
        self.velocity = Vec3(0,0,0)
        self.freeze = False
        self.mass = mass
        self.gravity = gravity
        self.last_position = self.world_position
    def update(self):
        if not self.freeze and not self.held:
            ray = raycast(self.world_position, (0,-1,0), distance=-self.velocity[1]*time.dt, ignore=(self,))
            if ray.world_point:
                self.position = ray.world_point
                self.velocity[1] *= -0.5
                self.velocity *= 0.8
            else:
                self.position += self.velocity*time.dt
                self.velocity[1] -= self.gravity*self.mass*time.dt
            self.velocity *= 0.9
            self.velocity[0] = round(self.velocity[0], 2)
            self.velocity[1] = round(self.velocity[1], 2)
            self.velocity[2] = round(self.velocity[2], 2)    
        
        elif self.held:
            self.velocity = (self.world_position - self.last_position) / time.dt
            self.last_position = self.world_position
        
        if hasattr(self, 'custom_update'):
            self.custom_update()

    def _on_hold(self):
        self.parent = self.held_by
        self.position =(0,0,0)
        if hasattr(self, 'on_hold'):
            self.on_hold()
            
    def _on_release(self):
        self.position = self.world_position
        self.rotation = self.world_rotation
        self.parent = scene
        if hasattr(self, 'on_release'):
            self.on_release()
            
class Pistol(PhysicsEntity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(model="gun",color=color.dark_gray,scale= 0.01,add_to_scene_entities=add_to_scene_entities, **kwargs)
        self.rotation = Vec3(0,90,0)
        self.mass = 5
    def shoot(self):
        bullet = Bullet(position=self.world_position+self.back*20, rotation=self.world_rotation)
        if not shoot_sound.playing:
            shoot_sound.play()
        if shoot_sound.playing:
            shoot_sound.stop()
            shoot_sound.play()
            
    def on_hold(self):
        self.rotation = Vec3(-90,90,10)
    
    def input(self,key):
        if key == 'right vr_trigger' and self.held:
            self.shoot()
        
        
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
            self.position += self.forward * time.dt *-600
            if dist>12:
                destroy(self)
    
class Target(Entity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(model="cube",texture="target",scale= 0.3,add_to_scene_entities=add_to_scene_entities, **kwargs)
        self.collider = 'box'
    
    def hit(self):
        destroy(self)
        """
        def respawn():
            targets = [Target(position=(random.randint(-5,5),1, random.randint(1,10)))]
        invoke(respawn,delay=1.5)

        simple respawn funcion
        """
    
def input(key):
    global current_weapon
    print(key)
    if key == 'right vr_grip':
        if not right :
            return
        for e in scene.entities:
            if not issubclass(type(e), PhysicsEntity):
                continue
            if e.held:
                continue
            if distance(e.world_position, right.getPos(scene)) < 0.5:
                e.held = True
                e.held_by = right
                if hasattr(e, '_on_hold'):
                    e._on_hold() 
                current_weapon = e
                right_hand.disable()
                break
            
    if key == 'right vr_grip up':
        
        if not current_weapon or not right :
            return
        current_weapon.held = False
        current_weapon.held_by = None
        if hasattr(current_weapon, '_on_release'):
            current_weapon._on_release()
        current_weapon = None
        right_hand.enable()
    if key == 'left vr_grip':
        left_hand_close.show()
        left_hand.disable()
        left_hand_open.hide()
        left_hand_close.play('ArmatureAction.001')
    if key == 'left vr_grip up':
        left_hand_open.show()
        left_hand_close.hide()
        left_hand_open.play('ArmatureAction.001')
        invoke(left_hand.enable,delay=1)

classes_map = { openvr.TrackedDeviceClass_Invalid: 'Invalid',
                openvr.TrackedDeviceClass_HMD: 'HMD',
                openvr.TrackedDeviceClass_Controller: 'Controller',
                openvr.TrackedDeviceClass_GenericTracker: 'Generic tracker',
                openvr.TrackedDeviceClass_TrackingReference: 'Tracking reference',
                openvr.TrackedDeviceClass_DisplayRedirect: 'Display redirect',
                }

roles_map = { openvr.TrackedControllerRole_Invalid: 'Invalid',
                openvr.TrackedControllerRole_LeftHand: 'Left',
                openvr.TrackedControllerRole_RightHand: 'Right',
                openvr.TrackedControllerRole_OptOut: 'Opt out',
                openvr.TrackedControllerRole_Treadmill: 'Treadmill',
                openvr.TrackedControllerRole_Stylus: 'Stylus',
            }

buttons_map = { openvr.k_EButton_System: 'System',
                openvr.k_EButton_ApplicationMenu: 'Application Menu',
                openvr.k_EButton_Grip: 'Grip',
                openvr.k_EButton_DPad_Left: 'Pad left',
                openvr.k_EButton_DPad_Up: 'Pad up',
                openvr.k_EButton_DPad_Right: 'Pad right',
                openvr.k_EButton_DPad_Down: 'Pad down',
                openvr.k_EButton_A: 'A',
                openvr.k_EButton_ProximitySensor: 'Proximity sensor',
                openvr.k_EButton_Axis0: 'Axis 0',
                openvr.k_EButton_Axis1: 'Axis 1',
                openvr.k_EButton_Axis2: 'Axis 2',
                openvr.k_EButton_Axis3: 'Axis 3',
                openvr.k_EButton_Axis4: 'Axis 4',
                #openvr.k_EButton_SteamVR_Touchpad: 'Touchpad',
                #openvr.k_EButton_SteamVR_Trigger: 'Trigger',
                #openvr.k_EButton_Dashboard_Back: 'Dashboard back',
                #openvr.k_EButton_IndexController_A: 'Controller A',
                #openvr.k_EButton_IndexController_B: 'Controller B',
                #openvr.k_EButton_IndexController_JoyStick: 'Controller joystick',

                }

button_events_map = { openvr.VREvent_ButtonPress: 'Press',
                        openvr.VREvent_ButtonUnpress: 'Unpress',
                        openvr.VREvent_ButtonTouch: 'Touch',
                        openvr.VREvent_ButtonUntouch: 'Untouch'
                    }

def button_event(event):
    """
    Print the information related to the button event received.
    """

    device_index = event.trackedDeviceIndex
    device_class = ovr.vr_system.getTrackedDeviceClass(device_index)
    if device_class != openvr.TrackedDeviceClass_Controller:
        return
    button_id = event.data.controller.button
    button_name = buttons_map.get(button_id)
    if button_name is None:
        button_name = 'Unknown button ({})'.format(button_id)
    role = ovr.vr_system.getControllerRoleForTrackedDeviceIndex(device_index)
    role_name = roles_map.get(role)
    if role_name is None:
        role_name = 'Unknown role ({})'.format(role)
    event_name = button_events_map.get(event.eventType)
    if event_name is None:
        event_name = 'Unknown event ({})'.format(event.eventType)
    key = '{} {}'.format(role_name.lower(), button_name.lower())
    if event_name != 'Press':
        key += " "+event_name.lower().replace("unpress","up")
    
    custom_input_replacements = {
        "axis 1":"vr_trigger",
        "grip":"vr_grip",
        "axis 2":"vr_grip",
        "right application menu":"vr_b",
        "left a":"vr_x",
        "right a":"vr_a",
        "left application menu":"vr_y"
        }
    
    for name,custom_replacement in custom_input_replacements.items():
        key = key.replace(name,custom_replacement)
    
    input(key)
    for e in scene.entities:
        if hasattr(e, 'input'):
            e.input(key)

def device_event( event, action):
    """
    Print the information related to the device event received.
    """

    device_index = event.trackedDeviceIndex
    device_class = ovr.vr_system.getTrackedDeviceClass(device_index)
    class_name = classes_map.get(device_class)
    if class_name is None:
        class_name = 'Unknown class ({})'.format(class_name)
    print('Device {} {} ({})'.format(event.trackedDeviceIndex, action, class_name))

def process_vr_event(event):
    if event.eventType == openvr.VREvent_TrackedDeviceActivated:
        device_event(event, 'attached')
    if event.eventType == openvr.VREvent_TrackedDeviceDeactivated:
        device_event(event, 'deactivated')
    elif event.eventType == openvr.VREvent_TrackedDeviceUpdated:
        device_event(event, 'updated')
    elif event.eventType in (openvr.VREvent_ButtonPress,
                            openvr.VREvent_ButtonUnpress,
                            openvr.VREvent_ButtonTouch,
                            openvr.VREvent_ButtonUntouch):
        button_event(event)
        
def new_tracked_device(device_index, device_anchor):
    """
    Attach a trivial model to the anchor or the detected device
    """
    global right , left,right_hand,left_hand, left_hand_close, left_hand_open
    print("Adding new device", device_anchor.name)
    device_class = ovr.vr_system.getTrackedDeviceClass(device_index)
    if device_class == openvr.TrackedDeviceClass_Controller:
        if "left" in device_anchor.name:
            left_hand = Entity(model="vr_glove_right_model_slim.fbx", scale=1, rotation=Vec3(0,-180, 0), position=Vec3(0, 0, -.1), color=color.clear)
            left_hand.parent = device_anchor
            left = device_anchor
            left_hand_close=Actor('models/vr_glove_left_model_slim_close.gltf')
            left_hand_close.setH(-180)
            left_hand_close.setPos(0,0,-0.1)
            left_hand_close.reparentTo(left)
            left_hand_close.play('ArmatureAction.001')
            left_hand_open=Actor('models/vr_glove_left_model_slim_open.gltf')
            left_hand_open.setH(-180)
            left_hand_open.setPos(0,0,-0.1)
            left_hand_open.reparentTo(left)
            left_hand_close.hide()
            #you'll have to sort out the rotations and postions and when the anim plays
        else :
            right_hand = Entity(model="vr_glove_left_model_slim.fbx", scale=1, rotation=Vec3(0,-180, 0), position=Vec3(0, 0, -.1), color=color.white)
            right_hand.parent = device_anchor
            right = device_anchor
        #pistol.parent = device_anchor
    """
    else:
        model = loader.loadModel("camera")
        model.reparent_to(device_anchor)
        model.set_scale(0.1)
    """

pistol = Pistol(position = (0,2,1))

ground = Entity(model="plane", scale=100, texture="grass",texture_scale=(4,4), double_sided=True, collider="box", color=color.green)

targets = [Target(position=(random.randint(-5,5),1, random.randint(1,10))) for _ in range(10)]

table = Entity(model="cube", scale=(2,1.5,1), texture="wood", collider="box",position=(0,0,1))


# Register a general event handler
ovr.register_event_handler(process_vr_event)

ovr.set_new_tracked_device_handler(new_tracked_device)

EditorCamera()
app.run()