import FreeCAD, FreeCADGui
import os

ICONPATH = os.path.join(os.path.dirname(__file__), "resources")


# def copy_distributed_load():
    # sel = FreeCADGui.Selection.getSelection()

    # if len(sel) < 2:
        # FreeCAD.Console.PrintError("Please select source load object first, then target elements.\n")
        # return

    # source = sel[0]
    # targets = sel[1:]

    # required_props = ["InitialLoading", "FinalLoading", "GlobalDirection", "ScaleDraw"]
    # if not all(hasattr(source, p) for p in required_props):
        # FreeCAD.Console.PrintError("Source object does not appear to be a valid LoadDistributed object.\n")
        # return

    # for target in targets:
        # try:
            # if not hasattr(target, "InitialLoading"):
                # target.addProperty("App::PropertyForce", "InitialLoading", "Distributed", "Initial loading")
            # if not hasattr(target, "FinalLoading"):
                # target.addProperty("App::PropertyForce", "FinalLoading", "Distributed", "Final loading")
            # if not hasattr(target, "GlobalDirection"):
                # target.addProperty("App::PropertyEnumeration", "GlobalDirection", "Load", "Global direction")
                # target.GlobalDirection = ['+X','-X', '+Y','-Y', '+Z','-Z']
            # if not hasattr(target, "ScaleDraw"):
                # target.addProperty("App::PropertyFloat", "ScaleDraw", "Load", "Drawing scale")

            # target.InitialLoading = source.InitialLoading
            # target.FinalLoading = source.FinalLoading
            # target.GlobalDirection = source.GlobalDirection
            # target.ScaleDraw = source.ScaleDraw

            # FreeCAD.Console.PrintMessage(f"Copied load properties to {target.Name}\n")

        # except Exception as e:
            # FreeCAD.Console.PrintError(f"Error copying to {target.Name}: {e}\n")

    # FreeCAD.ActiveDocument.recompute()

# Run it
#copy_distributed_load()


class CommandCopyload():
    """Copy load from selected member to others"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/Lss.svg"),
            "Accel": "" ,
            "MenuText": "Copy load value",
            "ToolTip": "Copies load from the first selected member to the rest"
        }

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()

        if len(sel) < 2:
           FreeCAD.Console.PrintError("Please select source load object first, then target elements.\n")
           return

        source = sel[0]
        targets = sel[1:]

        required_props = ["InitialLoading", "FinalLoading", "GlobalDirection", "ScaleDraw"]
        if not all(hasattr(source, p) for p in required_props):
           FreeCAD.Console.PrintError("Source object does not appear to be a valid LoadDistributed object.\n")
           return

        for target in targets:
            try:
                if not hasattr(target, "InitialLoading"):
                   target.addProperty("App::PropertyForce", "InitialLoading", "Distributed", "Initial loading")
                if not hasattr(target, "FinalLoading"):
                   target.addProperty("App::PropertyForce", "FinalLoading", "Distributed", "Final loading")
                if not hasattr(target, "GlobalDirection"):
                   target.addProperty("App::PropertyEnumeration", "GlobalDirection", "Load", "Global direction")
                   target.GlobalDirection = ['+X','-X', '+Y','-Y', '+Z','-Z']
                if not hasattr(target, "ScaleDraw"):
                   target.addProperty("App::PropertyFloat", "ScaleDraw", "Load", "Drawing scale")

                target.InitialLoading = source.InitialLoading
                target.FinalLoading = source.FinalLoading
                target.GlobalDirection = source.GlobalDirection
                target.ScaleDraw = source.ScaleDraw

                FreeCAD.Console.PrintMessage(f"Copied load properties to {target.Name}\n")

            except Exception as e:
                FreeCAD.Console.PrintError(f"Error copying to {target.Name}: {e}\n")

        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return True


FreeCADGui.addCommand("Copyload", CommandCopyload())

