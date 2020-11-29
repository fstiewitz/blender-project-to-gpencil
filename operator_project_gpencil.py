import bpy
import mathutils

bl_info = {
    "name": "Project to Grease Pencil",
    "description": "Project armature to grease pencil animation",
    "author": "Fabian Stiewitz",
    "version": (0, 1),
    "location": "View3D > Object > Project to Grease Pencil",
    "warning": "",
    "blender": (2, 91, 0),
    "category": "Object"
}


def get_armature_lines(armature):
    for bone in armature.pose.bones:
        yield bone.head, bone.tail

def main(context, projection, view_matrix):
    gpo = bpy.data.grease_pencils.new(name="Projected Frames")
    layer = gpo.layers.new(name="Layer", set_active=True)

    frame_save = context.scene.frame_current
    context.scene.frame_set(context.scene.frame_start)

    start_location = context.active_object.location.copy()
    plane_matrix = mathutils.Matrix(view_matrix)
    plane_matrix.translation = start_location
    plane_quat = plane_matrix.to_quaternion()

    for i in range(context.scene.frame_start, context.scene.frame_end + 1):
        context.scene.frame_set(i)
        frame = layer.frames.new(i, active=True)

        object_matrix = context.active_object.matrix_world

        for head, tail in get_armature_lines(context.active_object):
            phead = plane_matrix @ (object_matrix @ head)
            ptail = plane_matrix @ (object_matrix @ tail)

            if projection == 'projection_2D':
                phead.z = 0
                ptail.z = 0

            stroke = frame.strokes.new()
            stroke.line_width = 20
            stroke.points.add(2)
            stroke.points[0].co = phead
            stroke.points[1].co = ptail

    context.scene.frame_set(frame_save)

    obj = bpy.data.objects.new(name="Projected Frames", object_data=gpo)
    obj.location = start_location
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = plane_quat.inverted()
    context.scene.collection.objects.link(obj)

class ProjectGPencilOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.project_to_gpencil"
    bl_label = "Project to Grease Pencil"
    bl_options = {'REGISTER', 'UNDO'}

    projection: bpy.props.EnumProperty(items=[
        ("projection_3D", "3D", "Draw Grease Pencil Strokes over bones", 0),
        ("projection_2D", "2D", "Project Bones onto a 2D plane perpendicular to the viewport", 1)
    ], name="Projection Type")

    view_matrix: None

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        main(context, self.projection, self.view_matrix)
        return {'FINISHED'}

    def get_region(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D' and area.spaces.active:
                return area.spaces.active.region_3d
        return None

    def invoke(self, context, event):
        wm = context.window_manager
        region_data = self.get_region(context)
        if region_data is None:
            return None
        self.view_matrix = region_data.view_matrix
        return wm.invoke_props_dialog(self)


def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ProjectGPencilOperator.bl_idname)

def register():
    bpy.utils.register_class(ProjectGPencilOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(ProjectGPencilOperator)


if __name__ == "__main__":
    register()
