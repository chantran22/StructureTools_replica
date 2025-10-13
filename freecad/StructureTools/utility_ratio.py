import FreeCAD, FreeCADGui, Part, math, os
from PySide2 import QtWidgets

ICONPATH = os.path.join(os.path.dirname(__file__), "resources")
pathFont = os.path.join(os.path.dirname(__file__), "resources/fonts/ARIAL.TTF")

def show_error_message(msg):
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(QtWidgets.QMessageBox.Critical)
    msg_box.setWindowTitle("Error")
    msg_box.setText(msg)
    msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg_box.exec_()


class UtilityRatioVisual:
    """Visual display of utility ratios as text labels on structural members"""
    
    def __init__(self, obj, objCalc, listSelection):
        obj.Proxy = self
        obj.addProperty("App::PropertyLink", "ObjectBaseCalc", "Base", "Calc object with analysis results").ObjectBaseCalc = objCalc
        obj.addProperty("App::PropertyLinkSubList", "ObjectBaseElements", "Base", "Selected members for display").ObjectBaseElements = self.getMembers(listSelection)
        
        # Display properties
        obj.addProperty("App::PropertyColor", "ColorPass", "Display", "Color for passing ratios (UR ≤ 1.0)").ColorPass = (0, 255, 0, 0)  # Green
        obj.addProperty("App::PropertyColor", "ColorFail", "Display", "Color for failing ratios (UR > 1.0)").ColorFail = (255, 0, 0, 0)  # Red
        obj.addProperty("App::PropertyInteger", "FontHeight", "Display", "Font size for ratio values").FontHeight = 40
        obj.addProperty("App::PropertyInteger", "Precision", "Display", "Decimal precision for values").Precision = 3
        
        # Capacity factors
        obj.addProperty("App::PropertyFloat", "PhiCompression", "Capacity", "Capacity reduction for compression").PhiCompression = 0.90
        obj.addProperty("App::PropertyFloat", "PhiBending", "Capacity", "Capacity reduction for bending").PhiBending = 0.90
        obj.addProperty("App::PropertyFloat", "PhiTension", "Capacity", "Capacity reduction for tension").PhiTension = 0.90
        
        # Label position
        obj.addProperty("App::PropertyFloat", "LabelOffset", "Display", "Offset distance from member").LabelOffset = 60.0

    def getMembers(self, listSelection):
        """Get members to display - selected or all"""
        if listSelection:
            return [(sel.Object, sel.SubElementNames) for sel in listSelection]
        
        # Auto-select all members
        objects = FreeCAD.ActiveDocument.Objects
        members = [obj for obj in objects 
                  if ('Wire' in obj.Name or 'Line' in obj.Name) 
                  and 'MaterialMember' in obj.PropertiesList]
        
        return [(member, [f'Edge{i+1}' for i in range(len(member.Shape.Edges))]) 
                for member in members]

    def getMatrix(self, param):
        """Convert parameter strings to float matrix"""
        return [[float(val) for val in line.split(',')] for line in param]

    def mapNodes(self, elements):
        """Map all unique nodes from structure elements"""
        nodes = []
        for element in elements:
            for edge in element.Shape.Edges:
                for vertex in edge.Vertexes:
                    node = [round(vertex.Point.x, 2), 
                           round(vertex.Point.y, 2), 
                           round(vertex.Point.z, 2)]
                    if node not in nodes:
                        nodes.append(node)
        return nodes

    def mapMembers(self, elements, listNodes):
        """Map members with their node indices"""
        members = {}
        for element in elements:
            for i, edge in enumerate(element.Shape.Edges):
                indices = []
                for vertex in edge.Vertexes:
                    node = [round(vertex.Point.x, 2), 
                           round(vertex.Point.y, 2), 
                           round(vertex.Point.z, 2)]
                    indices.append(listNodes.index(node))
                
                n1, n2 = indices
                if listNodes[n1][2] > listNodes[n2][2]:
                    n1, n2 = n2, n1
                
                members[f"{element.Name}_{i}"] = {
                    'nodes': [str(n1), str(n2)]
                }
        return members

    def getSectionProperties(self, member_name):
        """Get section properties from the original line element"""
        try:
            parts = member_name.rsplit('_', 1)
            if len(parts) != 2:
                return None
            
            base_name = parts[0]
            edge_idx = int(parts[1])
            
            # Find the line element
            line_element = None
            for obj in FreeCAD.ActiveDocument.Objects:
                if obj.Name == base_name:
                    line_element = obj
                    break
            
            if not line_element or not hasattr(line_element, 'SectionMember'):
                return None
            
            section = line_element.SectionMember
            material = line_element.MaterialMember if hasattr(line_element, 'MaterialMember') else None
            
            properties = {
                'name': section.Label if hasattr(section, 'Label') else 'Unknown',
                'area': float(section.AreaSection.getValueAs('cm^2')),
                'Iy': float(FreeCAD.Units.Quantity(section.MomentInertiaY, 'cm^4').getValueAs('cm^4')),
                'Iz': float(FreeCAD.Units.Quantity(section.MomentInertiaZ, 'cm^4').getValueAs('cm^4')),
            }
            
            if hasattr(section, 'Height'):
                properties['height'] = float(section.Height.getValueAs('mm'))
            else:
                properties['height'] = 0.0
            
            if hasattr(section, 'Width'):
                properties['width'] = float(section.Width.getValueAs('mm'))
            else:
                properties['width'] = 0.0
            
            if material and hasattr(material, 'YieldStrength'):
                properties['fy'] = float(material.YieldStrength.getValueAs('MPa'))
            else:
                properties['fy'] = 250.0
            
            return properties
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error getting section properties for {member_name}: {str(e)}\n")
            return None

    def calculateCapacities(self, section_props):
        """Calculate member capacities from section properties"""
        if not section_props:
            return None
        
        try:
            A = section_props['area']
            Iy = section_props['Iy']
            Iz = section_props['Iz']
            fy = section_props['fy']
            
            h = section_props.get('height', 0.0)
            b = section_props.get('width', 0.0)
            
            # Calculate section moduli
            if h > 0:
                Wy = (2 * Iy) / (h / 10)
            else:
                h_est = math.sqrt(12 * Iy / A) if A > 0 else 0
                Wy = (2 * Iy) / h_est if h_est > 0 else Iy / 10
            
            if b > 0:
                Wz = (2 * Iz) / (b / 10)
            else:
                b_est = math.sqrt(12 * Iz / A) if A > 0 else 0
                Wz = (2 * Iz) / b_est if b_est > 0 else Iz / 10
            
            # Calculate capacities
            N_capacity = (A * fy) / 10.0  # kN
            My_capacity = (Wy * fy) / 1000.0  # kN·m
            Mz_capacity = (Wz * fy) / 1000.0  # kN·m
            
            return {
                'N': N_capacity,
                'My': My_capacity,
                'Mz': Mz_capacity
            }
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error calculating capacities: {str(e)}\n")
            return None

    def calculateUtilityRatio(self, forces, capacities, phi_comp, phi_tension, phi_bend):
        """Calculate utility ratio: UR = |N|/(φ·[N]) + |My|/(φ·[My]) + |Mz|/(φ·[Mz])"""
        if not capacities:
            return 0.0
        
        try:
            N = forces['axial']
            My = abs(forces['moment_y'])
            Mz = abs(forces['moment_z'])
            
            N_cap = capacities['N']
            My_cap = capacities['My']
            Mz_cap = capacities['Mz']
            
            phi_axial = phi_comp if N < 0 else phi_tension
            
            axial_ratio = abs(N) / (phi_axial * N_cap) if N_cap > 0 else 0.0
            my_ratio = My / (phi_bend * My_cap) if My_cap > 0 else 0.0
            mz_ratio = Mz / (phi_bend * Mz_cap) if Mz_cap > 0 else 0.0
            
            total = axial_ratio + my_ratio + mz_ratio
            
            return total
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error calculating utility ratio: {str(e)}\n")
            return 0.0

    def makeText(self, text_string, position, color_rgb, font_height):
        """Create text annotation at specified position"""
        try:
            # Create annotation object
            ann_obj = FreeCAD.ActiveDocument.addObject("App::Annotation", f"UR_{text_string}_{id(position)}")
            ann_obj.LabelText = text_string
            ann_obj.Position = position

            # Set text color properly for annotations
            if hasattr(ann_obj.ViewObject, "TextColor"):
                # Convert from 0-1 range to tuple format (R, G, B, A) where each is 0.0-1.0
                ann_obj.ViewObject.TextColor = color_rgb + (1.0,)  # Add alpha channel
            
            if hasattr(ann_obj.ViewObject, "FontSize"):
                ann_obj.ViewObject.FontSize = font_height

            return ann_obj

        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Warning: Could not create annotation: {str(e)}\n")
            return None


    def filterMembersSelected(self, obj):
        """Filter members based on selection"""
        if not obj.ObjectBaseElements:
            return list(enumerate(obj.ObjectBaseCalc.NameMembers))
        
        selected = []
        for element, sub_names in obj.ObjectBaseElements:
            for sub_name in sub_names:
                edge_idx = int(sub_name.split('Edge')[1]) - 1
                member_name = f"{element.Name}_{edge_idx}"
                if member_name in obj.ObjectBaseCalc.NameMembers:
                    member_idx = obj.ObjectBaseCalc.NameMembers.index(member_name)
                    selected.append((member_idx, member_name))
        
        return selected

    def execute(self, obj):
        """Main execution - create text labels showing utility ratios at 3 positions per member"""
        try:
            # Get structure data
            elements = [el for el in obj.ObjectBaseCalc.ListElements 
                       if 'Line' in el.Name or 'Wire' in el.Name]
            nodes = self.mapNodes(elements)
            members = self.mapMembers(elements, nodes)
            order_members = self.filterMembersSelected(obj)
            
            # Get force matrices
            moment_y = self.getMatrix(obj.ObjectBaseCalc.MomentY)
            moment_z = self.getMatrix(obj.ObjectBaseCalc.MomentZ)
            axial = self.getMatrix(obj.ObjectBaseCalc.AxialForce)
            
            FreeCAD.Console.PrintMessage(f"\n{'='*70}\n")
            FreeCAD.Console.PrintMessage(f"UTILITY RATIO LABELS (3 per member)\n")
            FreeCAD.Console.PrintMessage(f"{'='*70}\n")
            
            pass_count = 0
            fail_count = 0
            total_labels = 0
            
            # Process each member
            for member_idx, member_name in order_members:
                FreeCAD.Console.PrintMessage(f"\nProcessing {member_name}...\n")
                
                member = members[member_name]
                
                # Get section properties
                section_props = self.getSectionProperties(member_name)
                if not section_props:
                    FreeCAD.Console.PrintWarning(f"  Skipping - no section properties\n")
                    continue
                
                # Calculate capacities
                capacities = self.calculateCapacities(section_props)
                if not capacities:
                    FreeCAD.Console.PrintWarning(f"  Skipping - capacity calculation failed\n")
                    continue
                
                # Get node positions
                p1 = nodes[int(member['nodes'][0])]
                p2 = nodes[int(member['nodes'][1])]
                
                # Get force values
                if member_idx >= len(moment_y) or member_idx >= len(moment_z) or member_idx >= len(axial):
                    FreeCAD.Console.PrintWarning(f"  Skipping - member index out of range\n")
                    continue
                
                my_values = moment_y[member_idx]
                mz_values = moment_z[member_idx]
                n_values = axial[member_idx]
                
                # Get minimum length
                min_length = min(len(my_values), len(mz_values), len(n_values))
                if min_length == 0:
                    FreeCAD.Console.PrintWarning(f"  Skipping - no force data\n")
                    continue
                
                # Define 3 positions: start (0), middle (50%), end (100%)
                # Calculate indices for start, middle, end
                if min_length < 3:
                    check_indices = list(range(min_length))
                else:
                    check_indices = [0, min_length // 2, min_length - 1]
                
                member_max_ratio = 0.0
                
                # Calculate utility ratios at 3 positions
                for idx, point_idx in enumerate(check_indices):
                    forces = {
                        'axial': n_values[point_idx],
                        'moment_y': my_values[point_idx],
                        'moment_z': mz_values[point_idx]
                    }
                    
                    ratio = self.calculateUtilityRatio(
                        forces, capacities,
                        obj.PhiCompression, obj.PhiTension, obj.PhiBending
                    )
                    
                    member_max_ratio = max(member_max_ratio, ratio)
                    
                    # Calculate position along member (0 = start, 0.5 = middle, 1.0 = end)
                    if len(check_indices) > 1:
                        t = point_idx / (min_length - 1)
                    else:
                        t = 0.5
                    
                    # Interpolate position along member
                    pos_x = p1[0] + t * (p2[0] - p1[0])
                    pos_y = p1[1] + t * (p2[1] - p1[1])
                    pos_z = p1[2] + t * (p2[2] - p1[2])
                    
                    # Offset label position
                    label_pos = FreeCAD.Vector(pos_x, pos_y, pos_z + obj.LabelOffset)
                    
                    # Create text label
                    position_name = ["START", "MID", "END"][idx] if len(check_indices) == 3 else f"P{idx}"
                    text_string = f"UR:{ratio:.{obj.Precision}f}"
                    
                    # Determine color (pass = green, fail = red)
                    if ratio > 1.0:
                        # Red color for failure
                        color_rgb = (obj.ColorFail[0]/255.0, obj.ColorFail[1]/255.0, obj.ColorFail[2]/255.0)
                    else:
                        # Green color for pass
                        color_rgb = (obj.ColorPass[0]/255.0, obj.ColorPass[1]/255.0, obj.ColorPass[2]/255.0)
                    
                    # Create text
                    text_obj = self.makeText(text_string, label_pos, color_rgb, obj.FontHeight)
                    total_labels += 1
                    
                    # Report
                    FreeCAD.Console.PrintMessage(f"  {position_name}: UR = {ratio:.{obj.Precision}f}\n")
                
                # Count pass/fail for this member based on max ratio
                if member_max_ratio > 1.0:
                    fail_count += 1
                else:
                    pass_count += 1
            
            # Summary
            FreeCAD.Console.PrintMessage(f"\n{'='*70}\n")
            FreeCAD.Console.PrintMessage(f"SUMMARY\n")
            FreeCAD.Console.PrintMessage(f"{'='*70}\n")
            FreeCAD.Console.PrintMessage(f"Total members: {pass_count + fail_count}\n")
            FreeCAD.Console.PrintMessage(f"Total labels created: {total_labels}\n")
            FreeCAD.Console.PrintMessage(f"PASS (UR ≤ 1.0): {pass_count}\n")
            FreeCAD.Console.PrintMessage(f"FAIL (UR > 1.0): {fail_count}\n")
            
            if fail_count > 0:
                FreeCAD.Console.PrintWarning(f"\n⚠ WARNING: {fail_count} members are overstressed!\n")
            else:
                FreeCAD.Console.PrintMessage(f"\n✓ All members pass the utility ratio check.\n")
            
            FreeCAD.Console.PrintMessage(f"{'='*70}\n\n")
            
            # Create empty shape for main object
            obj.Shape = Part.Shape()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error generating utility ratio labels: {str(e)}\n")
            import traceback
            traceback.print_exc()

    def onChanged(self, obj, Parameter):
        if Parameter in ['PhiCompression', 'PhiBending', 'PhiTension', 
                        'Precision', 'FontHeight', 'LabelOffset',
                        'ColorPass', 'ColorFail']:
            if hasattr(obj, 'ObjectBaseCalc') and obj.ObjectBaseCalc:
                self.execute(obj)


class ViewProviderUtilityRatio:
    def __init__(self, obj):
        obj.Proxy = self

    def getIcon(self):
        return os.path.join(ICONPATH, "icons/percent.svg")


class CommandUtilityRatioVisual():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "icons/percent.svg"),
            "Accel": "",
            "MenuText": "Utility Ratio Labels",
            "ToolTip": "Display utility ratio values as colored text labels on members"
        }
    
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        if not selection:
            show_error_message('Select a calc object to show utility ratios')
            return
        
        objCalc = selection[0].Object
        listSelects = [sel for sel in selection 
                      if 'Wire' in sel.Object.Name or 'Line' in sel.Object.Name]
        
        if 'Calc' not in objCalc.Name:
            show_error_message('Must select a calc object to display utility ratios')
            return
        
        doc = FreeCAD.ActiveDocument
        obj = doc.addObject("Part::FeaturePython", "UtilityRatio")
        UtilityRatioVisual(obj, objCalc, listSelects)
        ViewProviderUtilityRatio(obj.ViewObject)
        
        FreeCAD.ActiveDocument.recompute()
    
    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


FreeCADGui.addCommand("utility_ratio_visual", CommandUtilityRatioVisual())