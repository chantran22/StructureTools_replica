import FreeCAD, FreeCADGui
import os

ICONPATH = os.path.join(os.path.dirname(__file__), "resources")

class CommandCopyMemberProps():
    """Copy member properties (Material, Section, Rotation) from one member to others"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/mss.svg"),
            "Accel": "",
            "MenuText": "Copy Member Properties",
            "ToolTip": "Copies material, section, and rotation from the first selected member to the rest"
        }

    def Activated(self):
        selections = FreeCADGui.Selection.getSelection()
        if len(selections) < 2:
            FreeCAD.Console.PrintError("Select at least two objects: source first, then targets.\n")
            return

        source = selections[0]
        targets = selections[1:]

        # Check if source has required properties
        if not all(hasattr(source, p) for p in ["MaterialMember", "SectionMember", "RotationSection"]):
            FreeCAD.Console.PrintError("Source object does not have required member properties.\n")
            return

        for obj in targets:
            try:
                if not hasattr(obj, "MaterialMember"):
                    obj.addProperty('App::PropertyLink', 'MaterialMember', 'Structure','Member material')
                if not hasattr(obj, "SectionMember"):
                    obj.addProperty('App::PropertyLink', 'SectionMember', 'Structure','Member section')
                if not hasattr(obj, "RotationSection"):
                    obj.addProperty('App::PropertyAngle', 'RotationSection', 'Structure','Member section rotation')
                if not hasattr(obj, "TrussMember"):
                    obj.addProperty('App::PropertyBool', 'TrussMember', 'Structure','Define como membro de treli\u00e7a')

                obj.MaterialMember = source.MaterialMember
                obj.SectionMember = source.SectionMember
                obj.RotationSection = source.RotationSection
                obj.TrussMember = source.TrussMember
                FreeCAD.Console.PrintMessage(f"Copied to {obj.Name}\n")

            except Exception as e:
                FreeCAD.Console.PrintError(f"Failed to copy to {obj.Name}: {e}\n")

        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return True


FreeCADGui.addCommand("Copymemberprops", CommandCopyMemberProps())