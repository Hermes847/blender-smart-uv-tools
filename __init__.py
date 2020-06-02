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
    "name" : "Smart UV Tools",
    "author" : "Li GuangYuan",
    "description" : "",
    "blender" : (2, 80, 0),   
    "version" : (0, 0, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "Generic"
}



import bpy
from . import my_ops
from . import my_panel
import inspect

classes = []
for name, obj in inspect.getmembers(my_ops):
    if inspect.isclass(obj) and issubclass(obj,bpy.types.Operator):
        classes.append(obj)
    
for name, obj in inspect.getmembers(my_panel):
    if inspect.isclass(obj) and issubclass(obj,bpy.types.Panel):
        classes.append(obj)

register,unregister = bpy.utils.register_classes_factory(classes)
