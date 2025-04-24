import FreeCAD, FreeCADGui
import os

ICONPATH = os.path.join(os.path.dirname(__file__), "resources")


class CopySupportAssignment():

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/spp.svg"),
            "Accel": "" ,
            "MenuText": "Copy assignment support",
            "ToolTip": "Copy assignment support to the rest"
        }

    def __init__(self):
        self.support_props = [
            "FixTranslationX", "FixTranslationY", "FixTranslationZ",
            "FixRotationX", "FixRotationY", "FixRotationZ",
            "ScaleDraw"
        ]

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) < 2:
            FreeCAD.Console.PrintError("Select source support first, then one or more target points.\n")
            return

        source = sel[0]
        targets = sel[1:]

        if not all(hasattr(source, p) for p in self.support_props):
            FreeCAD.Console.PrintError("First selected object must be a valid support.\n")
            return

        for target in targets:
            try:
                for prop in self.support_props:
                    if not hasattr(target, prop):
                        FreeCAD.Console.PrintMessage(f"Adding property {prop} to {target.Name}\n")
                        ptype = "App::PropertyBool" if "Fix" in prop else "App::PropertyFloat"
                        target.addProperty(ptype, prop, "CopiedSupport", f"Copied from {source.Name}")
                    setattr(target, prop, getattr(source, prop))
                FreeCAD.Console.PrintMessage(f"Support copied to {target.Name}\n")
            except Exception as e:
                FreeCAD.Console.PrintError(f"Failed to copy to {target.Name}: {e}\n")

        FreeCAD.ActiveDocument.recompute()
        
     
    def IsActive(self):
        return True
        




FreeCADGui.addCommand("Copysupport", CopySupportAssignment())

