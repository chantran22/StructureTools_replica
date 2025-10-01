import FreeCAD, FreeCADGui, Part, math, os
from typing import List, Tuple, Any, Optional, Dict
import logging

# Prefer PySide2 when available
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    try:
        from PySide import QtWidgets, QtCore, QtGui
    except ImportError as e:
        raise ImportError("Neither PySide2 nor PySide could be imported. Please install one of them.") from e

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ICONPATH = os.path.join(os.path.dirname(__file__), "resources")


class ReactionResults:
    """Class for displaying and managing reaction force and moment results from structural analysis."""
    
    def __init__(self, obj: Any, objCalc: Any) -> None:
        """Initialize the ReactionResults object.
        
        Args:
            obj: The FreeCAD object to attach to
            objCalc: The calculation object containing analysis results
        """
        obj.Proxy = self
        obj.addProperty("App::PropertyLink", "ObjectBaseCalc", "Base", "Calculation object with analysis results").ObjectBaseCalc = objCalc
        
        # Reaction force display properties
        obj.addProperty("App::PropertyBool", "ShowReactionFX", "Reaction Forces", "Show X-direction reaction forces").ShowReactionFX = True
        obj.addProperty("App::PropertyBool", "ShowReactionFY", "Reaction Forces", "Show Y-direction reaction forces").ShowReactionFY = True
        obj.addProperty("App::PropertyBool", "ShowReactionFZ", "Reaction Forces", "Show Z-direction reaction forces").ShowReactionFZ = True
        obj.addProperty("App::PropertyFloat", "ScaleReactionForces", "Reaction Forces", "Scale factor for reaction force display").ScaleReactionForces = 10.0
        
        # Reaction moment display properties
        obj.addProperty("App::PropertyBool", "ShowReactionMX", "Reaction Moments", "Show X-axis reaction moments").ShowReactionMX = True
        obj.addProperty("App::PropertyBool", "ShowReactionMY", "Reaction Moments", "Show Y-axis reaction moments").ShowReactionMY = True
        obj.addProperty("App::PropertyBool", "ShowReactionMZ", "Reaction Moments", "Show Z-axis reaction moments").ShowReactionMZ = True
        obj.addProperty("App::PropertyFloat", "ScaleReactionMoments", "Reaction Moments", "Scale factor for reaction moment display").ScaleReactionMoments = 10.0
        
        # Display options
        obj.addProperty("App::PropertyColor", "ForceArrowColor", "Display", "Color for force labels").ForceArrowColor = (1.0, 0.0, 0.0, 0.0)  # Red
        obj.addProperty("App::PropertyColor", "MomentArrowColor", "Display", "Color for moment labels").MomentArrowColor = (0.0, 1.0, 0.0, 0.0)  # Green
        obj.addProperty("App::PropertyBool", "ShowLabels", "Display", "Show reaction value labels").ShowLabels = True
        obj.addProperty("App::PropertyInteger", "LabelFontSize", "Display", "Font size for reaction labels").LabelFontSize = 8
        obj.addProperty("App::PropertyInteger", "Precision", "Display", "Decimal places for reaction values").Precision = 2
        
        # Minimum reaction threshold
        obj.addProperty("App::PropertyFloat", "MinReactionThreshold", "Display", "Minimum reaction magnitude to display").MinReactionThreshold = 1e-6
        
        # Internal storage for reaction visualization objects
        self.reaction_objects = []
        self.label_objects = []
        
        # Store reference to the FE model after analysis
        self.fe_model = None

    def execute(self, obj):
        """Execute the reaction visualization update."""
        try:
            self.clear_existing_visualization(obj)
            
            # Get the FE model from calc object
            if not self.get_fe_model_from_calc(obj):
                return
                
            self.create_reaction_visualization(obj)
        except Exception as e:
            logger.error(f"Error in ReactionResults.execute: {str(e)}")
            FreeCAD.Console.PrintError(f"ReactionResults error: {str(e)}\n")
    
    def get_fe_model_from_calc(self, obj):
        """Get the FE model from the Calc object after analysis has been run."""
        if not obj.ObjectBaseCalc:
            FreeCAD.Console.PrintError("No calculation object found\n")
            return False
            
        calc_obj = obj.ObjectBaseCalc
        
        # The Calc class from calc.txt creates the FE model in its execute() method
        # but doesn't store it as a property. We need to trigger the analysis
        # and capture the model during the process.
        
        # Check if calc has been executed recently
        if not hasattr(calc_obj, 'ListElements') or not calc_obj.ListElements:
            FreeCAD.Console.PrintError("Calc object has no elements - please set up the calculation first\n")
            return False
        
        # Try to recreate the FE model by calling the calc's internal methods
        try:
            # Import the FE model class
            from .Pynite_main.FEModel3D import FEModel3D
            
            # Recreate the model using calc's methods
            calc_proxy = calc_obj.Proxy
            model = FEModel3D()
            
            # Filter the different types of elements (same as in Calc.execute)
            lines = list(filter(lambda element: 'Line' in element.Name or 'Wire' in element.Name, calc_obj.ListElements))
            loads = list(filter(lambda element: 'Load' in element.Name, calc_obj.ListElements))
            supports = list(filter(lambda element: 'Suport' in element.Name, calc_obj.ListElements))
            
            if not lines:
                FreeCAD.Console.PrintError("No structural members found in calculation\n")
                return False
                
            if not supports:
                FreeCAD.Console.PrintError("No supports found in calculation\n")
                return False
            
            # Build the model using calc's methods
            nodes_map = calc_proxy.mapNodes(lines, calc_obj.LengthUnit)
            members_map = calc_proxy.mapMembers(lines, nodes_map, calc_obj.LengthUnit)
            
            model = calc_proxy.setMaterialAndSections(model, lines, calc_obj.LengthUnit, calc_obj.ForceUnit)
            model = calc_proxy.setNodes(model, nodes_map)
            model = calc_proxy.setMembers(model, members_map, calc_obj.selfWeight)
            model = calc_proxy.setLoads(model, loads, nodes_map, calc_obj.ForceUnit, calc_obj.LengthUnit)
            model = calc_proxy.setSuports(model, supports, nodes_map, calc_obj.LengthUnit)
            
            # Run the analysis
            FreeCAD.Console.PrintMessage("Running structural analysis for reaction calculation...\n")
            model.analyze()
            
            # Store the model
            self.fe_model = model
            
            FreeCAD.Console.PrintMessage(f"Analysis complete. Found {len(model.nodes)} nodes\n")
            return True
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to get FE model from calc: {str(e)}\n")
            return False

    def clear_existing_visualization(self, obj):
        """Clear all existing reaction visualization objects."""
        for react_obj in self.reaction_objects + self.label_objects:
            try:
                if hasattr(react_obj, 'Document') and react_obj.Document:
                    react_obj.Document.removeObject(react_obj.Name)
            except:
                pass
        
        self.reaction_objects.clear()
        self.label_objects.clear()

    def create_reaction_visualization(self, obj):
        """Create 3D visualization of reaction forces and moments."""
        if not self.fe_model:
            FreeCAD.Console.PrintError("No FE model available for reaction visualization\n")
            return
        
        model = self.fe_model
        
        # Print reaction information
        self.print_detailed_reaction_info(model)
        
        # Determine load combination to use
        load_combo = self.get_default_load_combination(model)
        
        # Create reaction labels for each supported node
        for node_name, node in model.nodes.items():
            if self.is_node_supported(node):
                # Convert Pynite coordinates to FreeCAD coordinate system
                # Pynite: X (horizontal), Y (vertical), Z (depth)  
                # FreeCAD: X (horizontal), Y (depth), Z (vertical)
                # Coordinate conversion: FreeCAD.X = Pynite.X, FreeCAD.Y = Pynite.Z, FreeCAD.Z = Pynite.Y
                
                # Check if coordinates need unit conversion
                pynite_x = node.X * 1000 if abs(node.X) < 100 else node.X  # Convert to mm if in meters
                pynite_y = node.Y * 1000 if abs(node.Y) < 100 else node.Y  
                pynite_z = node.Z * 1000 if abs(node.Z) < 100 else node.Z  
                
                # Map to FreeCAD coordinate system
                freecad_x = pynite_x  # X remains same
                freecad_y = pynite_z  # Y becomes Pynite's Z (depth)
                freecad_z = pynite_y  # Z becomes Pynite's Y (vertical)
                
                node_pos = FreeCAD.Vector(freecad_x, freecad_y, freecad_z)
                display_coords = (pynite_x, pynite_y, pynite_z)
                
                # Collect reaction values using safe access method
                reaction_components = []
                
                # Get reaction values safely
                rx = self.get_reaction_value(node, 'RxnFX', load_combo)
                ry = self.get_reaction_value(node, 'RxnFY', load_combo)
                rz = self.get_reaction_value(node, 'RxnFZ', load_combo)
                mx = self.get_reaction_value(node, 'RxnMX', load_combo)
                my = self.get_reaction_value(node, 'RxnMY', load_combo)
                mz = self.get_reaction_value(node, 'RxnMZ', load_combo)
                
                # Force components - check if they should be displayed
                if obj.ShowReactionFX and abs(rx) > obj.MinReactionThreshold:
                    reaction_components.append(f"Fx={rx:.{obj.Precision}f}")
                    
                if obj.ShowReactionFY and abs(ry) > obj.MinReactionThreshold:
                    reaction_components.append(f"Fy={ry:.{obj.Precision}f}")
                    
                if obj.ShowReactionFZ and abs(rz) > obj.MinReactionThreshold:
                    reaction_components.append(f"Fz={rz:.{obj.Precision}f}")
                
                # Moment components
                if obj.ShowReactionMX and abs(mx) > obj.MinReactionThreshold:
                    reaction_components.append(f"Mx={mx:.{obj.Precision}f}")
                    
                if obj.ShowReactionMY and abs(my) > obj.MinReactionThreshold:
                    reaction_components.append(f"My={my:.{obj.Precision}f}")
                    
                if obj.ShowReactionMZ and abs(mz) > obj.MinReactionThreshold:
                    reaction_components.append(f"Mz={mz:.{obj.Precision}f}")
                
                # Create combined label for this node
                if obj.ShowLabels and reaction_components:
                    self.create_combined_reaction_label(obj, node_pos, reaction_components, node_name, display_coords)

    def get_default_load_combination(self, model):
        """Get the default load combination to use for displaying reactions."""
        # Check if any node has dictionary-type reactions
        for node in model.nodes.values():
            if self.is_node_supported(node):
                for attr in ['RxnFX', 'RxnFY', 'RxnFZ', 'RxnMX', 'RxnMY', 'RxnMZ']:
                    if hasattr(node, attr):
                        reaction_data = getattr(node, attr)
                        if isinstance(reaction_data, dict) and reaction_data:
                            # Return the first available load combination
                            return list(reaction_data.keys())[0]
        return None

    def get_reaction_value(self, node, reaction_attr, load_combo=None):
        """Safely get reaction value, handling both dict and float formats."""
        if not hasattr(node, reaction_attr):
            return 0.0
            
        reaction_data = getattr(node, reaction_attr)
        
        # If it's a dictionary (load combinations), get the value
        if isinstance(reaction_data, dict):
            if load_combo and load_combo in reaction_data:
                return reaction_data[load_combo]
            elif reaction_data:
                # If no specific load combo specified, try common keys
                for key in ['Combo 1', 'LC 1', '1', 'DL', 'Dead Load']:
                    if key in reaction_data:
                        return reaction_data[key]
                # If none found, return first value
                return list(reaction_data.values())[0]
            else:
                return 0.0
        # If it's a simple float/number
        elif isinstance(reaction_data, (int, float)):
            return float(reaction_data)
        else:
            return 0.0

    def print_detailed_reaction_info(self, model):
        """Print detailed reaction information."""
        try:
            FreeCAD.Console.PrintMessage("\n=== REACTION RESULTS ===\n")
            
            # Count supported nodes
            supported_nodes = []
            for node_name, node in model.nodes.items():
                if self.is_node_supported(node):
                    supported_nodes.append((node_name, node))
            
            FreeCAD.Console.PrintMessage(f"Found {len(supported_nodes)} supported nodes\n")
            
            # Check what load combinations exist
            load_combos = set()
            for node_name, node in supported_nodes:
                for attr in ['RxnFX', 'RxnFY', 'RxnFZ', 'RxnMX', 'RxnMY', 'RxnMZ']:
                    if hasattr(node, attr):
                        reaction_data = getattr(node, attr)
                        if isinstance(reaction_data, dict):
                            load_combos.update(reaction_data.keys())
            
            # Use first load combination if any exist
            load_combo = list(load_combos)[0] if load_combos else None
            if load_combo:
                FreeCAD.Console.PrintMessage(f"Using load combination: {load_combo}\n")
                FreeCAD.Console.PrintMessage(f"Available load combinations: {list(load_combos)}\n")
            
            # Initialize sums for total reactions
            sum_fx = sum_fy = sum_fz = 0.0
            sum_mx = sum_my = sum_mz = 0.0
            
            # Process each supported node
            for node_name, node in supported_nodes:
                # Get reaction values safely
                rx = self.get_reaction_value(node, 'RxnFX', load_combo)
                ry = self.get_reaction_value(node, 'RxnFY', load_combo)
                rz = self.get_reaction_value(node, 'RxnFZ', load_combo)
                mx = self.get_reaction_value(node, 'RxnMX', load_combo)
                my = self.get_reaction_value(node, 'RxnMY', load_combo)
                mz = self.get_reaction_value(node, 'RxnMZ', load_combo)
                
                # Add to totals
                sum_fx += rx
                sum_fy += ry
                sum_fz += rz
                sum_mx += mx
                sum_my += my
                sum_mz += mz
                
                # Print node reactions
                FreeCAD.Console.PrintMessage(f"Node {node_name}: FX={rx:.3f}, FY={ry:.3f}, FZ={rz:.3f}, MX={mx:.3f}, MY={my:.3f}, MZ={mz:.3f}\n")
                
                # Print support conditions
                support_conditions = []
                if hasattr(node, 'support_DX') and node.support_DX: support_conditions.append("DX")
                if hasattr(node, 'support_DY') and node.support_DY: support_conditions.append("DY")
                if hasattr(node, 'support_DZ') and node.support_DZ: support_conditions.append("DZ")
                if hasattr(node, 'support_RX') and node.support_RX: support_conditions.append("RX")
                if hasattr(node, 'support_RY') and node.support_RY: support_conditions.append("RY")
                if hasattr(node, 'support_RZ') and node.support_RZ: support_conditions.append("RZ")
                FreeCAD.Console.PrintMessage(f"  Support conditions: {', '.join(support_conditions)}\n")
                
                # Print node coordinates
                FreeCAD.Console.PrintMessage(f"  Coordinates: ({node.X:.3f}, {node.Y:.3f}, {node.Z:.3f})\n")
                
                # Debug: Print reaction data types
                FreeCAD.Console.PrintMessage(f"  Debug - RxnFX type: {type(getattr(node, 'RxnFX', None))}\n")
                if hasattr(node, 'RxnFX'):
                    rxn_fx = getattr(node, 'RxnFX')
                    if isinstance(rxn_fx, dict):
                        FreeCAD.Console.PrintMessage(f"  Debug - RxnFX keys: {list(rxn_fx.keys())}\n")
            
            # Print total reactions
            FreeCAD.Console.PrintMessage(f"Total reactions - FX: {sum_fx:.3f}, FY: {sum_fy:.3f}, FZ: {sum_fz:.3f}\n")
            FreeCAD.Console.PrintMessage(f"Total moments - MX: {sum_mx:.3f}, MY: {sum_my:.3f}, MZ: {sum_mz:.3f}\n")
            FreeCAD.Console.PrintMessage("========================\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error printing reaction info: {str(e)}\n")

    def is_node_supported(self, node) -> bool:
        """Check if a node has any support conditions."""
        support_attrs = ['support_DX', 'support_DY', 'support_DZ', 'support_RX', 'support_RY', 'support_RZ']
        return any(hasattr(node, attr) and getattr(node, attr) for attr in support_attrs)

    def create_combined_reaction_label(self, obj, position: FreeCAD.Vector, reaction_components: list, node_name: str, mm_coords: tuple = None):
        """Create a single combined text label for all reaction values at a node."""
        try:
            # Position label exactly at the node position
            label_position = position
            
            # Create display lines
            display_lines = []
            
            # Add position information in mm if provided
            if mm_coords:
                x_mm, y_mm, z_mm = mm_coords
                position_text = f"({x_mm:.0f}, {y_mm:.0f}, {z_mm:.0f}) mm"
                display_lines.append(position_text)
            
            # Add reaction components in organized order
            force_order = ['Fx', 'Fy', 'Fz']
            moment_order = ['Mx', 'My', 'Mz']
            
            # Add forces first
            for force_name in force_order:
                for component in reaction_components:
                    if component.startswith(force_name + '='):
                        display_lines.append(component + ' kN')
                        break
            
            # Add moments
            for moment_name in moment_order:
                for component in reaction_components:
                    if component.startswith(moment_name + '='):
                        # Only show significant moments
                        try:
                            value_str = component.split('=')[1]
                            value = float(value_str)
                            if abs(value) > 0.05:
                                display_lines.append(component + ' kN·m')
                        except:
                            display_lines.append(component + ' kN·m')
                        break
            
            # Create annotation
            label_obj = FreeCAD.ActiveDocument.addObject("App::Annotation", f"Reactions_{node_name}")
            label_obj.LabelText = display_lines
            label_obj.Position = label_position
            
            # Set appearance
            if hasattr(label_obj, 'ViewObject'):
                label_obj.ViewObject.FontSize = max(obj.LabelFontSize, 10)
                
                if hasattr(label_obj.ViewObject, 'TextColor'):
                    label_obj.ViewObject.TextColor = (0.0, 0.0, 0.0)  # Black text
                
                if hasattr(label_obj.ViewObject, 'ShowFrame'):
                    label_obj.ViewObject.ShowFrame = True
                if hasattr(label_obj.ViewObject, 'FrameColor'):
                    label_obj.ViewObject.FrameColor = (1.0, 1.0, 1.0, 0.95)  # White background
                    
                if hasattr(label_obj.ViewObject, 'Justification'):
                    label_obj.ViewObject.Justification = "Center"
            
            self.label_objects.append(label_obj)
            
        except Exception as e:
            logger.error(f"Combined label creation failed: {str(e)}")
            FreeCAD.Console.PrintError(f"Could not create reaction label: {str(e)}\n")

    def onChanged(self, obj, prop):
        """Handle property changes."""
        if prop in ["ShowReactionFX", "ShowReactionFY", "ShowReactionFZ", 
                    "ShowReactionMX", "ShowReactionMY", "ShowReactionMZ",
                    "ShowLabels", "LabelFontSize", "Precision", 
                    "MinReactionThreshold"]:
            try:
                self.execute(obj)
            except Exception as e:
                FreeCAD.Console.PrintError(f"Error updating display: {str(e)}\n")


class ViewProviderReactionResults:
    """View provider for reaction results."""
    
    def __init__(self, vobj):
        vobj.Proxy = self
    
    def getIcon(self):
        return os.path.join(ICONPATH, "reaction.svg")
    
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
    
    def updateData(self, obj, prop):
        """Update visualization when properties change."""
        if prop in ["ShowReactionFX", "ShowReactionFY", "ShowReactionFZ", 
                   "ShowReactionMX", "ShowReactionMY", "ShowReactionMZ",
                   "ShowLabels"]:
            if hasattr(obj, 'Proxy') and obj.Proxy:
                obj.Proxy.execute(obj)

    def onChanged(self, vobj, prop):
        pass
    
    def getDisplayModes(self, obj):
        return []
    
    def getDefaultDisplayMode(self):
        return "Shaded"
    
    def setDisplayMode(self, mode):
        return mode


class CommandReactionResults:
    """Command to create reaction results visualization."""
    
    def GetResources(self):
        return {
            'Pixmap': os.path.join(ICONPATH, "icons/reaction.svg"),
            'MenuText': "Reaction Results", 
            'ToolTip': "Display reaction forces and moments at support points"
        }
    
    def Activated(self):
        try:
            # Check if a calculation object is selected
            selection = FreeCADGui.Selection.getSelection()
            calc_obj = None
            
            for obj in selection:
                if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, '__class__'):
                    if 'Calc' in obj.Proxy.__class__.__name__:
                        calc_obj = obj
                        break
            
            if not calc_obj:
                # Try to find calc object in document
                for obj in FreeCAD.ActiveDocument.Objects:
                    if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, '__class__'):
                        if 'Calc' in obj.Proxy.__class__.__name__:
                            calc_obj = obj
                            break
            
            if not calc_obj:
                QtWidgets.QMessageBox.warning(None, "Warning", 
                    "Please select or create a calculation object first.")
                return
            
            # Check if calc has elements
            if not hasattr(calc_obj, 'ListElements') or not calc_obj.ListElements:
                QtWidgets.QMessageBox.warning(None, "Warning", 
                    "The calculation object has no elements. Please set up the structural model first.")
                return
            
            # Create reaction results object
            reaction_obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", "ReactionResults")
            ReactionResults(reaction_obj, calc_obj)
            ViewProviderReactionResults(reaction_obj.ViewObject)
            
            FreeCAD.ActiveDocument.recompute()
            
        except Exception as e:
            logger.error(f"Error in CommandReactionResults.Activated: {str(e)}")
            QtWidgets.QMessageBox.critical(None, "Error", f"Failed to create reaction results: {str(e)}")
    
    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


# Register the command
if hasattr(FreeCADGui, 'addCommand'):
    FreeCADGui.addCommand('ReactionResults', CommandReactionResults())