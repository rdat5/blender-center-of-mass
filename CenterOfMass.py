# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Center of Mass",
    "author": "Ray Allen Datuin",
    "version": (0, 0, 3),
    "blender": (2, 90, 0),
    "location": "View3D > Tools > Center Of Mass",
    "description": "Visualizes the center of mass of a collection of objects",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

import bpy
import bmesh
import mathutils

# Classes

class ComProperties(bpy.types.PropertyGroup):
    com_obj : bpy.props.PointerProperty(name="Center of Mass Object", type=bpy.types.Object)
    com_coll : bpy.props.PointerProperty(name="Mass Collection", type=bpy.types.Collection)
    com_scale_to_floor : bpy.props.BoolProperty(name="Scale to floor", default=False)
    com_floor : bpy.props.FloatProperty(name="Floor", description="Where the Center of Mass scales to", default=0.0)
    com_snap_cursor : bpy.props.BoolProperty(name="Snap 3D Cursor", default=False)
    com_update_rate : bpy.props.IntProperty(name="", description="How fast 'Continuous Update' updates in milliseconds", default=5, min=1)

class CenterOfMassPanel(bpy.types.Panel):
    """Center of mass settings"""
    bl_label = "Center of Mass Settings"
    bl_idname = "OBJECT_PT_center_of_mass_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Center of Mass"
    
    def draw(self, context):
        layout = self.layout
        com_props = context.scene.com_properties
        timerOn = context.scene.get("timerOn")
        
        # Center of Mass
        row = layout.row(heading="Center of Mass", align=True)
        row.prop(com_props, "com_obj", text="")
        
        # Mass Objects
        row = layout.row(heading="Mass Objects", align=True)
        row.prop(com_props, "com_coll", text="")
        
        # Scale to floor
        row = layout.row(align=True)
        row.prop(com_props, "com_scale_to_floor")
        row.prop(com_props, "com_floor")
        
        # Snap 3D Cursor
        row = layout.row()
        row.prop(com_props, "com_snap_cursor")
        
        # Update
        col = layout.column(align=True)
        
        row = col.row()
        row.label(text="Update Center of Mass")
        
        row = col.row()
        row.operator("object.update_com", icon='FILE_REFRESH')
        
        row = col.row()
        row.scale_y = 2.0
        if timerOn == False:
            row.operator("wm.update_com_timer", icon='PLAY')
        elif timerOn == True:
            row.operator("wm.stop_com_timer", icon='PAUSE')
        
        row = col.row(align=True)
        row.label(text="Update rate (ms")
        row.prop(com_props, "com_update_rate")

class MassPropertiesPanel(bpy.types.Panel):
    """Mass properties panel"""
    bl_label = "Mass Properties"
    bl_idname = "OBJECT_PT_mass_properties_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Center of Mass"
    
    def draw(self, context):
        layout = self.layout
        selObj = context.selected_objects
        
        # Mass properties
        col = layout.column(align=True)
        
        row = col.row()
        row.label(text="Mass properties to selected")

        row = col.row(align=True)
        row.operator("object.comprop_add", text="Add", icon='ADD')
        row.operator("object.comprop_del", text="Remove", icon='REMOVE')
        
        # Volume
        col = layout.column(align=True)
        
        row = col.row()
        row.label(text="Volume")
        
        row = col.row()
        row.operator("object.calculate_volume", icon='CUBE')
        
        # Set active to selected
        col = layout.column(align=True)
        
        row = col.row()
        row.label(text="Set active to selected")
        
        row = col.row(align=True)
        row.operator("object.active_true", icon='RADIOBUT_ON')
        row.operator("object.active_false", icon='RADIOBUT_OFF')
        col.operator("object.toggle_active", icon='ARROW_LEFTRIGHT')
        
        # Selected mass objects
        col = layout.column(align=True)
        
        row = col.row(align=True)
        row.label(text="Selected Mass Objects: ")
        for obj in selObj:
            if obj.get('isMassObject') is not None:
                box = col.box()
                
                # split box
                split = box.split(factor=0.4)
                
                # left column
                col1 = split.column(align=True)
                col1.label(text="" + obj.name)
                
                # get if active
                if obj.get("active") == True:
                    col1.label(text="Active", icon='RADIOBUT_ON')
                elif obj.get("active") == False:
                    col1.label(text="Inactive", icon='RADIOBUT_OFF')
                
                # right column
                obj_mass = round(obj.get("density") * obj.get("volume") * obj.get("active"), 3)
                
                col2 = split.column(align=True)
                col2.prop(obj, '["density"]')
                col2.prop(obj, '["volume"]')
                col2.label(text="Mass: "  + str(obj_mass))

class AddMassProps(bpy.types.Operator):
    """Add mass properties to selected objects"""
    bl_idname = "object.comprop_add"
    bl_label = "Add mass properties to selected"
    
    def execute(self, context):
        selObj = context.selected_objects
        
        for obj in selObj:
            if obj.type == 'MESH':
                if obj.get('isMassObject') is None:
                    obj["isMassObject"] = True
                if obj.get('active') is None:
                    obj["active"] = True
                if obj.get('density') is None:
                    obj["density"] = 1.0
                if obj.get('volume') is None:
                    obj["volume"] = 1.0;
        return {'FINISHED'} 

class RemoveMassProps(bpy.types.Operator):
    """Remove mass properties from selected objects"""
    bl_idname = "object.comprop_del"
    bl_label = "Remove mass properties from selected"
    
    def execute(self, context):
        selObj = context.selected_objects
        
        for obj in selObj:
            if obj.type == 'MESH':
                if obj.get('active') is not None:
                    del obj["active"]
                if obj.get('density') is not None:
                    del obj["density"]
                if obj.get('volume') is not None:
                    del obj["volume"]
                if obj.get('isMassObject') is not None:
                    del obj["isMassObject"]
        return {'FINISHED'} 

class ToggleActiveProperty(bpy.types.Operator):
    """Toggles the active property"""
    bl_idname = "object.toggle_active"
    bl_label = "Toggle Active"
    
    def execute(self, context):
        selObj = context.selected_objects
        
        for obj in selObj:
            if obj.get('active') is not None:
                set_active(obj, (not obj['active']))
        return {'FINISHED'} 

class SetActiveTrue(bpy.types.Operator):
    """Toggles the active property"""
    bl_idname = "object.active_true"
    bl_label = "Active"
    
    def execute(self, context):
        selObj = context.selected_objects
        
        for obj in selObj:
            if obj.get('active') is not None:
                set_active(obj, True)
        return {'FINISHED'} 

class SetActiveFalse(bpy.types.Operator):
    """Toggles the active property"""
    bl_idname = "object.active_false"
    bl_label = "Inactive"
    
    def execute(self, context):
        selObj = context.selected_objects
        
        for obj in selObj:
            if obj.get('active') is not None:
                set_active(obj, False)
        return {'FINISHED'} 

class CalculateVolume(bpy.types.Operator):
    """Calculate volume of selected"""
    bl_idname = "object.calculate_volume"
    bl_label = "Calculate volume of selected"
    
    def execute(self, context):
        selObj = context.selected_objects
        
        for obj in selObj:
            if obj.get('isMassObject') is not None and obj.type == 'MESH':
                obj['volume'] = get_volume(obj)
        return {'FINISHED'} 

class UpdateCom(bpy.types.Operator):
    """Updates position of Center of Mass"""
    bl_idname = "object.update_com"
    bl_label = "Update Center of Mass"
    
    def execute(self, context):
        comObj = context.scene.com_properties.get("com_obj")
        comColl = context.scene.com_properties.get("com_coll")
        
        if comObj is not None and comColl is not None:
            updateComPosition()
        return {'FINISHED'}

class ComUpdateTimer(bpy.types.Operator):
    """Updates position of Center of Mass on a timer"""
    bl_idname = "wm.update_com_timer"
    bl_label = "Continuous Update"

    _timer = None

    def modal(self, context, event):
        timerOn = context.scene.get("timerOn")
        
        if timerOn == False:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            updateComPosition()

        return {'PASS_THROUGH'}

    def execute(self, context):
        com_props = context.scene.com_properties
        timerOn = context.scene.get("timerOn")
        update_rate = 5
        
        if com_props.get("com_update_rate") is None:
            update_rate = 5
        elif com_props.get("com_update_rate") is not None:
            update_rate = com_props.get("com_update_rate")
        
        wm = context.window_manager
        self._timer = wm.event_timer_add((update_rate / 100), window=context.window)
        wm.modal_handler_add(self)
        context.scene["timerOn"] = True
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class StopTimer(bpy.types.Operator):
    """Stops Continuous Update"""
    bl_idname = "wm.stop_com_timer"
    bl_label = "Stop Continuous Update"
    
    def execute(self, context):        
        context.scene["timerOn"] = False
        return {'FINISHED'}

# Function definitions

def set_active(obj, act):
    obj['active'] = act
    if act == True:
        obj.display_type = 'SOLID'
    elif act == False:
        obj.display_type = 'WIRE'

def get_volume(obj):
    volume = 0.0
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    me = obj_eval.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    obj_eval.to_mesh_clear()
    volume = bm.calc_volume()
    bm.free()
    
    return volume

def updateComPosition():
    com_props = bpy.context.scene.com_properties
    comObj = com_props.get("com_obj")
    comColl = com_props.get("com_coll")
    snap_cursor = False
    scale_floor = False
    floor_level = 0.0
    
    # Defaults
    if com_props.get("com_snap_cursor") is None:
        snap_cursor = False
    elif com_props.get("com_snap_cursor") is not None:
        snap_cursor = com_props.get("com_snap_cursor")
    
    if com_props.get("com_scale_to_floor") is None:
        scale_floor = False
    elif com_props.get("com_scale_to_floor") is not None:
        scale_floor = com_props.get("com_scale_to_floor")
    
    if com_props.get("com_floor") is None:
        floor_level = 0.0
    elif com_props.get("com_floor") is not None:
        floor_level = com_props.get("com_floor")
    
    # Calculate center of mass
    accum_mass = 0.0
    accum_pos = mathutils.Vector((0, 0, 0))

    old_pos = comObj.matrix_world.translation
    
    for obj in comColl.all_objects:
        if obj.get("active"):
            obj_mass = obj.get("density") * obj.get("volume")
            
            accum_mass += obj_mass
            accum_pos += (obj_mass * obj.matrix_world.translation)
    
    new_pos = (accum_pos / accum_mass)
    
    # Move center of mass object
    comObj.matrix_world.translation = new_pos

    # Move Cursor
    if snap_cursor:
        bpy.context.scene.cursor.location = comObj.matrix_world.translation
    
    # Scale to floor
    if scale_floor:
        floor = new_pos[2] - floor_level
        comObj.scale = [floor, floor, floor]

# Class registration

classes = (
    ComProperties,
    CenterOfMassPanel,
    MassPropertiesPanel,
    AddMassProps,
    RemoveMassProps,
    ToggleActiveProperty,
    SetActiveTrue,
    SetActiveFalse,
    CalculateVolume,
    UpdateCom,
    ComUpdateTimer,
    StopTimer
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.com_properties = bpy.props.PointerProperty(type=ComProperties)
    
    bpy.context.scene["timerOn"] = False

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.com_properties

    del bpy.context.scene["timerOn"]
    
if __name__ == "__main__":
    register()