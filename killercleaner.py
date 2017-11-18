### This addon allows you to clean your scene ###
### remove doubles, recalculate normals, rename objects...###

bl_info = {
    "name": "Killer Cleaner",
    "author": "dono",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "description": "Clean objects of your scene",
    "location": "View3D > Tool Shelf > Killer Cleaner",
    "warning": "",
    "wiki_url": "",
    "category": "User",
    }

## KILLER CLEANER

import bpy
from bpy import context
import bmesh
import math
from math import pi
from bpy.props import *
from mathutils import Matrix

## DECLARE

myModifierList = []
myList = []


## MENU text and icon
my_bool = {'remove_doubles':["LATTICE_DATA","Remove duplicate doubles"],
             'tris_to_quad':["OUTLINER_OB_LATTICE","Join triangle into quad"],
             'recalculate_normals':["FACESEL","Recalculate outside"],
             'clear_custom_normal':["UV_FACESEL","Remove the custom split normals layer, if it exists"],
             #'apply_modifiers':"MODIFIER",
             'double_sided':["MOD_BEVEL","Display the mesh with double sided lighting (OpenGL only)"],
             'apply_scale':["NDOF_TRANS","Apply the object's transformation to its data"],
             'autosmooth':["SURFACE_NCIRCLE","Auto smooth"],
             'remove_material':["MATERIAL_DATA","Remove material"],
             'rename_objects':["FONT_DATA", "Rename objects with 'GEO' + the Scene name"],
             'make_single_user':["OUTLINER_OB_GROUP_INSTANCE","Make link data local"]}

## CLASS KillerCleanerSettings
class KillerCleanerSettings(bpy.types.PropertyGroup):
    polycount_before = bpy.props.IntProperty()
    polycount_after = bpy.props.IntProperty()
    lenModifierList = bpy.props.IntProperty()
    

for i in my_bool:
    setattr(KillerCleanerSettings,i,bpy.props.BoolProperty(name=i.replace('_',' ').title(), description=my_bool[i][1].replace('_',' '), default =True))

## CLASS to show menu
class DialogOperator(bpy.types.Operator):

    bl_idname = "object.dialog_operator"
    bl_label = "KILLER CLEANER"
    
    def draw(self,context):
        
        ## PANEL        
        layout = self.layout
        settings = context.scene.killer_cleaner_settings
        
        
        row=layout.row()
        row=layout.row()
        row=layout.row()
        
        for prop,icon in my_bool.items():
            layout.prop(settings, prop, icon=icon[0])
            row=layout.row()
            layout.row()
            #row.label(icon=icon)
            #row.prop(settings, prop)
            
        row=layout.row()
        row=layout.row()
        row=layout.row()
        row=layout.row()
        row=layout.row()
                       
    ## EXECUTE
    def execute(self, context):
        
        ## DECLARE
        scene = context.scene
        decor = scene.name
        override = bpy.context.copy()
        myList = []
        myModifierList = []
        settings = scene.killer_cleaner_settings
        settings.lenModifierList = 0
                
        ## PROGRESS BAR
        wm = bpy.context.window_manager
        tot = len(bpy.context.selected_objects)
        wm.progress_begin(0, tot)

        ## START
        
        ## DELETE ALL NAMES
        if settings.rename_objects == True:
            for ob in bpy.context.selected_objects:
                ob.name=""
        
        ## FOR IN SELECTED OBJECTS
        for index,ob in enumerate(bpy.context.selected_objects) :

            ## PROGRESS BAR
            wm.progress_update(index/100)
            
            ## IF GROUP
            if ob.type == 'EMPTY':
                continue
            
            ## RENAME OBJECT AND MESH
            if settings.rename_objects == True:
                ind = str(index).zfill(3)
                ob.name = "GEO_"+decor+"_"+ str(ind)
                ob.data.name = "GEO_DATA_"+decor+"_"+ str(ind)
            
            ## IF MESH
            if ob.type == 'MESH':
                override = context.copy()
                override['object'] = ob
                override['active_object'] = ob
                new_mesh = ob.data
                
#                ## APPLY MODIFIERS
#                old_mesh = ob.data
#                new_mesh = ob.to_mesh (scene, True, 'PREVIEW')
#                ob.modifiers.clear()
#                ob.data = new_mesh
                
                ## ENTER BMESH
                bm = bmesh.new()
                bm.from_mesh(new_mesh)

                ## REMOVE DOUBLES
                if settings.remove_doubles == True:
                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0)
                
                ## TRIS TO QUADS
                if settings.tris_to_quad == True:
                    bmesh.ops.join_triangles(bm, faces = bm.faces,angle_face_threshold = pi,angle_shape_threshold =pi)
                
                ## RECALCULATE NORMALS
                if settings.recalculate_normals == True:
                    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                
                ## QUIT BMESH
                bm.to_mesh(new_mesh)
                new_mesh.update()
                bm.clear()
                    
                ## CLEAR CUSTOM SPLIT NORMALS
                if settings.clear_custom_normal == True:
                    bpy.ops.mesh.customdata_custom_splitnormals_clear(override)
                
                ## MAKE SINGLE USER OBJECT DATA
                #if ob.data.users>1:
                
                if settings.make_single_user == True:
                    ob.data = ob.data.copy()
                
                ## APPLY SCALE (if no modifier)
                if settings.apply_scale == True:
                    if ob.modifiers:
                        myModifierList.append(ob.name)
                        settings.lenModifierList +=1
                    else:
                        mat = Matrix()
                        mat[0][0], mat[1][1], mat[2][2] = ob.matrix_world.to_scale()
                        ob.data.transform(mat)
                        ob.matrix_world = ob.matrix_world.normalized()                           
                        
                ## AUTO SMOOTH
                if settings.autosmooth == True:
                    ob.data.use_auto_smooth = True
                    ob.data.auto_smooth_angle = math.radians(30)
                    for poly in bpy.context.object.data.polygons:
                        poly.use_smooth = True
                
                ## DOUBLE SIDED
                if settings.double_sided == True:
                    ob.data.show_double_sided = True

                ## REMOVE MATERIALS
                if settings.remove_material == True:
                    ob.data.materials.clear(True)
               
                ## PRINT NAME AND POLYCOUNT len(object.data.vertices)
                #print (index, "/", len(bpy.context.selected_objects))
                myList.append((ob.name, len(ob.data.polygons)))

        ## PRINT LIST
        #for item in sorted(myList, key=lambda a : a[1], reverse=False):
        #    print (item)
        for index,ob in enumerate(bpy.context.selected_objects) :
            if ob.type == 'MESH':
                settings.polycount_after+=len(ob.data.polygons)
            
#        bpy.ops.object.select_all(action='TOGGLE')

        ## SELECT OBJECTS WITH MODIFIER
        for ob in bpy.data.objects:
            ob.select = False
        
        for modifiers in myModifierList:
            #print(settings.lenModifierList)
            bpy.data.objects[modifiers].select=True

        ## END PROGRESS BAR
        wm.progress_end()      
        self.report({'INFO'}, "FINISHED!")
        bpy.ops.object.dialog_operator2('INVOKE_DEFAULT')
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        settings = context.scene.killer_cleaner_settings
        settings.polycount_before = 0
        settings.polycount_after = 0
                
        for index,ob in enumerate(bpy.context.selected_objects) :
            if ob.type == 'MESH':
                settings.polycount_before+=len(ob.data.polygons)
        return wm.invoke_props_dialog(self)

## CLASS to show results
class DialogOperator2(bpy.types.Operator):

    bl_idname = "object.dialog_operator2"
    bl_label = "FINISHED !"
            
    def draw(self,context):
        settings = context.scene.killer_cleaner_settings
        polycount_before = settings.polycount_before
        polycount_after = settings.polycount_after
        
        layout = self.layout        
        row = layout.row()
        layout.label(text="Killer Cleaner has removed %s faces"%(polycount_before-polycount_after), icon='SOLO_ON')
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.row()
        if settings.apply_scale == True:
            if settings.lenModifierList>0:
                layout.label(text="Scale not applied on %01d" % settings.lenModifierList +" objects" , icon="OUTLINER_OB_LAMP")
                layout.label(text="These objects with modifiers have been selected", icon='VISIBLE_IPO_ON')
                    
    def execute(self, context):
        self.report({'INFO'}, "OBJECTS WITH MODIFIERS SELECTED !")        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager        
        return wm.invoke_props_dialog(self) #(self, width=400, height=400)

### Panel Killer Cleaner launch ###
class CleanerPanel(bpy.types.Panel):

    bl_idname = "override"
    bl_label = "Killer Cleaner"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Killer CLeaner"
    
    def draw(self, context):
        layout = self.layout
        layout = self.layout
        layout.operator("object.dialog_operator", icon = "SOLO_ON") #Create button Assign

        layout = self.layout
        

### Register / Unregister ###       
def register():
      
    ## REGISTER    
    bpy.utils.register_class(KillerCleanerSettings)
    bpy.utils.register_class(DialogOperator)
    bpy.utils.register_class(DialogOperator2)
    bpy.types.Scene.killer_cleaner_settings = bpy.props.PointerProperty(type = KillerCleanerSettings)
    bpy.utils.register_class(CleanerPanel)

def unregister():
    bpy.utils.unregister_class(CleanerPanel)

if __name__ == "__main__":
    register()
    

# call test
#bpy.ops.object.dialog_operator('INVOKE_DEFAULT')

