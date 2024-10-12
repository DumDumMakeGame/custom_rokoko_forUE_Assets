import bpy

from .main import ToolPanel
from ..operators import retargeting, detector
from ..core.icon_manager import Icons
from ..core.retargeting import get_target_armature, get_source_armature

from bpy.types import PropertyGroup, UIList
from bpy.props import StringProperty, BoolProperty

bpy.types.Object.dumdum_selected_source = bpy.props.BoolProperty(name = "dumdum_selected_source", default=False)
bpy.types.Scene.armature_index = bpy.props.IntProperty(name = "armature_index", default=0)

# UIList to draw valid actions using template_list
class DDSS_UL_ArmatureUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align = True)
        row.prop(item, "dumdum_selected_source", text = "")
        row.prop(item, "name", text="", emboss = False)
    
    def filter_items(self, context, data, propname):
        # Default return values.
        flt_flags = []
        flt_neworder = []
        
        # Get list of all items
        items = getattr(data, propname)
        
        #Initialize filter flags
        flt_flags = [self.bitflag_filter_item] * len(items)
        
        i = 0
        
        # Do not display actions that don't have clear animation data (pose.bones)
        while i < len(items):
            displayItem = items[i].type == "ARMATURE"
            
            if not displayItem: flt_flags[i] &= ~self.bitflag_filter_item
            i += 1
        
        return flt_flags, flt_neworder

# Retargeting panel
class RetargetingPanel(ToolPanel, bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_rsl_retargeting_v2'
    bl_label = 'Retargeting'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        row = layout.row(align=True)
        row.label(text='Select the armatures:')

        row = layout.row(align=True)
        row.label(text="Source:")
        #row.prop(context.scene, 'rsl_retargeting_armature_source', icon='ARMATURE_DATA')
        
        row = layout.row()
        row.template_list(listtype_name = "DDSS_UL_ArmatureUIList", 
                          list_id = "The_List", 
                          dataptr = bpy.data, 
                          propname = "objects", 
                          active_dataptr = bpy.context.scene, 
                          active_propname = "armature_index",
                          rows = 3)
                          
        row = layout.row(align=True)
        row.prop(context.scene, 'rsl_retargeting_armature_target', icon='ARMATURE_DATA')

        anim_exists = False
        for obj in bpy.data.objects:
            if obj.animation_data and obj.animation_data.action:
                anim_exists = True

        if not anim_exists:
            row = layout.row(align=True)
            row.label(text='No animated armature found!', icon='INFO')
            return
        
        any_sources_selected = False
        for obj in bpy.data.objects:
            if obj.type == "ARMATURE" and obj.dumdum_selected_source:
                any_sources_selected = True

        if not any_sources_selected or not context.scene.rsl_retargeting_armature_target:
            self.draw_import_export(layout)
            return

        if not context.scene.rsl_retargeting_bone_list:
            row = layout.row(align=True)
            row.scale_y = 1.2
            row.operator(retargeting.BuildBoneList.bl_idname, icon_value=Icons.CALIBRATE.get_icon())
            self.draw_import_export(layout)
            return

        subrow = layout.row(align=True)
        row = subrow.row(align=True)
        row.scale_y = 1.2
        row.operator(retargeting.BuildBoneList.bl_idname, text='Rebuild Bone List', icon_value=Icons.CALIBRATE.get_icon())
        row = subrow.row(align=True)
        row.scale_y = 1.2
        row.alignment = 'RIGHT'
        row.operator(retargeting.ClearBoneList.bl_idname, text="", icon='X')

        layout.separator()

        row = layout.row(align=True)
        row.template_list("RSL_UL_BoneList", "Bone List", context.scene, "rsl_retargeting_bone_list", context.scene, "rsl_retargeting_bone_list_index", rows=1, maxrows=10)

        row = layout.row(align=True)
        row.operator(retargeting.AddBoneListItem.bl_idname, text="Add Custom Entry", icon='ADD')

        row = layout.row(align=True)
        row.prop(context.scene, 'rsl_retargeting_auto_scaling')

        row = layout.row(align=True)
        row.label(text='Use Pose:')
        row.prop(context.scene, 'rsl_retargeting_use_pose', expand=True)

        row = layout.row(align=True)
        row.scale_y = 1.4
        row.operator(retargeting.RetargetAnimations.bl_idname, icon_value=Icons.CALIBRATE.get_icon())

        self.draw_import_export(layout)

    def draw_import_export(self, layout):
        layout.separator()

        row = layout.row(align=True)
        row.label(text='Custom Naming Schemes:')

        subrow = layout.row(align=True)
        row = subrow.row(align=True)
        row.scale_y = 0.9
        row.operator(detector.SaveCustomBonesRetargeting.bl_idname, text='Save')
        row.operator(detector.ImportCustomBones.bl_idname, text='Import')
        row.operator(detector.ExportCustomBones.bl_idname, text='Export')
        row = subrow.row(align=True)
        row.scale_y = 0.9
        row.alignment = 'RIGHT'
        row.operator(detector.ClearCustomBones.bl_idname, text='', icon='X')


class BoneListItem(PropertyGroup):
    """Properties of the bone list items"""
    bone_name_source: StringProperty(
        name="Source Bone",
        description="The source bone name",
        default="")

    bone_name_target: StringProperty(
        name="Target Bone",
        description="The target bone name",
        default="")

    bone_name_key: StringProperty(
        name="Auto Detection Key",
        description="The automatically detected bone key",
        default="")

    is_custom: BoolProperty(
        description="This determines if the field is a custom one source bone one",
        default=False)


class RSL_UL_BoneList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        armature_target = get_target_armature()
        armature_source = get_source_armature()

        layout = layout.split(factor=0.36, align=True)

        # Displays source bone
        if item.is_custom:
            layout.prop_search(item, 'bone_name_source', armature_source.pose, "bones", text='')
        else:
            layout.label(text=item.bone_name_source)

        # Displays target bone
        if armature_target:
            layout.prop_search(item, 'bone_name_target', armature_target.pose, "bones", text='')
