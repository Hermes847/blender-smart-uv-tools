import mathutils 
import bpy 
import bmesh
import math
import random
def group_by(arr,key = None,value = None):
    def add_value(k,v,ret):
        if k in ret:
            ret[k].append(v)
        else:
            ret[k] = [v]
    ret = {}
    for i,x in enumerate(arr):
        if key == None:
            k = x
        else:
            k = key(x)
        if value == None:
            v = i
        else:
            v = value(i)
            
        if isinstance(k,list):
            for _k in k:
                add_value(_k,v,ret)
        else:
            add_value(k,v,ret)

    return ret

def cal_cos(p1,p2,p3):
    v1 = p1-p2
    v1.normalize()
    v2 = p2-p3
    v2.normalize()
    return v1 @ v2

class UVGraph:
    
    def __init__(self,obj,uv_layer = None):       
        self.me = obj.data
        self.bm = bmesh.from_edit_mesh(self.me)
        if uv_layer:
            self.uv_layer = uv_layer
        else:
            self.uv_layer = self.bm.loops.layers.uv.verify()
        self.uvs = []
        self.edges = set()
        self.graph = {}
        self.equal_loops = {}
        self.uv_index_mapping = {}
        loops_cleaned = []
        loops = [l for f in self.bm.faces for l in f.loops]
               
        loops_group_by_vert = group_by(loops,key = lambda x:x.vert.index,value = lambda x:loops[x])
        
        mapping = {}
        
        for _,ls in loops_group_by_vert.items():
            temp = []
            for l1 in ls:          
                is_same = False
                for l_index,l2 in temp:
                    uv1 = l1[self.uv_layer].uv
                    uv2 = l2[self.uv_layer].uv
                    if (uv1-uv2).length < 1e-4:
                        if l_index in self.equal_loops:
                            self.equal_loops[l_index].append(l1)
                        else:
                            self.equal_loops[l_index]=[l1]
                        is_same = True
                        mapping[(l1.face.index,l1.vert.index)] = l_index
                        break
                if not is_same:
                    loop_index = len(loops_cleaned)
                    mapping[(l1.face.index,l1.vert.index)] = loop_index
                    temp.append((loop_index,l1))
                    loops_cleaned.append(l1)
                
                    
        for i,l in enumerate(loops_cleaned):            
            self.uvs.append(l)
            next_loops = [l.link_loop_next]
            if i in self.equal_loops:
                for l2 in self.equal_loops[i]:
                    next_loops.append(l2.link_loop_next)
            for nl in next_loops:
                next_index = mapping[(nl.face.index,nl.vert.index)]
                self.edges.add((i,next_index))
                
        for e in self.edges:
            if e[0] not in self.graph:
                self.graph[e[0]] = set()
            if e[1] not in self.graph:
                self.graph[e[1]] = set()
            self.graph[e[0]].add(e[1])
            self.graph[e[1]].add(e[0])
            
        for i,l in enumerate(self.uvs):
            self.uv_index_mapping[(l.face.index,l.vert.index)] = i

    def straighten_quad(self,verts,method = 'AVG'):
        indices = verts+[verts[0]]
        for i in range(len(indices)-1):
            self.align_uv_axis(indices[i],indices[i+1],method)
        
    def align_uv_axis(self,index1,index2,method = 'AVG'):
        
        if method == 'AVG':
            method_f = (lambda v1,v2:(v1.x+v2.x)/2,lambda v1,v2:(v1.y+v2.y)/2)
        elif method == 'MIN':
            method_f = (lambda v1,v2:min(v1.x,v2.x),lambda v1,v2:min(v1.y,v2.y))
        elif method == 'MAX':
            method_f = (lambda v1,v2:max(v1.x,v2.x),lambda v1,v2:max(v1.y,v2.y))
        else:
            raise Exception('no such method')
        
        v1 = self.uvs[index1][self.uv_layer].uv 
        v2 = self.uvs[index2][self.uv_layer].uv 
        if abs(v1.x-v2.x)>abs(v1.y-v2.y):          
            y = method_f[1](v1,v2)
            self.moveto_uv(index1,mathutils.Vector([v1.x,y]))
            self.moveto_uv(index2,mathutils.Vector([v2.x,y]))
        else:
            x = method_f[0](v1,v2)
            self.moveto_uv(index1,mathutils.Vector([x,v1.y]))
            self.moveto_uv(index2,mathutils.Vector([x,v2.y]))
            
    def get_sub_graph(self,indices):
        sg = {}
        indices = set(indices)
        for i in indices:
            sg[i] = self.graph[i].intersection(indices)   
        return sg
    
    def update_bmesh(self):
        bmesh.update_edit_mesh(self.me)
        
    def free(self):
        self.bm.free()
        
    def get_selected(self):
        selected = []
        for i,l in enumerate(self.uvs):
            is_select = False
            if l[self.uv_layer].select:
                selected.append(i)
                is_select = True
            elif i in self.equal_loops:             
                for l2 in self.equal_loops[i]:
                    if l2[self.uv_layer].select: 
                        selected.append(i)
                        is_select = True
                        break
            if is_select:
                if i in self.equal_loops:  
                    for l2 in self.equal_loops[i]:
                        l2[self.uv_layer].select = True
                l[self.uv_layer].select = True
        
        return selected
                        
    def moveby_uv(self,index,vector):
        self.uvs[index][self.uv_layer].uv+=vector
        if index in self.equal_loops:
            for l2 in self.equal_loops[index]:
                l2[self.uv_layer].uv+=vector
        
    def moveto_uv(self,index,pos):
        self.uvs[index][self.uv_layer].uv=pos
        if index in self.equal_loops:
            for l2 in self.equal_loops[index]:
                l2[self.uv_layer].uv=pos
         
    def set_select_uv(self,index,select=True):
        l = self.uvs[index]      
        if index in self.equal_loops:
            for l2 in self.equal_loops[index]:
                l2[self.uv_layer].select = select
        l[self.uv_layer].select = select
        
    def get_linked(self,uv_id,selected = None):
        open_set = self.graph[uv_id]
        if selected:
            open_set.intersection_update(selected)
        close_set = set([uv_id])
        while len(open_set)>0:
            temp = set()
            for x in open_set:
                close_set.add(x)
                if x in self.graph:
                    temp.update(self.graph[x])
            open_set = temp-close_set
            if selected:
                open_set.intersection_update(selected)
        return close_set
                
    def get_islands(self,select_only=False):
        islands = []
        selected = self.get_selected()
        if select_only:
            open_set = set(selected)
        else:
            open_set = set(range(len(self.uvs)))
        while len(open_set) > 0 :
            x = open_set.pop()
            island = self.get_linked(x,selected)
            islands.append(island)
            open_set.difference_update(island)
                       
        return islands
 
    def find_best_quad(self,face_view,vert_in_face):
        best_index = 0
        best_value = 1
        for f,f_uvs in vert_in_face.items():
            if len(f_uvs)!=4:
                return -1,-1
            else:
                c1 = cal_cos(self.uvs[f_uvs[0]][self.uv_layer].uv,self.uvs[f_uvs[1]][self.uv_layer].uv,self.uvs[f_uvs[2]][self.uv_layer].uv)
                c2 = cal_cos(self.uvs[f_uvs[1]][self.uv_layer].uv,self.uvs[f_uvs[2]][self.uv_layer].uv,self.uvs[f_uvs[3]][self.uv_layer].uv)
                cur_val = abs(c1)+abs(c2)
                if cur_val < best_value:
                    best_value = cur_val
                    best_index = f
        return best_index,best_value
                         
    def get_faces(self,uv_id):
        if uv_id in self.equal_loops:
            return [self.uvs[uv_id].face.index]+[x.face.index for x in self.equal_loops[uv_id]]
        else:
            return [self.uvs[uv_id].face.index]
          
    def order_face_verts(self,uv_indices):
        cur = uv_indices[0]
        new_indices = [cur]
        cur_set = set(uv_indices)
        while len(new_indices)<len(cur_set):
            adjs = self.graph[cur]
            cur = [y for y in adjs if y in cur_set and y not in new_indices][0]
            new_indices.append(cur)
        return new_indices
            
    def build_face_view(self,island):
        island = list(island)
        face_view = {}
        vert_in_face = {}
        uvs_groupby_face = group_by(island,key = lambda x:self.get_faces(x),value = lambda x:island[x])

        selected_faces = [(x,y) for x,y in uvs_groupby_face.items() if len(y)==len(self.bm.faces[x].loops)]
        selected_faces_indices = set([x[0] for x in selected_faces])
        for f_index,f_uvs in selected_faces:
            adjs = set([z for x in f_uvs
                        for y in self.graph[x]
                        for z in self.get_faces(y) if z in selected_faces_indices])
            adjs = [x for x in adjs if x in uvs_groupby_face and len(set(uvs_groupby_face[x]).intersection(set(f_uvs)))>=2]
            for x in adjs:
                if x == f_index:
                    continue
                if x not in face_view:
                    face_view[x] = set()
                if f_index not in face_view:
                    face_view[f_index] = set()
                face_view[x].add(f_index)
                face_view[f_index].add(x)
            vert_in_face[f_index] = self.order_face_verts(f_uvs)
        
            
        return face_view,vert_in_face

    def get_edges_uvs(self,uv_indices,bidir = True):
        uv_indices_set = set(uv_indices)      
        if bidir:
            return [(x,y) for x in uv_indices for y in self.graph[x] if y in uv_indices_set]
        else:
            cur = set()
            for x in uv_indices:
                for y in self.graph[x]:
                    if (x,y) not in cur and (y,x) not in cur and y in uv_indices_set:
                        cur.add((x,y))
            return list(cur)
    
    def get_faces_in_uvs(self,uv_indices):
        pass
       
    def scale_quad_to_geo(self,verts_in_the_quad,uv_geo_ratio = None):
        if len(verts_in_the_quad)!=4:
            raise Exception('must be a quad')
        geo_locs = [self.me.vertices[self.uvs[x].vert.index].co for x in verts_in_the_quad]
        uv_locs = [self.uvs[x][self.uv_layer].uv for x in verts_in_the_quad]
        geo_l1 = (geo_locs[1]-geo_locs[0]).length
        geo_l2 = (geo_locs[2]-geo_locs[1]).length
        geo_ratio = geo_l2/geo_l1
        uv_l1 = (uv_locs[1]-uv_locs[0]).length
        move_dir = (uv_locs[2]-uv_locs[1])       
        move_dir.normalize()
        move_by = move_dir*(uv_l1*geo_ratio)/2
        self.moveto_uv(verts_in_the_quad[3],uv_locs[0]+move_by)
        self.moveto_uv(verts_in_the_quad[2],uv_locs[1]+move_by)
        self.moveby_uv(verts_in_the_quad[0],-move_by)
        self.moveby_uv(verts_in_the_quad[1],-move_by)
        if uv_geo_ratio:
            scale = geo_l1*uv_geo_ratio/uv_l1
            co = mathutils.Vector([0,0])
            uv_locs = {x:self.uvs[x][self.uv_layer].uv for x in verts_in_the_quad}
            for _,uv_loc in uv_locs.items():
                co+=uv_loc
            co/=4
            for v in verts_in_the_quad:
                move_dir = uv_locs[v]-co
                length = move_dir.length*scale
                move_dir.normalize()
                self.moveto_uv(v,co+move_dir*length)
                
        
        return uv_l1/geo_l1
    
    def reorder_index_in_quad(self,verts,index0,index1):
        if len(verts)!=4:
            raise Exception('must be a quad')
        else:
            x = (index0+4-index1) % 4
            if x == 1:
                return [verts[(index0-i)%4] for i in range(4)]
            elif x == 3:
                return [verts[(index0+i)%4] for i in range(4)]
            else:
                raise Exception('something wrong')
        pass
    
    def get_face_co(self,verts):
        if len(verts)!=4:
            raise Exception('must be a quad')
        else:
            co = mathutils.Vector([0,0])
            for v in verts:
                co+=self.uvs[v][self.uv_layer].uv
            return co/len(verts)
            
    def scale_uvs(self,scale_x,scale_y,uv_indices,co = None):
        if not co :
            co = mathutils.Vector([0,0])
            for uv_index in uv_indices:
                co+=self.uvs[uv_index][self.uv_layer].uv
            co/=len(uv_indices)
        for uv_index in uv_indices:
            loc = self.uvs[uv_index][self.uv_layer].uv
            move_dir = loc-co
            vec = mathutils.Vector([move_dir.x*scale_x,move_dir.y*scale_y])
            self.moveto_uv(uv_index,co+vec)
        
    def uniform_all_shells(self,islands,ref_edges):
        assert len(islands) == len(ref_edges),'len(islands) and len(ref_edges) must be equal'
        geo_lens = [(self.me.vertices[self.uvs[v1].vert.index].co-self.me.vertices[self.uvs[v2].vert.index].co).length
                     for v1,v2 in ref_edges]
        uv_lens = [(self.uvs[v1][self.uv_layer].uv-self.uvs[v2][self.uv_layer].uv).length 
                   for v1,v2 in ref_edges]
        ratios = [uv_lens[i]/geo_lens[i] for i in range(len(islands))]
        avg_ratio = sum(ratios)/len(islands)
        #x = [avg_ratio/ratios[i] for i in range(len(islands))]
        for i in range(len(islands)):
            s = avg_ratio/ratios[i]
            self.scale_uvs(s,s,islands[i])

    def random_select_uv(self,groups,k,type):
        if type == 'vertex':
            to_be_select = [[random.sample(x,k)] for x in groups]
        elif type == 'edge':
            to_be_select = [random.sample(y,k) for x in groups for y in self.get_edges_uvs(x)]
        elif type == 'face':
            to_be_select = [random.sample(y,k) for x in groups for y in self.get_faces_in_uvs(x)]
        else:
            raise Exception('no such type')
        for x in to_be_select:
            for y in x:
                self.uvs[y][self.uv_layer].select = True
                
    def find_longest_edges(self,uv_indices):
        edges = self.get_edges_uvs(uv_indices)
        max_len = 0
        longest_edge = -1
        for e in edges:
            if e[0] == e[1]:
                continue
            length = (self.me.vertices[self.uvs[e[0]].vert.index].co - self.me.vertices[self.uvs[e[1]].vert.index].co).length
            if length>max_len:
                max_len = length
                longest_edge = e
        return longest_edge,max_len
    
    def find_best_projected_edge(self,uv_indices):
        values = {}
        for uv_index in uv_indices:
            value = self.cal_coplanar(self.uvs[uv_index].vert.index,[self.uvs[x].vert.index for x in self.graph[uv_index]])
            values[uv_index] = value
        edges = self.get_edges_uvs(uv_indices)
        best_value = float('inf')
        best_edge = None
        for e in edges:
            if e[0] == e[1]:
                continue
            length = (self.me.vertices[self.uvs[e[0]].vert.index].co - self.me.vertices[self.uvs[e[1]].vert.index].co).length
            value_edge = (values[e[0]]+values[e[1]])
            if value_edge < best_value:
                best_value = value_edge
                best_edge = e
                
        return best_edge,best_value
                
    def cal_coplanar_4_vert(self,verts):
        assert len(verts) == 4,'must be 4 verts'
        a = (self.me.vertices[self.uvs[verts[1]].vert.index].co-self.me.vertices[self.uvs[verts[0]].vert.index].co)
        a.normalize()
        b = (self.me.vertices[self.uvs[verts[1]].vert.index].co-self.me.vertices[self.uvs[verts[2]].vert.index].co)
        b.normalize()
        c = (self.me.vertices[self.uvs[verts[1]].vert.index].co-self.me.vertices[self.uvs[verts[3]].vert.index].co)
        c.normalize()       
        return abs(a.cross(b) @ c)
        
    def cal_coplanar(self,vert_index,adjs):
        if len(adjs)<=3:
            return 0
        value = 0
        for i in range(len(adjs)-2):
            value+=self.cal_coplanar_4_vert([i,i+1,i+2,vert_index])
        return value
              
    def deselect_all(self):
        for x in range(len(self.uvs)):
            self.set_select_uv(x,False)  
            
    def flow_quad(self,quad_index,island,face_view,vert_in_face,uv_geo_ratio = None):
        if len(vert_in_face[quad_index])!=4:
            raise Exception('input must be quad')
        else:
            fixed_verts = set(vert_in_face[quad_index])
            if quad_index not in face_view:
                return
            open_set = face_view[quad_index]
            close_set = set([quad_index])
            link = {x:quad_index for x in open_set}

            while len(open_set)>0:
                temp = set()
                for f in open_set:
                    cur_verts = vert_in_face[f]
                    if len(cur_verts)!= 4:
                        close_set.add(f)
                        continue
                    cur_verts_set = set(cur_verts)
                    not_fixed_verts = cur_verts_set.difference(fixed_verts)
                    cur_fixed = list(cur_verts_set-not_fixed_verts)
                    not_fixed_verts = list(not_fixed_verts)
                    if len(not_fixed_verts) == 2:
                        cur_verts = self.reorder_index_in_quad(cur_verts,
                                                              cur_verts.index(cur_fixed[0]),
                                                              cur_verts.index(cur_fixed[1]))
                        geo_locs = [self.me.vertices[self.uvs[x].vert.index].co for x in cur_verts]
                        uv_locs = [self.uvs[x][self.uv_layer].uv for x in cur_verts]
                        co = self.get_face_co(vert_in_face[link[f]])
                        move_dir = (uv_locs[1]+uv_locs[0])/2 - co
                        move_dir.normalize()
                        geo_l1 = (geo_locs[1]-geo_locs[0]).length
                        geo_l2 = (geo_locs[2]-geo_locs[1]).length
                        if uv_geo_ratio:
                            uv_l1 = geo_l1*uv_geo_ratio
                        else:
                            uv_l1 = (uv_locs[1]-uv_locs[0]).length
                        geo_ratio = geo_l2/geo_l1
                        move_by = move_dir*(uv_l1*geo_ratio)
                        self.moveto_uv(cur_verts[3],uv_locs[0]+move_by)
                        self.moveto_uv(cur_verts[2],uv_locs[1]+move_by)    
                        fixed_verts.update(not_fixed_verts)                     
                        
                    elif len(not_fixed_verts) == 1:
                        v_index = not_fixed_verts[0]
                        index_in_quad = cur_verts.index(v_index)
                        cur_verts = self.reorder_index_in_quad(cur_verts,index_in_quad,(index_in_quad+1)%4)                       
                        pos = [self.uvs[x][self.uv_layer].uv for x in cur_verts]
                        self.moveto_uv(v_index,pos[3]+pos[1]-pos[2])
                        fixed_verts.update(not_fixed_verts) 
                    elif len(not_fixed_verts) > 2:
                        raise Exception('some thing wrong')                    
                    close_set.add(f)
                    next_verts = face_view[f]
                    temp.update(next_verts)
                    link.update({x:f for x in next_verts})
                open_set = temp-close_set
                
    def __getitem__(self,key):
        return self.graph[key]
    
    
 
   

    
   
