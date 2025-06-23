import FreeCAD, FreeCADGui
import FreeCAD as App
import FreeCADGui as Gui
from PySide2 import QtWidgets
import  os

script_dir = os.path.dirname(os.path.abspath(__file__))
ICONPATH = os.path.join(script_dir, "resources")

def change_line_color_by_section():
    """Change line color for all objects with a specific SectionMember label"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document.\n")
        return

    # Prompt user for SectionMember label to filter
    section_name, ok = QtWidgets.QInputDialog.getText(
        None, 
        "Section Filter", 
        "Enter SectionMember label (e.g., W200X52):"
    )
    if not ok or not section_name:
        return

    # Ask user for color
    color = QtWidgets.QColorDialog.getColor()
    if not color.isValid():
        return

    # Convert QColor to FreeCAD RGB tuple
    r = color.red() / 255.0
    g = color.green() / 255.0
    b = color.blue() / 255.0
    fc_color = (r, g, b)

    # Find all objects with matching SectionMember label
    matched_objects = []
    for obj in doc.Objects:
        if hasattr(obj, "SectionMember") and obj.SectionMember:
            if hasattr(obj.SectionMember, "Label") and obj.SectionMember.Label == section_name:
                matched_objects.append(obj)

    if not matched_objects:
        QtWidgets.QMessageBox.information(
            None, 
            "No Objects Found", 
            f"No objects found with SectionMember label: {section_name}"
        )
        return

    # Apply color to all matched objects
    success_count = 0
    for obj in matched_objects:
        try:
            if hasattr(obj, 'ViewObject') and obj.ViewObject:
                obj.ViewObject.LineColor = fc_color
                success_count += 1
        except Exception as e:
            App.Console.PrintError(f"Failed to set color for {obj.Name}: {e}\n")

    # Show results
    if success_count > 0:
        QtWidgets.QMessageBox.information(
            None, 
            "Success", 
            f"Color applied to {success_count} object(s) with section '{section_name}'."
        )
        App.Console.PrintMessage(f"Color changed for {success_count} objects with section '{section_name}'.\n")
        
        # Refresh the view
        Gui.updateGui()
    else:
        QtWidgets.QMessageBox.warning(
            None, 
            "Error", 
            f"Failed to apply color to any objects with section '{section_name}'."
        )




#sum_length_by_section()


class ColorbySect:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/colorsec.svg"),
            "Accel": "",
            "MenuText": "Color for section",
            "ToolTip": "Copy color from 1st line to other lines"
        }

    def Activated(self):
        tool = change_line_color_by_section()
        #tool.run()

    def IsActive(self):
        return App.ActiveDocument is not None

Gui.addCommand("Color_Section", ColorbySect())
