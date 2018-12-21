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
    "category": "Mesh",
    }

## KILLER CLEANER

import bpy
from bpy import context
import bmesh
import math
from math import pi
from bpy.props import *
from mathutils import Matrix
from statistics import mean

## FUNCTION to apply_scale on object and children
def apply_scale(ob):    
#    mat = Matrix()
#    mat[0][0], mat[1][1], mat[2][2] = ob.matrix_world.to_scale()
#    ob.data.transform(mat)
#    ob.matrix_world = ob.matrix_world.normalized()
#    ob.scale = [1,1,1]
    ob.select = True
    bpy.ops.object.transform_apply(scale = True)
    ob.select = False


## DECLARE
myModifierList = []
myList = []



## MENU text and icon
# icon --- description --- name
my_bool = {'remove_doubles':["LATTICE_DATA","Remove duplicate doubles", "Remove Doubles"],
             'tris_to_quad':["OUTLINER_OB_LATTICE","Join triangle into quad", "Tris to Quad"],
             'recalculate_normals':["FACESEL","Recalculate outside", "Recalculate"],
             'clear_custom_normal':["UV_FACESEL","Remove the custom split normals layer, if it exists", "Clear Customs"],
             'remove_all_modifiers':["MODIFIER","Remove all modifiers", "Remove All"],
             'remove_hidden_modifiers':["MODIFIER","Remove hidden modifiers", "Remove Hidden"],
             'remove_unrendered_modifiers':["MODIFIER","Remove unrendered modifiers", "Remove Unrendered"],
             #'apply_modifiers':"MODIFIER",
             'double_sided':["MOD_BEVEL","Display the mesh with double sided lighting (OpenGL only)", "Double Sided"],
             'apply_scale':["NDOF_TRANS","Apply the object's transformation to its data", "Apply Scale"],
             'autosmooth':["SURFACE_NCIRCLE","Auto smooth", "Auto Smooth"],
             'remove_material':["MATERIAL_DATA","Remove material", "Remove Materials"],
             'rename_objects':["FONT_DATA", "Rename objects with 'GEO' + the Scene name", "Rename"],
             'make_single_user':["OUTLINER_OB_GROUP_INSTANCE","Make link data local", "Single User"]}

## CLASS KillerCleanerSettings
class KillerCleanerSettings(bpy.types.PropertyGroup):
    polycount_before = bpy.props.IntProperty()
    polycount_after = bpy.props.IntProperty()
    lenModifierList = bpy.props.IntProperty()
    custom_rename = bpy.props.BoolProperty(name="Custom Rename", default=False)
    temp_ob_rename = bpy.props.StringProperty(name="Rename in", default="GEO_")
    temp_mesh_rename = bpy.props.StringProperty(name="Rename in", default="GEO_DATA_")    

for i in my_bool:
    setattr(KillerCleanerSettings,i,bpy.props.BoolProperty(name=my_bool[i][2], description=my_bool[i][1].replace('_',' '), default =False))

## CLASS to show menu
class DialogOperator(bpy.types.Operator):

    bl_idname = "object.dialog_operator"
    bl_label = "Clean selected objects"
               
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
        list_selected=[]
                        
        ## PROGRESS BAR
        wm = bpy.context.window_manager
        tot = len(bpy.context.selected_objects)
        print("Killer Cleaner --- " + str(tot) + " Objects selected ")
        wm.progress_begin(0, tot)
        
        ## GET LIST OF SELECTED OBJECTS
        for ob in bpy.context.selected_objects:
            list_selected.append(ob)
            ob.select= False
        bpy.ops.object.select_all(action='DESELECT')

        ## START
        
        wm = context.window_manager
        settings = context.scene.killer_cleaner_settings
        settings.polycount_before = 0
        settings.polycount_after = 0
                
        for index,ob in enumerate(list_selected) :
            if ob.type == 'MESH':
                settings.polycount_before+=len(ob.data.polygons)
        
        ## DELETE ALL NAMES
        if settings.rename_objects == True:
            for ob in bpy.context.selected_objects:
                ob.name=""
        
        ## FOR IN SELECTED OBJECTS
        for index,ob in enumerate(list_selected) :
            
            ## PRINT PROGRESS IN CONSOLE
            print("Killer Cleaner --- Object "+str(index+1)+"/"+str(tot))
            
            ## PROGRESS BAR
            wm.progress_update(index/100)
            
            ## IF GROUP
            if ob.type == 'EMPTY':
                continue
            if ob.type == 'CAMERA':
                continue
            
            ## RENAME OBJECT AND MESH
            if settings.rename_objects == True:
                ind = str(index).zfill(3)
                if settings.custom_rename == False :
                    ob.name = "GEO_"+decor+"_"+ str(ind)
                    ob.data.name = "GEO_DATA_"+decor+"_"+ str(ind)
                else:
                    ob.name = settings.temp_ob_rename + str(ind)
                    ob.data.name = settings.temp_mesh_rename + str(ind)
            
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
                    bmesh.ops.join_triangles(bm, faces = bm.faces,angle_face_threshold = math.radians(40),angle_shape_threshold =math.radians(40))
                
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
                if settings.make_single_user == True:
                    ob.data = ob.data.copy()
                    
                ## REMOVE MODIFIERS
                if settings.remove_all_modifiers or settings.remove_hidden_modifiers or settings.remove_unrendered_modifiers :
                    if ob.modifiers:
                        for mo in ob.modifiers:
                            if settings.remove_all_modifiers:
                                ob.modifiers.remove(mo)
                            else:
                                if settings.remove_hidden_modifiers:
                                    if mo.show_viewport==False :
                                        ob.modifiers.remove(mo)
                                if settings.remove_unrendered_modifiers:
                                    if mo.show_render==False :
                                        ob.modifiers.remove(mo)
                
                ## APPLY SCALE
                if settings.apply_scale == True:
                    if ob.modifiers:
                        
                        if not(ob.scale[0] == 1 and ob.scale[1] == 1 and ob.scale[2] == 1):
                            # APPLY SCALE IF MODIFIER ARRAY
                            for mo in ob.modifiers:
                                mod_array = False
                                if mo.type == 'ARRAY':
                                    if ob.scale.x < 0 or ob.scale.y < 0 or ob.scale.z < 0:
                                        myModifierList.append(ob.name)
                                        settings.lenModifierList +=1
                                        mod_array = True
                                        print (mod_array)
                                        break
                                    else:
                                        apply_scale(ob)
                            for mo in ob.modifiers:                                   
                                ## APPLY SCALE IF MODIFIER BEVEL   
                                if mo.type == 'BEVEL' and mod_array == False:
                                    print('Bevel modifier detected')
                                    old_bevel = mo.width
                                    new_bevel = old_bevel * ((abs(ob.scale[0])+abs(ob.scale[1])+abs(ob.scale[2]))/3)
                                    mo.width = new_bevel
                                    apply_scale (ob)

                                ## APPLY SCALE IF MODIFIER SOLIDIFY                       
                                if mo.type == 'SOLIDIFY' and mod_array == False:
                                    print('Bevel modifier detected')
                                    old_solidify = mo.thickness
                                    new_solidify = old_solidify * mean(ob.scale)
                                    mo.thickness = new_solidify
                                    apply_scale (ob)

                                # APPLY SCALE IF MODIFIER SUBSURF
                                if mo.type == 'SUBSURF' and mod_array == False:
                                    apply_scale (ob)
                                
                                elif mod_array == False:
                                    apply_scale(ob)      
                                                        
                    ## IF PARENT AND CHILDREN        
                    else:
                        if ob.children:
                            list_children = []
                            for child in ob.children:
                                list_children.append([child,child.matrix_world])                          
                            for child in ob.children:                                    
                                if child.modifiers:
                                    print('on passe notre tour')
                                    myModifierList.append(ob.name)
                                    settings.lenModifierList +=1
                                    pass
                                else:                                      
                                    apply_scale(ob)
                                    
                                
                                    for c in list_children:
                                        c[0].matrix_world = c[1]
                                        apply_scale(c[0])
                                                 
                        else:
                            apply_scale(ob)
                                                          
                ## AUTO SMOOTH
                if settings.autosmooth == True:
                    if ob.type == 'MESH':
                        ob.data.use_auto_smooth = True
                        ob.data.auto_smooth_angle = math.radians(30)
                        for poly in ob.data.polygons:
                            poly.use_smooth = True
                
                ## DOUBLE SIDED
                if settings.double_sided == True:
                    if ob.type == 'MESH':
                        ob.data.show_double_sided = True

                ## REMOVE MATERIALS
                if settings.remove_material == True:
                    if ob.type == 'MESH':
                        ob.data.materials.clear(True)
               
                ## PRINT NAME AND POLYCOUNT len(object.data.vertices)
                #print (index, "/", len(bpy.context.selected_objects))
                if ob.type == 'MESH' and ob.type !='CAMERA':
                    myList.append((ob.name, len(ob.data.polygons)))

        ## PRINT LIST
        #for item in sorted(myList, key=lambda a : a[1], reverse=False):
        #    print (item)
        for index,ob in enumerate(list_selected) :
            if ob.type == 'MESH':
                settings.polycount_after+=len(ob.data.polygons)
            
#        bpy.ops.object.select_all(action='TOGGLE')

        ## SELECT OBJECTS WITH MODIFIER
#        for ob in bpy.data.objects:
#            ob.select = False
#        
#        for modifiers in myModifierList:
#            #print(settings.lenModifierList)
#            bpy.data.objects[modifiers].select=True

        ## RESELECT OBJECTS
        for ob in list_selected :
            ob.select = True

        ## END PROGRESS BAR
        wm.progress_end()      
        self.report({'INFO'}, "FINISHED!")
        bpy.ops.object.dialog_operator2('INVOKE_DEFAULT')
        return {'FINISHED'}


#    def invoke(self, context, event):
#        wm = context.window_manager
#        settings = context.scene.killer_cleaner_settings
#        settings.polycount_before = 0
#        settings.polycount_after = 0
#                
#        for index,ob in enumerate(bpy.context.selected_objects) :
#            if ob.type == 'MESH':
#                settings.polycount_before+=len(ob.data.polygons)
#        return wm.invoke_props_dialog(self)


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
        layout.label(text="%s face(s) removed"%(polycount_before-polycount_after), icon='SOLO_ON')

        if settings.apply_scale == True:
            if settings.lenModifierList>0:
                layout.label(text="%01d" % settings.lenModifierList +" object(s) selected : scale not applied" , icon="OUTLINER_OB_LAMP")
                #layout.label(text="%01d Objects with modifiers selected" % settings.lenModifierList, icon='VISIBLE_IPO_ON')
                    
    def execute(self, context):
        settings = context.scene.killer_cleaner_settings
        if settings.lenModifierList>0:
            self.report({'INFO'}, "Object(s) selected : scale not applied")        
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
    bl_category = "Tools"
    
    def draw(self, context):
        bl_idname = "object.dialog_operator"
        bl_label = "Killer Cleaner"
    
    def draw(self,context):
        
        ## PANEL        
        layout = self.layout
        settings = context.scene.killer_cleaner_settings
        
        bigcol = layout.column(align=False)
        
        ## OBJECT
        box2 = bigcol.box()
        box2.label("Object", icon="OBJECT_DATAMODE")
        col = box2.column(align=True)
        col.prop(settings, 'make_single_user', icon='OUTLINER_OB_GROUP_INSTANCE')
        col.prop(settings, 'rename_objects', icon='FONT_DATA')
        if settings.rename_objects:
            col.prop(settings, "custom_rename", icon='SORTALPHA')
            if settings.custom_rename:
                col.prop(settings, "temp_ob_rename", text='', icon='OBJECT_DATAMODE')
                col.prop(settings, "temp_mesh_rename", text='', icon='OUTLINER_DATA_MESH')

        ## SHADING
        box2 = bigcol.box()
        box2.label("Shading", icon="MATERIAL")
        col = box2.column(align=True)
        col.prop(settings, 'remove_material', icon='MATERIAL_DATA')
        col.prop(settings, 'double_sided', icon='MOD_BEVEL')
        col.prop(settings, 'autosmooth', icon='SURFACE_NCIRCLE')

        ## MESH
        box2 = bigcol.box()
        box2.label("Mesh", icon="OUTLINER_DATA_MESH")
        col = box2.column(align=True)
        col.prop(settings, 'remove_doubles', icon='LATTICE_DATA')
        col.prop(settings, 'tris_to_quad', icon='OUTLINER_OB_LATTICE')
        col.prop(settings, 'apply_scale', icon='NDOF_TRANS')

        ## NORMALS
        box2 = bigcol.box()
        box2.label("Normals", icon="SNAP_NORMAL")
        col = box2.column(align=True)
        col.prop(settings, 'clear_custom_normal', icon='UV_FACESEL')
        col.prop(settings, 'recalculate_normals', icon='FACESEL')

        ## MODIFIERS
        box2 = bigcol.box()
        box2.label("Modifiers", icon="MODIFIER")
        col = box2.column(align=True)
        col.prop(settings, 'remove_all_modifiers', icon='MODIFIER')
        col.prop(settings, 'remove_hidden_modifiers', icon='RESTRICT_VIEW_OFF')
        col.prop(settings, 'remove_unrendered_modifiers', icon='RESTRICT_RENDER_OFF')

        layout.operator("object.dialog_operator", icon = "FILE_TICK") #Create button Assign

### Register / Unregister ###       
def register():
     ## REGISTER    
    bpy.utils.register_class(KillerCleanerSettings)
    bpy.utils.register_class(DialogOperator)
    bpy.utils.register_class(DialogOperator2)
    bpy.utils.register_class(CleanerPanel)

    bpy.types.Scene.killer_cleaner_settings = bpy.props.PointerProperty(type = KillerCleanerSettings)

def unregister():
    ## UNREGISTER
    bpy.utils.unregister_class(KillerCleanerSettings)
    bpy.utils.unregister_class(CleanerPanel)
    bpy.utils.unregister_class(DialogOperator)
    bpy.utils.unregister_class(DialogOperator2)

    del bpy.types.Scene.killer_cleaner_settings

if __name__ == "__main__":
    register()
