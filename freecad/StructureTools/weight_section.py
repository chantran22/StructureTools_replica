import FreeCAD, FreeCADGui
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide2 import QtWidgets
import  os

script_dir = os.path.dirname(os.path.abspath(__file__))
ICONPATH = os.path.join(script_dir, "resources")



# Standard material densities (kg/m³)
MATERIAL_DENSITIES = {
    "Steel": 7850,
    "Aluminum": 2700,
    "Concrete": 2400,
    "Wood": 600,
    "Stainless Steel": 8000,
    "Cast Iron": 7200,
    "Custom": 0  # User will input custom density
}

def calculate_weight_by_section():
    """Calculate total weight for all objects with a specific SectionMember label"""
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

    # Select material and get density
    material_items = list(MATERIAL_DENSITIES.keys())
    material, ok = QtWidgets.QInputDialog.getItem(
        None, 
        "Material Selection", 
        "Select material:", 
        material_items, 
        0, 
        False
    )
    if not ok:
        return

    density = MATERIAL_DENSITIES[material]
    if material == "Custom":
        density, ok = QtWidgets.QInputDialog.getDouble(
            None, 
            "Custom Density", 
            "Enter material density (kg/m³):", 
            7850, 
            0, 
            20000, 
            2
        )
        if not ok:
            return

    # Find all objects with matching SectionMember label
    matched_objects = []
    total_weight = 0
    total_length = 0
    section_area = 0

    for obj in doc.Objects:
        if hasattr(obj, "SectionMember") and obj.SectionMember:
            if hasattr(obj.SectionMember, "Label") and obj.SectionMember.Label == section_name:
                if hasattr(obj, "Shape") and obj.Shape:
                    length = obj.Shape.Length / 1000  # Convert mm to m
                    
                    # Get section area from SectionMember
                    if hasattr(obj.SectionMember, "AreaSection"):
                        area_mm2 = obj.SectionMember.AreaSection.Value # value in
                        area_m2 = area_mm2 / 10**6  # Convert mm² to m²
                        if section_area == 0:  # Store first area found
                            section_area = area_mm2
                    else:
                        # Fallback: estimate from shape if no sectional area
                        area_m2 = 0.001  # Default small area
                        area_mm2 = 1000
                    
                    weight = length * area_m2 * density  # kg
                    total_weight += weight
                    total_length += length
                    
                    matched_objects.append({
                        'name': obj.Name,
                        'length': length,
                        'area_mm2': area_mm2,
                        'weight': weight
                    })

    if matched_objects:
        # Create detailed report
        report = f"\n{'='*60}\n"
        report += f"WEIGHT CALCULATION REPORT\n"
        report += f"{'='*60}\n"
        report += f"Section: {section_name}\n"
        report += f"Material: {material}\n"
        report += f"Density: {density:.2f} kg/m³\n"
        report += f"Section Area: {section_area:.2f} mm²\n"
        report += f"{'='*60}\n"
        
        for obj in matched_objects:
            report += f"{obj['name']:<20} | "
            report += f"L: {obj['length']:.3f} m | "
            report += f"A: {obj['area_mm2']:.1f} mm² | "
            report += f"W: {obj['weight']:.3f} kg\n"
        
        report += f"{'='*60}\n"
        report += f"TOTALS:\n"
        report += f"Total Length: {total_length:.3f} m\n"
        report += f"Total Weight: {total_weight:.3f} kg\n"
        report += f"Weight per meter: {total_weight/total_length:.3f} kg/m\n"
        report += f"{'='*60}\n"
        
        print(report)
        
        # Show summary dialog
        QtWidgets.QMessageBox.information(
            None, 
            "Weight Calculation Complete", 
            f"Section: {section_name}\n"
            f"Objects: {len(matched_objects)}\n"
            f"Total Length: {total_length:.3f} m\n"
            f"Total Weight: {total_weight:.3f} kg\n"
            f"Material: {material} ({density} kg/m³)\n\n"
            f"Detailed report printed to console."
        )
    else:
        App.Console.PrintMessage(f"No objects found with SectionMember label: {section_name}\n")



def get_section_properties():
    """Display section properties for a specific section type"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document.\n")
        return

    # Prompt user for SectionMember label
    section_name, ok = QtWidgets.QInputDialog.getText(
        None, 
        "Section Properties", 
        "Enter SectionMember label (e.g., W200X52):"
    )
    if not ok or not section_name:
        return

    # Find first object with this section
    section_obj = None
    for obj in doc.Objects:
        if hasattr(obj, "SectionMember") and obj.SectionMember:
            if hasattr(obj.SectionMember, "Label") and obj.SectionMember.Label == section_name:
                section_obj = obj.SectionMember
                break

    if not section_obj:
        QtWidgets.QMessageBox.information(
            None, 
            "Not Found", 
            f"No section found with label: {section_name}"
        )
        return

    # Extract properties
    properties = f"\nSECTION PROPERTIES: {section_name}\n"
    properties += f"{'-'*50}\n"
    
    if hasattr(section_obj, "SectionalArea"):
        area = section_obj.SectionalArea.Value
        properties += f"Sectional Area: {area:.2f} mm²\n"
    
    # if hasattr(section_obj, "MomentOfInertiaX"):
    #     ixx = section_obj.MomentOfInertiaX.Value
    #     properties += f"Moment of Inertia X: {ixx:.2f} mm⁴\n"
    
    # if hasattr(section_obj, "MomentOfInertiaY"):
    #     iyy = section_obj.MomentOfInertiaY.Value
    #     properties += f"Moment of Inertia Y: {iyy:.2f} mm⁴\n"
    
    # if hasattr(section_obj, "TorsionalMoment"):
    #     j = section_obj.TorsionalMoment.Value
    #     properties += f"Torsional Moment: {j:.2f} mm⁴\n"
    
    properties += f"{'-'*50}\n"
    
    print(properties)
    
    QtWidgets.QMessageBox.information(
        None, 
        f"Section Properties: {section_name}", 
        properties
    )




def calculate_weight_all_sections():
    """Calculate weight for all sections in the document, grouped by section type"""
    doc = App.ActiveDocument
    if not doc:
        App.Console.PrintError("No active document.\n")
        return

    # Select material and get density
    material_items = list(MATERIAL_DENSITIES.keys())
    material, ok = QtWidgets.QInputDialog.getItem(
        None, 
        "Material Selection", 
        "Select material for all sections:", 
        material_items, 
        0, 
        False
    )
    if not ok:
        return

    density = MATERIAL_DENSITIES[material]
    if material == "Custom":
        density, ok = QtWidgets.QInputDialog.getDouble(
            None, 
            "Custom Density", 
            "Enter material density (kg/m³):", 
            7850, 
            0, 
            20000, 
            2
        )
        if not ok:
            return

    # Group objects by section type
    sections_data = {}
    
    for obj in doc.Objects:
        if hasattr(obj, "SectionMember") and obj.SectionMember:
            if hasattr(obj.SectionMember, "Label"):
                section_name = obj.SectionMember.Label
                
                if hasattr(obj, "Shape") and obj.Shape:
                    length = obj.Shape.Length / 1000  # Convert mm to m
                    
                    # Get section area
                    if hasattr(obj.SectionMember, "AreaSection"):
                        area_mm2 = obj.SectionMember.AreaSection.Value # 
                        area_m2 = area_mm2 / 10**6 # Convert mm² to m²
                        #area_m2 = area_mm2 / 1000000  # Convert mm² to m²
                    else:
                        area_m2 = 0.001  # Default
                        area_mm2 = 1000
                    
                    weight = length * area_m2 * density  # kg
                    
                    if section_name not in sections_data:
                        sections_data[section_name] = {
                            'objects': [],
                            'total_length': 0,
                            'total_weight': 0,
                            'area_mm2': area_mm2
                        }
                    
                    sections_data[section_name]['objects'].append({
                        'name': obj.Name,
                        'length': length,
                        'weight': weight
                    })
                    sections_data[section_name]['total_length'] += length
                    sections_data[section_name]['total_weight'] += weight

    if sections_data:
        # Create comprehensive report
        report = f"\n{'='*80}\n"
        report += f"COMPREHENSIVE WEIGHT REPORT - ALL SECTIONS\n"
        report += f"{'='*80}\n"
        report += f"Material: {material} (Density: {density:.2f} kg/m³)\n"
        report += f"{'='*80}\n"
        
        grand_total_weight = 0
        grand_total_length = 0
        
        for section_name, data in sorted(sections_data.items()):
            report += f"\nSECTION: {section_name}\n"
            report += f"Area: {data['area_mm2']:.1f} mm²\n"
            report += f"{'-'*60}\n"
            
            for obj in data['objects']:
                report += f"  {obj['name']:<25} | L: {obj['length']:.3f} m | W: {obj['weight']:.3f} kg\n"
            
            report += f"{'-'*60}\n"
            report += f"  Section Total: Length: {data['total_length']:.3f} m | Weight: {data['total_weight']:.3f} kg\n"
            report += f"  Weight/meter: {data['total_weight']/data['total_length']:.3f} kg/m\n"
            
            grand_total_weight += data['total_weight']
            grand_total_length += data['total_length']
        
        report += f"\n{'='*80}\n"
        report += f"GRAND TOTALS:\n"
        report += f"Total Length: {grand_total_length:.3f} m\n"
        report += f"Total Weight: {grand_total_weight:.3f} kg\n"
        report += f"Average Weight/meter: {grand_total_weight/grand_total_length:.3f} kg/m\n"
        report += f"{'='*80}\n"
        
        print(report)
        
        # Show summary dialog
        summary = f"Material: {material}\n"
        summary += f"Total Sections: {len(sections_data)}\n"
        summary += f"Total Length: {grand_total_length:.3f} m\n"
        summary += f"Total Weight: {grand_total_weight:.3f} kg\n\n"
        summary += "Detailed report printed to console."
        
        QtWidgets.QMessageBox.information(
            None, 
            "Complete Weight Analysis", 
            summary
        )
    else:
        App.Console.PrintMessage("No objects with SectionMember found in document.\n")



class WeightbySect:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/scaleweight.svg"),
            "Accel": "",
            "MenuText": "Weight by section",
            "ToolTip": "Weight all steel structure"
        }

    def Activated(self):
        tool = calculate_weight_by_section()
        #tool.run()

    def IsActive(self):
        return App.ActiveDocument is not None
        
        


class WeightallbySect:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/scaleallwt.svg"),
            "Accel": "",
            "MenuText": "Weight all by section",
            "ToolTip": "Weight all steel structure"
        }

    def Activated(self):
        tool = calculate_weight_all_sections()
        #tool.run()

    def IsActive(self):
        return App.ActiveDocument is not None
        

Gui.addCommand("Weight_structure", WeightbySect())

Gui.addCommand("Weightall_structure", WeightallbySect())
