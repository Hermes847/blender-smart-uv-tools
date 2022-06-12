import bpy
from . import utils as u
import mathutils
import bmesh
import math
 
         
class AlignUV(bpy.types.Operator):
    bl_idname = 'uv.align_uv'
    bl_label = 'align uv'
    bl_description = 'align uv'
    bl_options = {'REGISTER', 'UNDO'}
        # enum set in {'REGISTER', 'UNDO', 'UNDO_GROUPED', 'BLOCKING', 'MACRO', 'GRAB_CURSOR', 'PRESET', 'INTERNAL'}
    bl_undo_group = ""  # Unused without 'UNDO_GROUPED'.
    
    align_method = bpy.props.EnumProperty(
            name = "mine.align_method",
            description = "align method",
            items = [
                ("AVG", "AVG", "align uvs at avg point"),
                ("MIN", "MIN", "align uvs at min point"),          
                ("MAX", "MAX", "align uvs at max point"),    
            ]        
        )
  
    
    @classmethod
    def poll(self, context):
        return context.active_object!=None
      
    def execute(self,context):
        obj = context.active_object
        g = u.UVGraph(obj)
        selected = g.get_selected()
        sg = g.get_sub_graph(selected)
        for x,adjs in sg.items():
            for y in adjs:
                g.align_uv_axis(x,y,str(self.align_method))
        g.update_bmesh()    
         
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
  
        layout.prop(self, 'align_method')

class ExtendSelectedEdges(bpy.types.Operator):
    bl_idname = 'uv.extend_selected_edges'
    bl_label = 'extend selected edges'
    bl_description = 'extend elected edges'
    bl_options = {'REGISTER', 'UNDO'}
        # enum set in {'REGISTER', 'UNDO', 'UNDO_GROUPED', 'BLOCKING', 'MACRO', 'GRAB_CURSOR', 'PRESET', 'INTERNAL'}
    bl_undo_group = ""  # Unused without 'UNDO_GROUPED'.
    
    angle_tolerance = bpy.props.FloatProperty(description="Max angle tolerance",default=45)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'angle_tolerance')
        
      
    def extend_edge(self,v1,v2,uv_graph,angle_tolerance):

        last_index = v1
        cur_index = v2

        while True:
            last_pos = uv_graph.uvs[last_index][uv_graph.uv_layer].uv
            cur_pos = uv_graph.uvs[cur_index][uv_graph.uv_layer].uv
            cur_dir = cur_pos-last_pos#uvs[cur_index[0]][cur_index[1]].uv-uvs[last_index[0]][last_index[1]].uv
            cur_dir.normalize()
            next_index = 0
            max_dot = -1
            for candidate_index in uv_graph[cur_index]:
                candidate_pos = uv_graph.uvs[candidate_index][uv_graph.uv_layer].uv
                candidate_dir = candidate_pos-cur_pos
                candidate_dir.normalize()
                dot = candidate_dir @ cur_dir
                
                if dot > max_dot:
                    max_dot = dot
                    next_index = candidate_index
                    
            next_seleted = uv_graph.uvs[next_index][uv_graph.uv_layer].select
            if  max_dot > math.cos(math.pi*angle_tolerance/180) and not next_seleted:
                uv_graph.set_select_uv(next_index)     
                last_index = cur_index         
                cur_index = next_index               
            else:
                break   

    def execute(self,context):
        at = float(self.angle_tolerance)
        obj = context.active_object
        g = u.UVGraph(obj)
        selected_edges = g.get_edges_uvs(g.get_selected())
        for v1,v2 in selected_edges:
            self.extend_edge(v1,v2,g,at)
            self.extend_edge(v2,v1,g,at)
        g.update_bmesh()    
        return {'FINISHED'}
    
class UniformScale(bpy.types.Operator):
    bl_idname = 'uv.uniform_scale'
    bl_label = 'uniform scale'
    bl_description = 'uniform scale'
    bl_options = {'REGISTER', 'UNDO'}
        # enum set in {'REGISTER', 'UNDO', 'UNDO_GROUPED', 'BLOCKING', 'MACRO', 'GRAB_CURSOR', 'PRESET', 'INTERNAL'}
    bl_undo_group = ""  # Unused without 'UNDO_GROUPED'.
    
    def execute(self,context):
        objs = context.selected_objects
        gs = [u.UVGraph(x) for x in objs]
        values = []
        for g in gs:
            for island in g.get_islands():
                values.append(g.get_uv_geo_ratio(island))
                
        avg_ratio = sum(values)/len(values)
        for g in gs:
            for island in g.get_islands():
                g.fix_uv_geo_ratio(avg_ratio)
            g.update_bmesh()     
            
        return {'FINISHED'}
        # obj = context.active_object
        # g = u.UVGraph(obj)
        # edges = g.get_edges_uvs(g.get_selected(),False)
        # g.uniform_all_shells([g.get_linked(x[0]) for x in edges],edges)
        # g.update_bmesh()     
        # return {'FINISHED'}

class SelectLongestEdges(bpy.types.Operator):
    bl_idname = 'uv.select_longest_edges'
    bl_label = 'select longest edges'
    bl_description = 'select longest edges'
    bl_options = {'REGISTER', 'UNDO'}
        # enum set in {'REGISTER', 'UNDO', 'UNDO_GROUPED', 'BLOCKING', 'MACRO', 'GRAB_CURSOR', 'PRESET', 'INTERNAL'}
    bl_undo_group = ""  # Unused without 'UNDO_GROUPED'.
    def execute(self,context):
        obj = context.active_object
        g = u.UVGraph(obj)
        islands = g.get_islands(True)
        longest_edges = [g.find_longest_edges(x)[0] for x in islands]
        g.deselect_all()
        for x in longest_edges:
            g.set_select_uv(x[0],True)
            g.set_select_uv(x[1],True)
        g.update_bmesh()     
        return {'FINISHED'}
    
class StraightenQuads(bpy.types.Operator):
    bl_idname = 'uv.straighten_quads'
    bl_label = 'straighten quads'
    bl_description = 'Find the best quad, straighten it and adjust the uv ratio, then the other quads follow the quad'
    bl_options = {'REGISTER', 'UNDO'}
        # enum set in {'REGISTER', 'UNDO', 'UNDO_GROUPED', 'BLOCKING', 'MACRO', 'GRAB_CURSOR', 'PRESET', 'INTERNAL'}
    bl_undo_group = ""  # Unused without 'UNDO_GROUPED'.
    
    
    # def flow_quad(self,g,face_view,vert_in_face,quad_to_flow):
    #     verts_in_the_quad = vert_in_face[quad_to_flow]
    #     indices = verts_in_the_quad+[verts_in_the_quad[0]]
    #     for i in range(len(indices)-1):           
    #         g.align_uv_axis(self,indices[i],indices[i+1],method = 'AVG') 
    #     geo_locs = [g.me.vertices[g.uvs[x].vert.index].co for x in verts_in_the_quad]
    #     uv_locs = [g.uvs[x][g.uv_layout].uv for x in verts_in_the_quad]
    #     geo_l1 = (geo_locs[1]-geo_locs[0]).length
    #     geo_l2 = (geo_locs[2]-geo_locs[1]).length
    #     geo_ratio = geo_l2/geo_l1
    #     uv_l1 = (uv_locs[1]-uv_locs[0]).length
    #     uv_l2 = (uv_locs[2]-uv_locs[1]).length
    #     uv_ratio = uv_l2/uv_l1
    #     move_dir = (uv_locs[2]-uv_locs[1])
    #     move_dir.normalize()
    #     move_by = move_dir*uv_l2*(geo_ratio/uv_ratio-1)
    #     g.moveby_uv(verts_in_the_quad[2],move_by)
    #     g.moveby_uv(verts_in_the_quad[3],move_by)
    
    
    def execute(self,context):
        obj = context.active_object
        g = u.UVGraph(obj)
        islands = g.get_islands(True)
        
        uv_geo_ratio = None
        for island in islands:
            face_view,vert_in_face = g.build_face_view(island)
            if not face_view:
                if len(vert_in_face) ==4:
                    best_quad = vert_in_face.keys()[0]
                else:
                    continue
            else:
                best_quad,value = g.find_best_quad(face_view,vert_in_face)
            if best_quad == -1 :
                continue
            g.straighten_quad(vert_in_face[best_quad])
            s = g.scale_quad_to_geo(vert_in_face[best_quad],uv_geo_ratio)
            if not uv_geo_ratio:
                uv_geo_ratio = s
            g.flow_quad(best_quad,island,face_view,vert_in_face,uv_geo_ratio)
        g.update_bmesh()        
        return {'FINISHED'}
    
    
    # def draw(self, context):
    #     layout = self.layout
  
    #     layout.prop(self, 'align_method')