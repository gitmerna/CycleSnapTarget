bl_info = {
    "name": "_ Z.Snap Target Switcher & Ctrl+Shift+Tab Disable",
    "author": "Yame",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Switch Snap Targets and optionally disable Ctrl+Shift+Tab snapping panel",
    "category": "3D View",
}

import bpy

# Snap Target のみ列挙
snap_targets = [
    ("GRID", "Grid", ""),
    ("VERTEX", "Vertex", ""),
    ("EDGE", "Edge", ""),
    ("FACE", "Face", ""),
]

# Scene プロパティ登録
def init_properties():
    for target, _, _ in snap_targets:
        setattr(bpy.types.Scene, f"snap_{target}", bpy.props.BoolProperty(name=target, default=True))

    # ✅ Snap切り替え時に自動でSnapを有効にするオプション
    bpy.types.Scene.snap_auto_enable = bpy.props.BoolProperty(
        name="切り替え時にSnapを有効にする",
        description="Snap Targetを切り替えると自動的にスナップをONにします",
        default=True
    )


def clear_properties():
    for target, _, _ in snap_targets:
        if hasattr(bpy.types.Scene, f"snap_{target}"):
            delattr(bpy.types.Scene, f"snap_{target}")

    if hasattr(bpy.types.Scene, "snap_auto_enable"):
        delattr(bpy.types.Scene, "snap_auto_enable")


# -----------------------------
# Snap Target 切り替えオペレーター
# -----------------------------
class SNAP_OT_next_target(bpy.types.Operator):
    bl_idname = "view3d.snap_next_target"
    bl_label = "Next Snap Target"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        tool = scene.tool_settings

        # 現在の Snap Target（セットから取得）
        if tool.snap_elements:
            current = next(iter(tool.snap_elements))
        else:
            current = None

        print("現在の Snap Target:", current)

        # チェックされた Snap Target
        checked_targets = [t[0] for t in snap_targets if getattr(scene, f"snap_{t[0]}", False)]
        if not checked_targets:
            self.report({"WARNING"}, "チェックされた Snap Target がありません")
            return {'CANCELLED'}

        # 次のターゲットを決定
        if current not in checked_targets:
            next_target = checked_targets[0]
        else:
            idx = checked_targets.index(current)
            next_target = checked_targets[(idx + 1) % len(checked_targets)]

        # 切り替え（set にして代入）
        tool.snap_elements = {next_target}  # set 型

        # ✅ Snap自動有効化がONならスナップをONにする
        if scene.snap_auto_enable:
            tool.use_snap = True
            print("Snapを有効にしました")

        self.report({"INFO"}, f"Snap Target を {next_target} に変更")
        return {'FINISHED'}


# -----------------------------
# Ctrl+Shift+Tab 無効化オペレーター
# -----------------------------
class SNAP_OT_disable_ctrlshift_tab(bpy.types.Operator):
    bl_idname = "snap.disable_ctrlshift_tab"
    bl_label = "Disable Ctrl+Shift+Tab (VIEW3D_PT_snapping)"

    def execute(self, context):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user  # ユーザー設定

        print("=== Ctrl+Shift+Tab（VIEW3D_PT_snapping）割り当て確認 ===")

        found = False
        for km in kc.keymaps:
            for kmi in km.keymap_items:
                if (kmi.type == 'TAB' and kmi.ctrl and kmi.shift and not kmi.alt):
                    props = {}
                    if hasattr(kmi, "properties") and kmi.properties:
                        props = {k: getattr(kmi.properties, k) for k in kmi.properties.keys()}
                    if props.get("name") == "VIEW3D_PT_snapping":
                        found = True
                        print(f"無効化: {km.name} - {kmi.idname}")
                        kmi.active = False

        if not found:
            print("Ctrl+Shift+Tab に 'VIEW3D_PT_snapping' の割り当ては見つかりませんでした。")

        # ------------------------------------------------------------
        # Ctrl+Shift+Tab に「Snap Next Target」を再登録
        # ------------------------------------------------------------
        km = kc.keymaps.get("3D View", None)
        if km:
            # すでに登録済みなら重複を避けて削除
            for kmi in list(km.keymap_items):
                if (kmi.idname == "view3d.snap_next_target" and
                    kmi.type == 'TAB' and kmi.ctrl and kmi.shift and not kmi.alt):
                    km.keymap_items.remove(kmi)

            # 新しく登録
            kmi = km.keymap_items.new("view3d.snap_next_target", 'TAB', 'PRESS', ctrl=True, shift=True)
            print("Ctrl+Shift+Tab に view3d.snap_next_target を登録しました。")
        else:
            print("⚠ 3D View キーマップが見つかりませんでした。")

        self.report({"INFO"}, "Ctrl+Shift+Tab に Snap Next Target を登録しました")
        return {'FINISHED'}


# -----------------------------
# UI パネル
# -----------------------------
class SNAP_PT_panel(bpy.types.Panel):
    bl_label = "Snap Target Switcher"
    bl_idname = "SNAP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="切り替えする対象")

        # Snap Target チェックボックス
        for target, label, _ in snap_targets:
            box.prop(scene, f"snap_{target}", text=label)
            
        layout.separator()
        layout.operator("view3d.snap_next_target", text="Next Snap Target")

        layout.separator()
        layout.operator("snap.disable_ctrlshift_tab", text="Disable Ctrl+Shift+Tab (Snapping)")

        layout.separator()
        # ✅ 新オプション（スナップ自動ON設定）
        layout.prop(scene, "snap_auto_enable")


# -----------------------------
# 登録 / 解除
# -----------------------------
classes = [SNAP_OT_next_target, SNAP_OT_disable_ctrlshift_tab, SNAP_PT_panel]

def register():
    init_properties()
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    clear_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
