import bpy
import inspect
from . import my_ops



class MyPanel(bpy.types.Panel):
    bl_idname = 'my_panel'
    bl_label = 'my tools'
    bl_category = 'my tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self,context):
        layout = self.layout       
        for name, obj in inspect.getmembers(my_ops):
            if inspect.isclass(obj) and issubclass(obj,bpy.types.Operator): 
                if obj.bl_idname.split('.')[0] == 'view3d':    
                    row = layout.row()
                    row.operator(obj.bl_idname,text = obj.bl_label)
                
class MyUVPanel(bpy.types.Panel):
    bl_idname = 'smart_uv_panel'
    bl_label = 'smart uv tools'
    bl_category = 'smart uv tools'
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    
    def draw(self,context):
        layout = self.layout       
        for name, obj in inspect.getmembers(my_ops):
            if inspect.isclass(obj) and issubclass(obj,bpy.types.Operator): 
                if obj.bl_idname.split('.')[0] == 'uv':    
                    row = layout.row()
                    row.operator(obj.bl_idname,text = obj.bl_label)    

                