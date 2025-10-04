"""
FreeCAD Frame3DD Structure Importer
Imports nodes, members, and restraints from Frame3DD .3DD files
Author: Refactored version
"""

import FreeCAD
import FreeCADGui
import os
import shutil
from PySide import QtGui, QtCore
from PySide.QtGui import QFileDialog


class Node:
    """Represents a structural node with 3D coordinates"""
    def __init__(self, node_id, x, y, z):
        self.id = str(node_id)
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class Member:
    """Represents a structural member connecting two nodes"""
    def __init__(self, member_id, node1_id, node2_id):
        self.id = str(member_id)
        self.n1 = str(node1_id)
        self.n2 = str(node2_id)


class Restraint:
    """Represents nodal restraints (fixed DOF)"""
    def __init__(self, node_id, rx=0, ry=0, rz=0, rxx=0, ryy=0, rzz=0):
        self.node_id = str(node_id)
        self.rx = int(rx)   # 1=fixed, 0=free in X direction
        self.ry = int(ry)   # 1=fixed, 0=free in Y direction
        self.rz = int(rz)   # 1=fixed, 0=free in Z direction
        self.rxx = int(rxx) # 1=fixed, 0=free rotation about X
        self.ryy = int(ryy) # 1=fixed, 0=free rotation about Y
        self.rzz = int(rzz) # 1=fixed, 0=free rotation about Z


class Frame3DDParser:
    """Parses Frame3DD .3DD files and extracts structural data"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.nodes = {}
        self.members = {}
        self.restraints = {}
        self.scale_factor = 1.0
        
    def skip_to_data(self, fp):
        """Skip empty lines and comments, return next data line"""
        while True:
            line = fp.readline().strip()
            if not line or line.startswith('#'):
                continue
            return line
    
    def parse_nodes(self, fp, num_nodes):
        """Parse node coordinates from file"""
        print(f"Parsing {num_nodes} nodes...")
        
        for i in range(num_nodes):
            line = self.skip_to_data(fp)
            data = line.split()
            
            if len(data) < 4:
                print(f"Warning: Invalid node data at line: {line}")
                continue
                
            node_id = data[0]
            x, y, z = float(data[1]), float(data[2]), float(data[3])
            self.nodes[node_id] = Node(node_id, x, y, z)
            
        print(f"Successfully parsed {len(self.nodes)} nodes")
    
    def parse_restraints(self, fp, num_restraints):
        """Parse restraint conditions from file"""
        print(f"Parsing {num_restraints} restraints...")
        
        for i in range(num_restraints):
            line = self.skip_to_data(fp)
            data = line.split()
            
            if len(data) < 7:
                print(f"Warning: Invalid restraint data at line: {line}")
                continue
            
            node_id = data[0]
            rx, ry, rz = int(data[1]), int(data[2]), int(data[3])
            rxx, ryy, rzz = int(data[4]), int(data[5]), int(data[6])
            
            self.restraints[node_id] = Restraint(node_id, rx, ry, rz, rxx, ryy, rzz)
            
        print(f"Successfully parsed {len(self.restraints)} restraints")
    
    def parse_members(self, fp, num_members):
        """Parse member connectivity from file"""
        print(f"Parsing {num_members} members...")
        
        for i in range(num_members):
            line = self.skip_to_data(fp)
            data = line.split()
            
            if len(data) < 3:
                print(f"Warning: Invalid member data at line: {line}")
                continue
            
            member_id = data[0]
            n1, n2 = data[1], data[2]
            self.members[member_id] = Member(member_id, n1, n2)
            
        print(f"Successfully parsed {len(self.members)} members")
    
    def parse_file(self):
        """Main parsing routine for .3DD file"""
        try:
            with open(self.filepath, 'r') as fp:
                # Skip title line
                line = self.skip_to_data(fp)
                print(f"Project: {line}")
                
                # Parse nodes
                line = self.skip_to_data(fp)
                num_nodes = int(line.split()[0])
                self.parse_nodes(fp, num_nodes)
                
                # Parse restraints
                line = self.skip_to_data(fp)
                num_restraints = int(line.split()[0])
                self.parse_restraints(fp, num_restraints)
                
                # Parse members
                line = self.skip_to_data(fp)
                num_members = int(line.split()[0])
                self.parse_members(fp, num_members)
                
            return True
            
        except Exception as e:
            print(f"Error parsing file: {str(e)}")
            return False
    
    def load_restraints_from_txt(self, txt_filepath):
        """Load additional restraints from a .txt file
        
        Format:
        # Node restraints (node_id rx ry rz rxx ryy rzz)
        1 1 1 1 0 0 0
        2 0 1 1 0 0 0
        """
        try:
            with open(txt_filepath, 'r') as fp:
                print(f"Loading restraints from: {txt_filepath}")
                
                for line in fp:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    data = line.split()
                    if len(data) < 7:
                        continue
                    
                    node_id = data[0]
                    rx, ry, rz = int(data[1]), int(data[2]), int(data[3])
                    rxx, ryy, rzz = int(data[4]), int(data[5]), int(data[6])
                    
                    self.restraints[node_id] = Restraint(node_id, rx, ry, rz, rxx, ryy, rzz)
                
                print(f"Loaded {len(self.restraints)} restraints from txt file")
                return True
                
        except Exception as e:
            print(f"Error loading restraints from txt: {str(e)}")
            return False


class Frame3DDImporter:
    """Creates FreeCAD objects from parsed Frame3DD data"""
    
    def __init__(self, parser):
        self.parser = parser
        self.scale = parser.scale_factor
        
    def create_nodes(self):
        """Create FreeCAD point objects for nodes"""
        import Draft
        
        # Create or clear nodes group
        grp_nodes = FreeCAD.ActiveDocument.getObject('Nodes')
        if grp_nodes:
            grp_nodes.removeObjectsFromDocument()
        else:
            FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "Nodes")
            grp_nodes = FreeCAD.ActiveDocument.getObject('Nodes')
        
        for node_id, node in self.parser.nodes.items():
            point = Draft.makePoint(
                node.x * self.scale,
                node.y * self.scale,
                node.z * self.scale
            )
            point.Label = f"N{node_id}"
            point.ViewObject.PointColor = (0.667, 0.0, 0.0)
            grp_nodes.addObject(point)
        
        print(f"Created {len(self.parser.nodes)} node objects")
    
    def create_members(self):
        """Create FreeCAD line objects for members"""
        import Draft
        from FreeCAD import Base
        
        # Create or clear members group
        grp_members = FreeCAD.ActiveDocument.getObject('Members')
        if grp_members:
            grp_members.removeObjectsFromDocument()
        else:
            FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "Members")
            grp_members = FreeCAD.ActiveDocument.getObject('Members')
        
        for member_id, member in self.parser.members.items():
            n1 = self.parser.nodes[member.n1]
            n2 = self.parser.nodes[member.n2]
            
            points = [
                Base.Vector(n1.x * self.scale, n1.y * self.scale, n1.z * self.scale),
                Base.Vector(n2.x * self.scale, n2.y * self.scale, n2.z * self.scale)
            ]
            
            wire = Draft.makeWire(points, closed=False, face=False, support=None)
            wire.Label = f"M{member_id}"
            grp_members.addObject(wire)
        
        print(f"Created {len(self.parser.members)} member objects")
    
    def create_restraints(self):
        """Create visual representations of restraints"""
        import Draft
        from FreeCAD import Base
        
        # Create or clear restraints group
        grp_restraints = FreeCAD.ActiveDocument.getObject('Restraints')
        if grp_restraints:
            grp_restraints.removeObjectsFromDocument()
        else:
            FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup", "Restraints")
            grp_restraints = FreeCAD.ActiveDocument.getObject('Restraints')
        
        symbol_size = 50.0 * self.scale
        
        for node_id, restraint in self.parser.restraints.items():
            if node_id not in self.parser.nodes:
                print(f"Warning: Restraint references non-existent node {node_id}")
                continue
            
            node = self.parser.nodes[node_id]
            base_point = Base.Vector(
                node.x * self.scale,
                node.y * self.scale,
                node.z * self.scale
            )
            
            # Create restraint symbol group
            restraint_grp = FreeCAD.ActiveDocument.addObject(
                "App::DocumentObjectGroup",
                f"R{node_id}"
            )
            grp_restraints.addObject(restraint_grp)
            
            # Draw restraint symbols based on fixed directions
            if restraint.rx == 1:  # Fixed in X
                self._draw_restraint_symbol(
                    restraint_grp, base_point, 'X', symbol_size, (1.0, 0.0, 0.0)
                )
            
            if restraint.ry == 1:  # Fixed in Y
                self._draw_restraint_symbol(
                    restraint_grp, base_point, 'Y', symbol_size, (0.0, 1.0, 0.0)
                )
            
            if restraint.rz == 1:  # Fixed in Z
                self._draw_restraint_symbol(
                    restraint_grp, base_point, 'Z', symbol_size, (0.0, 0.0, 1.0)
                )
            
            # Add label
            restraint_type = self._get_restraint_type(restraint)
            restraint_grp.Label = f"R{node_id}_{restraint_type}"
        
        print(f"Created {len(self.parser.restraints)} restraint objects")
    
    def _draw_restraint_symbol(self, parent_group, base_point, direction, size, color):
        """Draw a triangular restraint symbol"""
        import Draft
        from FreeCAD import Base
        
        offset = size * 0.3
        
        if direction == 'X':
            p1 = Base.Vector(base_point.x - offset, base_point.y, base_point.z)
            p2 = Base.Vector(p1.x - size*0.5, p1.y - size*0.3, p1.z)
            p3 = Base.Vector(p1.x - size*0.5, p1.y + size*0.3, p1.z)
        elif direction == 'Y':
            p1 = Base.Vector(base_point.x, base_point.y - offset, base_point.z)
            p2 = Base.Vector(p1.x - size*0.3, p1.y - size*0.5, p1.z)
            p3 = Base.Vector(p1.x + size*0.3, p1.y - size*0.5, p1.z)
        else:  # Z
            p1 = Base.Vector(base_point.x, base_point.y, base_point.z - offset)
            p2 = Base.Vector(p1.x - size*0.3, p1.y, p1.z - size*0.5)
            p3 = Base.Vector(p1.x + size*0.3, p1.y, p1.z - size*0.5)
        
        # Draw triangle
        points = [p1, p2, p3, p1]
        wire = Draft.makeWire(points, closed=True, face=True, support=None)
        wire.Label = f"Support_{direction}"
        wire.ViewObject.LineColor = color
        wire.ViewObject.ShapeColor = color
        parent_group.addObject(wire)
    
    def _get_restraint_type(self, restraint):
        """Determine restraint type description"""
        fixed = []
        if restraint.rx == 1:
            fixed.append('X')
        if restraint.ry == 1:
            fixed.append('Y')
        if restraint.rz == 1:
            fixed.append('Z')
        
        if len(fixed) == 3:
            return "Fixed"
        elif len(fixed) == 2:
            return f"Pin_{''.join(fixed)}"
        elif len(fixed) == 1:
            return f"Roller_{fixed[0]}"
        else:
            return "Free"
    
    def create_all(self):
        """Create all FreeCAD objects"""
        self.create_nodes()
        self.create_members()
        #self.create_restraints()
        
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.SendMsgToActiveView("ViewFit")


class Frame3DDImportCommand:
    """FreeCAD command to import Frame3DD files"""
    
    def GetResources(self):
        return {
            "MenuText": "Import Frame3DD Structure",
            "Accel": "Shift+F",
            "ToolTip": "Import nodes, members, and restraints from Frame3DD .3DD file",
            "Pixmap": os.path.join(os.path.dirname(__file__), "resources/icons/", "folder.svg")
        }
    
    def IsActive(self):
        return FreeCAD.ActiveDocument is not None
    
    def Activated(self):
        # File selection dialog
        default_path = os.path.expanduser("~")
        
        try:
            filename = QFileDialog.getOpenFileName(
                None,
                QString.fromLocal8Bit("Select Frame3DD .3DD file"),
                default_path,
                "Frame3DD files (*.3DD);;All files (*.*)"
            )
            if isinstance(filename, tuple):
                filename = filename[0]
        except:
            filename, _ = QtGui.QFileDialog.getOpenFileName(
                None,
                "Select Frame3DD .3DD file",
                default_path,
                "Frame3DD files (*.3DD);;All files (*.*)"
            )
        
        if not filename:
            print("Import cancelled")
            return
        
        print(f"Importing: {filename}")
        
        # Parse the file
        parser = Frame3DDParser(filename)
        if not parser.parse_file():
            QtGui.QMessageBox.critical(
                None,
                "Import Error",
                "Failed to parse Frame3DD file. Check console for details."
            )
            return
        
        # Check for additional restraints file
        txt_file = filename.replace('.3DD', '_restraints.txt').replace('.3dd', '_restraints.txt')
        if os.path.exists(txt_file):
            reply = QtGui.QMessageBox.question(
                None,
                "Additional Restraints Found",
                f"Found restraints file:\n{txt_file}\n\nLoad these restraints?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            )
            if reply == QtGui.QMessageBox.Yes:
                parser.load_restraints_from_txt(txt_file)
        
        # Create FreeCAD objects
        importer = Frame3DDImporter(parser)
        importer.create_all()
        
        print("Import completed successfully!")
        QtGui.QMessageBox.information(
            None,
            "Import Complete",
            f"Successfully imported:\n"
            f"- {len(parser.nodes)} nodes\n"
            f"- {len(parser.members)} members\n"
            #f"- {len(parser.restraints)} restraints"
        )


# Register the command
FreeCADGui.addCommand('Frame3DD_Import', Frame3DDImportCommand())