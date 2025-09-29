import FreeCAD, FreeCADGui
import os
from typing import List, Dict, Any, Optional
import csv

# Prefer PySide2 when available
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    try:
        from PySide import QtWidgets, QtCore, QtGui
    except ImportError as e:
        raise ImportError("Neither PySide2 nor PySide could be imported. Please install one of them.") from e

ICONPATH = os.path.join(os.path.dirname(__file__), "resources")


class ReactionTablePanel:
    """Compact panel for displaying reaction results in a table format with export functionality."""
    
    def __init__(self, reaction_obj):
        self.reaction_obj = reaction_obj
        self.form = self.create_ui()
        self.setup_connections()
        self._populating = False  # Recursion guard
        self.populate_reaction_table()
    
    def create_ui(self):
        """Create a compact user interface for the reaction table panel."""
        # Main widget
        widget = QtWidgets.QWidget()
        widget.setMinimumSize(800, 500)
        widget.setMaximumSize(1200, 700)
        main_layout = QtWidgets.QVBoxLayout(widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # --- Header (title + load combo only) ---
        header_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Reaction Results")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        header_layout.addWidget(QtWidgets.QLabel("Load Combo:"))
        self.load_combo_dropdown = QtWidgets.QComboBox()
        self.load_combo_dropdown.setMinimumWidth(120)
        self.load_combo_dropdown.setMaximumWidth(150)
        header_layout.addWidget(self.load_combo_dropdown)
        main_layout.addLayout(header_layout)

        # --- Table for reaction results ---
        self.table_widget = QtWidgets.QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f8f9fa;
                background-color: white;
                gridline-color: #dee2e6;
                font-size: 9px;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                font-weight: bold;
                font-size: 9px;
                padding: 3px;
            }
        """)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        main_layout.addWidget(self.table_widget, stretch=1)

        # --- Status bar ---
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #27ae60; font-size: 9px; padding: 2px;")
        main_layout.addWidget(self.status_label)

        # --- Footer with OK/Cancel and Export/Refresh ---
        footer_layout = QtWidgets.QVBoxLayout()

        # Button row for OK/Cancel
        ok_cancel_layout = QtWidgets.QHBoxLayout()
        ok_cancel_layout.addStretch()
        self.ok_button = QtWidgets.QPushButton("OK")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        ok_cancel_layout.addWidget(self.ok_button)
        ok_cancel_layout.addWidget(self.cancel_button)
        footer_layout.addLayout(ok_cancel_layout)

        # Second row for CSV/TXT/Refresh
        export_layout = QtWidgets.QHBoxLayout()
        export_layout.addStretch()
        self.export_csv_button = QtWidgets.QPushButton("CSV")
        self.export_csv_button.setMaximumWidth(60)
        self.export_txt_button = QtWidgets.QPushButton("TXT")
        self.export_txt_button.setMaximumWidth(60)
        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.setMaximumWidth(80)
        export_layout.addWidget(self.export_csv_button)
        export_layout.addWidget(self.export_txt_button)
        export_layout.addWidget(self.refresh_button)
        footer_layout.addLayout(export_layout)

        main_layout.addLayout(footer_layout)

        return widget

    
    def setup_connections(self):
        """Connect UI elements to their handlers."""
        self.load_combo_dropdown.currentTextChanged.connect(self.on_load_combination_changed)
        self.refresh_button.clicked.connect(self.populate_reaction_table)
        self.export_csv_button.clicked.connect(lambda: self.export_to_format("csv"))
        self.export_txt_button.clicked.connect(lambda: self.export_to_format("txt"))
    
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
    
    def populate_load_combinations(self, model):
        """Populate the load combination dropdown from model."""
        self.load_combo_dropdown.clear()
        
        # Get load combinations from nodes
        load_combos = set()
        for node in model.nodes.values():
            if self.is_node_supported(node):
                for attr in ['RxnFX', 'RxnFY', 'RxnFZ', 'RxnMX', 'RxnMY', 'RxnMZ']:
                    if hasattr(node, attr):
                        reaction_data = getattr(node, attr)
                        if isinstance(reaction_data, dict):
                            load_combos.update(reaction_data.keys())
        
        if load_combos:
            combo_list = sorted(list(load_combos))
            self.load_combo_dropdown.addItems(combo_list)
            return combo_list[0]  # Return first combo as default
        else:
            # No load combinations found, add default
            self.load_combo_dropdown.addItem("Default")
            return None
    
    def populate_reaction_table(self):
        """Populate the reaction table with data."""
        if self._populating:
            return
        
        try:
            self._populating = True
            self.table_widget.clear()
            
            if not self.reaction_obj or not self.reaction_obj.ObjectBaseCalc:
                self.status_label.setText("No calculation object linked")
                self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                return
            
            # Get the FE model from calc object
            calc_obj = self.reaction_obj.ObjectBaseCalc
            
            # Try to get the model using the same approach as ReactionResults
            if hasattr(calc_obj, 'Proxy') and calc_obj.Proxy:
                try:
                    # Import the FE model class
                    from .Pynite_main.FEModel3D import FEModel3D
                    
                    # Recreate the model using calc's methods
                    calc_proxy = calc_obj.Proxy
                    model = FEModel3D()
                    
                    # Filter elements
                    lines = list(filter(lambda element: 'Line' in element.Name or 'Wire' in element.Name, calc_obj.ListElements))
                    loads = list(filter(lambda element: 'Load' in element.Name, calc_obj.ListElements))
                    supports = list(filter(lambda element: 'Suport' in element.Name, calc_obj.ListElements))
                    
                    if not lines or not supports:
                        self.status_label.setText("No structural elements or supports found")
                        self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                        return
                    
                    # Build the model using calc's methods
                    nodes_map = calc_proxy.mapNodes(lines, calc_obj.LengthUnit)
                    members_map = calc_proxy.mapMembers(lines, nodes_map, calc_obj.LengthUnit)
                    
                    model = calc_proxy.setMaterialAndSections(model, lines, calc_obj.LengthUnit, calc_obj.ForceUnit)
                    model = calc_proxy.setNodes(model, nodes_map)
                    model = calc_proxy.setMembers(model, members_map, calc_obj.selfWeight)
                    model = calc_proxy.setLoads(model, loads, nodes_map, calc_obj.ForceUnit, calc_obj.LengthUnit)
                    model = calc_proxy.setSuports(model, supports, nodes_map, calc_obj.LengthUnit)
                    
                    # Run the analysis
                    model.analyze()
                    
                except Exception as e:
                    self.status_label.setText(f"Error creating FE model: {str(e)}")
                    self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                    return
            else:
                self.status_label.setText("No calculation proxy found")
                self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                return
            
            if not model or not hasattr(model, 'nodes') or not model.nodes:
                self.status_label.setText("No nodes found in model")
                self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                return
            
            # Populate load combinations
            default_combo = self.populate_load_combinations(model)
            
            # Get current load combination
            load_combo = self.load_combo_dropdown.currentText()
            if load_combo == "Default":
                load_combo = default_combo
            
            # Prepare table data
            table_data = []
            headers = ["Node", "X", "Y", "Z", "FX", "FY", "FZ", "MX", "MY", "MZ"]
            
            # Get supported nodes and their reactions
            for node_name, node in model.nodes.items():
                if self.is_node_supported(node):
                    # Get reaction values safely
                    rx = self.get_reaction_value(node, 'RxnFX', load_combo)
                    ry = self.get_reaction_value(node, 'RxnFY', load_combo)
                    rz = self.get_reaction_value(node, 'RxnFZ', load_combo)
                    mx = self.get_reaction_value(node, 'RxnMX', load_combo)
                    my = self.get_reaction_value(node, 'RxnMY', load_combo)
                    mz = self.get_reaction_value(node, 'RxnMZ', load_combo)
                    
                    # Convert coordinates (adjust for unit scaling)
                    x_pos = node.X * 1000 if abs(node.X) < 100 else node.X
                    y_pos = node.Y * 1000 if abs(node.Y) < 100 else node.Y
                    z_pos = node.Z * 1000 if abs(node.Z) < 100 else node.Z
                    
                    # Add row data with compact formatting
                    row_data = [
                        node_name,
                        f"{x_pos:.1f}",
                        f"{y_pos:.1f}",
                        f"{z_pos:.1f}",
                        f"{rx:.3f}",
                        f"{ry:.3f}",
                        f"{rz:.3f}",
                        f"{mx:.3f}",
                        f"{my:.3f}",
                        f"{mz:.3f}"
                    ]
                    
                    table_data.append(row_data)
            
            # Sort by node name
            table_data.sort(key=lambda x: x[0])
            
            # Set up table
            self.table_widget.setRowCount(len(table_data))
            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels(headers)
            
            # Populate table with data
            for row_idx, row_data in enumerate(table_data):
                for col_idx, cell_data in enumerate(row_data):
                    item = QtWidgets.QTableWidgetItem(str(cell_data))
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    # Right align numeric columns
                    if col_idx > 0:
                        item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                    self.table_widget.setItem(row_idx, col_idx, item)
            
            # Adjust column sizes for compact display
            self.table_widget.resizeColumnsToContents()
            for i in range(self.table_widget.columnCount()):
                current_width = self.table_widget.columnWidth(i)
                # Cap maximum column width for compact display
                max_width = 80 if i == 0 else 60  # Node column wider, others narrower
                self.table_widget.setColumnWidth(i, min(current_width, max_width))
            
            # Store model and load combo for export
            self.current_model = model
            self.current_load_combo = load_combo
            
            # Update status
            self.status_label.setText(f"{len(table_data)} supported nodes | Load: {load_combo}")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 9px;")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error populating reaction table: {str(e)}\n")
            self.status_label.setText(f"Error: {str(e)[:50]}...")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
        finally:
            self._populating = False
    
    def is_node_supported(self, node) -> bool:
        """Check if a node has any support conditions."""
        support_attrs = ['support_DX', 'support_DY', 'support_DZ', 'support_RX', 'support_RY', 'support_RZ']
        return any(hasattr(node, attr) and getattr(node, attr) for attr in support_attrs)
    
    def on_load_combination_changed(self, combo_name):
        """Handle load combination selection change."""
        if not self._populating:
            self.populate_reaction_table()
    
    def export_to_format(self, format_type: str):
        """Export reaction results to specified format."""
        try:
            # Get file extension and filter based on format
            if format_type == "csv":
                file_filter = "CSV Files (*.csv);;All Files (*)"
                default_ext = ".csv"
            else:  # txt
                file_filter = "Text Files (*.txt);;All Files (*)"
                default_ext = ".txt"
            
            # Get file path from user
            file_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
                self.form, 
                f"Export Reaction Results", 
                f"reactions_{self.current_load_combo if hasattr(self, 'current_load_combo') else 'data'}{default_ext}", 
                file_filter
            )
            
            if not file_path:
                return
            
            # Ensure file has correct extension
            if not file_path.lower().endswith(default_ext):
                file_path += default_ext
            
            # Export based on format
            if format_type == "csv":
                success = self.export_to_csv(file_path)
            else:  # txt
                success = self.export_to_txt(file_path)
            
            if success:
                self.status_label.setText(f"Exported to: {os.path.basename(file_path)}")
                self.status_label.setStyleSheet("color: #27ae60; font-size: 9px;")
            else:
                self.status_label.setText("Export failed")
                self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
                
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error exporting reaction results: {str(e)}\n")
            self.status_label.setText(f"Export error")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
    
    def export_to_csv(self, file_path: str) -> bool:
        """Export reaction results to CSV file."""
        try:
            load_combo = getattr(self, 'current_load_combo', 'Unknown')
            
            # Get table data
            headers = []
            for col in range(self.table_widget.columnCount()):
                headers.append(self.table_widget.horizontalHeaderItem(col).text())
            
            rows = []
            for row in range(self.table_widget.rowCount()):
                row_data = []
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    row_data.append(item.text() if item else "")
                rows.append(row_data)
            
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header info
                writer.writerow([f"Reaction Results - Load Combination: {load_combo}"])
                writer.writerow([f"Units: Forces in kN, Moments in kN·m, Coordinates in mm"])
                writer.writerow([])
                
                # Write column headers
                writer.writerow(headers)
                
                # Write data
                writer.writerows(rows)
                
                # Write summary
                writer.writerow([])
                writer.writerow([f"Total Supported Nodes: {len(rows)}"])
                
                # Calculate totals
                total_fx = total_fy = total_fz = 0.0
                for row in rows:
                    try:
                        total_fx += float(row[4])  # FX column
                        total_fy += float(row[5])  # FY column
                        total_fz += float(row[6])  # FZ column
                    except (ValueError, IndexError):
                        pass
                
                writer.writerow([f"Total FX: {total_fx:.3f} kN"])
                writer.writerow([f"Total FY: {total_fy:.3f} kN"])
                writer.writerow([f"Total FZ: {total_fz:.3f} kN"])
            
            return True
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error exporting to CSV: {str(e)}\n")
            return False
    
    def export_to_txt(self, file_path: str) -> bool:
        """Export reaction results to formatted text file."""
        try:
            load_combo = getattr(self, 'current_load_combo', 'Unknown')
            
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                # Write header
                txtfile.write("="*80 + "\n")
                txtfile.write("REACTION FORCES AND MOMENTS REPORT\n")
                txtfile.write("="*80 + "\n")
                txtfile.write(f"Load Combination: {load_combo}\n")
                txtfile.write(f"Units: Forces in kN, Moments in kN·m, Coordinates in mm\n")
                txtfile.write(f"Generated by FreeCAD Structure Tools\n")
                txtfile.write("-"*80 + "\n\n")
                
                # Calculate totals first
                total_fx = total_fy = total_fz = 0.0
                total_mx = total_my = total_mz = 0.0
                node_count = 0
                
                # Write node data and calculate totals
                for row in range(self.table_widget.rowCount()):
                    node_name = self.table_widget.item(row, 0).text()
                    x_coord = self.table_widget.item(row, 1).text()
                    y_coord = self.table_widget.item(row, 2).text()
                    z_coord = self.table_widget.item(row, 3).text()
                    fx = self.table_widget.item(row, 4).text()
                    fy = self.table_widget.item(row, 5).text()
                    fz = self.table_widget.item(row, 6).text()
                    mx = self.table_widget.item(row, 7).text()
                    my = self.table_widget.item(row, 8).text()
                    mz = self.table_widget.item(row, 9).text()
                    
                    # Write node info
                    txtfile.write(f"Node {node_name}:\n")
                    txtfile.write(f"  Coordinates: ({x_coord}, {y_coord}, {z_coord}) mm\n")
                    txtfile.write(f"  Reaction Forces:  FX = {fx:>8} kN    FY = {fy:>8} kN    FZ = {fz:>8} kN\n")
                    txtfile.write(f"  Reaction Moments: MX = {mx:>8} kN·m  MY = {my:>8} kN·m  MZ = {mz:>8} kN·m\n")
                    
                    # Get support conditions from model if available
                    if hasattr(self, 'current_model') and self.current_model:
                        try:
                            node_obj = self.current_model.nodes[node_name]
                            supports = []
                            if hasattr(node_obj, 'support_DX') and node_obj.support_DX: supports.append("DX")
                            if hasattr(node_obj, 'support_DY') and node_obj.support_DY: supports.append("DY")
                            if hasattr(node_obj, 'support_DZ') and node_obj.support_DZ: supports.append("DZ")
                            if hasattr(node_obj, 'support_RX') and node_obj.support_RX: supports.append("RX")
                            if hasattr(node_obj, 'support_RY') and node_obj.support_RY: supports.append("RY")
                            if hasattr(node_obj, 'support_RZ') and node_obj.support_RZ: supports.append("RZ")
                            if supports:
                                txtfile.write(f"  Support Conditions: {', '.join(supports)}\n")
                        except:
                            pass
                    
                    txtfile.write("\n")
                    
                    # Add to totals
                    try:
                        total_fx += float(fx)
                        total_fy += float(fy)
                        total_fz += float(fz)
                        total_mx += float(mx)
                        total_my += float(my)
                        total_mz += float(mz)
                        node_count += 1
                    except ValueError:
                        pass
                
                # Write summary
                txtfile.write("-"*80 + "\n")
                txtfile.write("SUMMARY\n")
                txtfile.write("-"*80 + "\n")
                txtfile.write(f"Total Supported Nodes: {node_count}\n")
                txtfile.write(f"Total Reaction Forces:\n")
                txtfile.write(f"  Sum FX = {total_fx:>10.3f} kN\n")
                txtfile.write(f"  Sum FY = {total_fy:>10.3f} kN\n")
                txtfile.write(f"  Sum FZ = {total_fz:>10.3f} kN\n")
                txtfile.write(f"Total Reaction Moments:\n")
                txtfile.write(f"  Sum MX = {total_mx:>10.3f} kN·m\n")
                txtfile.write(f"  Sum MY = {total_my:>10.3f} kN·m\n")
                txtfile.write(f"  Sum MZ = {total_mz:>10.3f} kN·m\n")
                
                # Equilibrium check
                txtfile.write("\nEquilibrium Check:\n")
                txtfile.write(f"  Force equilibrium should sum to zero (within numerical tolerance)\n")
                txtfile.write(f"  Moment equilibrium should sum to zero (within numerical tolerance)\n")
                txtfile.write("="*80 + "\n")
            
            return True
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error exporting to TXT: {str(e)}\n")
            return False
    
    def accept(self):
        """Accept and close panel."""
        FreeCADGui.Control.closeDialog()
    
    def reject(self):
        """Reject and close panel."""
        FreeCADGui.Control.closeDialog()
    
    def getStandardButtons(self):
        """Return standard buttons for the panel."""
        return int(QtWidgets.QDialogButtonBox.Ok)


class CommandReactionTablePanel:
    """Command to open reaction results table panel."""
    
    def GetResources(self):
        return {
            'Pixmap': os.path.join(ICONPATH, "icons/reaction_table.svg"),
            'MenuText': "Reaction Table", 
            'ToolTip': "Display reaction forces and moments in a compact table"
        }
    
    def Activated(self):
        try:
            # Find calc object
            calc_obj = None
            selection = FreeCADGui.Selection.getSelection()
            
            # Check selection first
            for obj in selection:
                if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, '__class__'):
                    if 'Calc' in obj.Proxy.__class__.__name__:
                        calc_obj = obj
                        break
            
            # If not found in selection, search document
            if not calc_obj:
                for obj in FreeCAD.ActiveDocument.Objects:
                    if hasattr(obj, 'Proxy') and hasattr(obj.Proxy, '__class__'):
                        if 'Calc' in obj.Proxy.__class__.__name__:
                            calc_obj = obj
                            break
            
            if not calc_obj:
                QtWidgets.QMessageBox.warning(None, "Warning", 
                    "Please create and run a structural calculation first.")
                return
            
            # Check if calc has elements
            if not hasattr(calc_obj, 'ListElements') or not calc_obj.ListElements:
                QtWidgets.QMessageBox.warning(None, "Warning", 
                    "The calculation object has no elements. Please set up the structural model first.")
                return
            
            # Create a temporary reaction results object for the panel
            class TempReactionObj:
                def __init__(self, calc_obj):
                    self.ObjectBaseCalc = calc_obj
            
            temp_reaction_obj = TempReactionObj(calc_obj)
            
            # Open the panel
            panel = ReactionTablePanel(temp_reaction_obj)
            FreeCADGui.Control.showDialog(panel)
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error opening reaction table panel: {str(e)}\n")
            QtWidgets.QMessageBox.critical(None, "Error", f"Failed to open reaction table: {str(e)}")
    
    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


# Register the command
if hasattr(FreeCADGui, 'addCommand'):
    FreeCADGui.addCommand('ReactionTablePanel', CommandReactionTablePanel())