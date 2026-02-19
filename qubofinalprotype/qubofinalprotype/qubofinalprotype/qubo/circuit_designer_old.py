"""
Visual Quantum Circuit Designer - Drag & Drop Interface
Similar to draw.io but for quantum circuits
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QLabel, QPushButton, QFrame, QSplitter, QToolBar,
    QAction, QSpinBox, QComboBox, QGraphicsView, QGraphicsScene,
    QGraphicsItem, QGraphicsPixmapItem, QGraphicsTextItem,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem,
    QMenu, QFileDialog, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QMimeData, QPoint, QRect, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QDrag, QPainter, QPixmap, QFont, QPen, QBrush, QColor, 
    QIcon, QCursor, QPainterPath, QPolygonF, QLinearGradient, QRadialGradient
)
import json
import os

# IDE Theme Colors (matching the main GUI)
GATE_COLORS = {
    'background': '#220033',
    'border': '#3a0050',
    'hover': '#2b0040',
    'text': '#e6d6ff',
    'accent': '#b892ff',
    'grid': '#1a0028',
    'wire': '#6d5a88',
    'selected': '#d8b4ff'
}

def create_gate_pixmap(gate_name, width=50, height=30, is_control=False):
    """Create a custom-drawn gate pixmap matching the IDE theme."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Create gradient background
    if is_control:
        # Control gates (CNOT, CZ, etc.) - circular design
        gradient = QRadialGradient(width//2, height//2, min(width, height)//2)
        gradient.setColorAt(0, QColor(GATE_COLORS['accent']))
        gradient.setColorAt(1, QColor(GATE_COLORS['background']))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(GATE_COLORS['border']), 2))
        painter.drawEllipse(2, 2, width-4, height-4)
        
        # Draw control symbol
        painter.setPen(QPen(QColor(GATE_COLORS['text']), 3))
        painter.drawLine(width//2, 6, width//2, height-6)
        painter.drawLine(6, height//2, width-6, height//2)
        
    else:
        # Regular gates - rectangular design with rounded corners
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(GATE_COLORS['background']).lighter(120))
        gradient.setColorAt(1, QColor(GATE_COLORS['background']))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(GATE_COLORS['border']), 2))
        
        # Draw rounded rectangle
        rect = QRectF(2, 2, width-4, height-4)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Add subtle inner glow
        inner_pen = QPen(QColor(GATE_COLORS['accent']).lighter(150), 1)
        painter.setPen(inner_pen)
        inner_rect = QRectF(3, 3, width-6, height-6)
        painter.drawRoundedRect(inner_rect, 3, 3)
    
    # Draw gate text
    painter.setPen(QPen(QColor(GATE_COLORS['text'])))
    font = QFont("Arial", 10, QFont.Bold)
    painter.setFont(font)
    
    # Center the text
    text_rect = QRectF(0, 0, width, height)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, gate_name)
    
    painter.end()
    return pixmap

def create_measurement_pixmap(width=50, height=30):
    """Create a measurement gate pixmap with a meter-like design."""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw measurement box
    gradient = QLinearGradient(0, 0, 0, height)
    gradient.setColorAt(0, QColor(GATE_COLORS['background']).lighter(120))
    gradient.setColorAt(1, QColor(GATE_COLORS['background']))
    
    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(QColor(GATE_COLORS['border']), 2))
    
    rect = QRectF(2, 2, width-4, height-4)
    painter.drawRoundedRect(rect, 4, 4)
    
    # Draw measurement symbol (arc and arrow)
    painter.setPen(QPen(QColor(GATE_COLORS['text']), 2))
    
    # Draw arc
    arc_rect = QRectF(width*0.2, height*0.4, width*0.6, height*0.4)
    painter.drawArc(arc_rect, 0, 180 * 16)  # 180 degrees
    
    # Draw arrow
    arrow_start = QPointF(width*0.5, height*0.4)
    arrow_end = QPointF(width*0.7, height*0.25)
    painter.drawLine(arrow_start, arrow_end)
    
    # Arrow head
    arrow_head = QPolygonF([
        arrow_end,
        QPointF(arrow_end.x() - 3, arrow_end.y() + 2),
        QPointF(arrow_end.x() - 1, arrow_end.y() + 4)
    ])
    painter.setBrush(QBrush(QColor(GATE_COLORS['text'])))
    painter.drawPolygon(arrow_head)
    
    painter.end()
    return pixmap

class QuantumGate(QGraphicsItem):
    """Base class for quantum gates in the visual designer."""
    
    def __init__(self, gate_type, qubits=None, params=None):
        super().__init__()
        self.gate_type = gate_type
        self.qubits = qubits or []
        self.params = params or []
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        # Gate dimensions
        self.width = 80
        self.height = 60
        
        # Create custom gate pixmap based on type
        control_gates = ['CNOT', 'CZ', 'CSWAP', 'CCX']
        is_control = gate_type in control_gates
        
        if gate_type == 'M':
            self.gate_pixmap = create_measurement_pixmap(self.width-10, self.height-10)
        else:
            self.gate_pixmap = create_gate_pixmap(gate_type, self.width-10, self.height-10, is_control)
        
        # Appearance with IDE theme colors
        self.background_brush = QBrush(QColor(GATE_COLORS['background']))
        self.normal_pen = QPen(QColor(GATE_COLORS['border']), 2)
        self.selected_pen = QPen(QColor(GATE_COLORS['selected']), 3)
        
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter, option, widget=None):
        # Draw the custom gate pixmap centered
        rect = self.boundingRect()
        pixmap_rect = QRectF(
            (self.width - self.gate_pixmap.width()) / 2,
            (self.height - self.gate_pixmap.height()) / 2,
            self.gate_pixmap.width(),
            self.gate_pixmap.height()
        )
        
        # Add selection highlight if selected
        if self.isSelected():
            painter.setPen(self.selected_pen)
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            highlight_rect = rect.adjusted(-3, -3, 3, 3)
            painter.drawRoundedRect(highlight_rect, 8, 8)
        
        # Draw the custom gate pixmap
        painter.drawPixmap(pixmap_rect, self.gate_pixmap, self.gate_pixmap.rect())
        
        # Draw gate label below the pixmap
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(GATE_COLORS['text'])))
        label_rect = QRectF(0, self.height - 20, self.width, 15)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.gate_type)
        
        # Draw qubit info if available
        if hasattr(self, 'qubits') and self.qubits:
            qubit_text = f"Q{','.join(map(str, self.qubits))}"
            painter.setFont(QFont("Arial", 8))
            painter.drawText(QRect(5, 25, 70, 15), Qt.AlignmentFlag.AlignCenter, qubit_text)

class QubitWire(QGraphicsLineItem):
    """Visual representation of a qubit wire."""
    
    def __init__(self, start_point, end_point, qubit_index):
        super().__init__()
        self.qubit_index = qubit_index
        self.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        self.setPen(QPen(QColor(50, 50, 50), 2))
        
class GatePalette(QWidget):
    """Palette containing draggable quantum gates."""
    
    gate_dropped = pyqtSignal(str, QPoint)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Title
        title = QLabel("Quantum Gates")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("background-color: #e0e0e0; padding: 5px; border-radius: 3px;")
        layout.addWidget(title)
        
        # Gate categories
        self.create_gate_category("Single Qubit", [
            ("H", "Hadamard Gate"),
            ("X", "Pauli-X Gate"), 
            ("Y", "Pauli-Y Gate"),
            ("Z", "Pauli-Z Gate"),
            ("S", "S Gate"),
            ("T", "T Gate"),
            ("RX", "X Rotation"),
            ("RY", "Y Rotation"), 
            ("RZ", "Z Rotation")
        ], layout)
        
        self.create_gate_category("Two Qubit", [
            ("CNOT", "Controlled-NOT"),
            ("CZ", "Controlled-Z"),
            ("SWAP", "Swap Gate"),
            ("ISWAP", "iSWAP Gate")
        ], layout)
        
        self.create_gate_category("Multi Qubit", [
            ("CCX", "Toffoli Gate"),
            ("CSWAP", "Fredkin Gate"),
            ("QFT", "Quantum Fourier Transform")
        ], layout)
        
        self.create_gate_category("Measurement", [
            ("M", "Measurement"),
            ("RESET", "Reset Gate")
        ], layout)
        
        layout.addStretch()
        
    def create_gate_category(self, category_name, gates, layout):
        """Create a collapsible category of gates."""
        # Category header
        header = QLabel(category_name)
        header.setFont(QFont("Arial", 10, QFont.Bold))
        header.setStyleSheet("background-color: #f0f0f0; padding: 3px; margin-top: 10px;")
        layout.addWidget(header)
        
        # Gates in category
        for gate_type, description in gates:
            gate_widget = DraggableGate(gate_type, description)
            layout.addWidget(gate_widget)

class DraggableGate(QLabel):
    """Widget representing a draggable gate in the palette."""
    
    def __init__(self, gate_type, description):
        super().__init__()
        self.gate_type = gate_type
        self.description = description
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(50)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }
            QLabel:hover {
                background-color: #e9ecef;
                border-color: #007bff;
            }
        """)
        
        # Layout with icon space and text
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Icon placeholder (32x32 space for PNG)
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setFrameStyle(QFrame.Box)
        icon_label.setStyleSheet("border: 1px dashed #ccc; background-color: white;")
        icon_label.setText("PNG")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFont(QFont("Arial", 8))
        layout.addWidget(icon_label)
        
        # Gate info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(self.gate_type)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Arial", 8))
        desc_label.setStyleSheet("color: #666;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            
    def mouseMoveEvent(self, ev):
        if not (ev.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if ((ev.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
            
        # Start drag operation
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(f"quantum_gate:{self.gate_type}")
        drag.setMimeData(mimeData)
        
        # Create drag pixmap
        pixmap = QPixmap(80, 60)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(QColor(200, 220, 255, 180)))
        painter.setPen(QPen(QColor(100, 150, 255), 2))
        painter.drawRoundedRect(0, 0, 79, 59, 5, 5)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(QRect(0, 0, 80, 60), Qt.AlignmentFlag.AlignCenter, self.gate_type)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(40, 30))
        
        # Execute drag
        dropAction = drag.exec_(Qt.DropAction.CopyAction)

class CircuitCanvas(QGraphicsView):
    """Main canvas for designing quantum circuits."""
    
    def __init__(self):
        super().__init__()
        self.setup_scene()
        self.setup_ui()
        self.circuit_data = {"gates": [], "qubits": 4}
        
    def setup_scene(self):
        self._scene = QGraphicsScene()
        self._scene.setSceneRect(0, 0, 2000, 1000)
        self.setScene(self._scene)
        
        # Background grid
        self.draw_grid()
        
    def setup_ui(self):
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Styling
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #ffffff;
                border: 1px solid #ddd;
            }
        """)
        
    def draw_grid(self):
        """Draw background grid."""
        grid_size = 20
        scene_rect = self._scene.sceneRect()
        
        # Vertical lines
        x = scene_rect.left()
        while x <= scene_rect.right():
            line = self._scene.addLine(x, scene_rect.top(), x, scene_rect.bottom())
            line.setPen(QPen(QColor(240, 240, 240), 1))
            x += grid_size
            
        # Horizontal lines  
        y = scene_rect.top()
        while y <= scene_rect.bottom():
            line = self._scene.addLine(scene_rect.left(), y, scene_rect.right(), y)
            line.setPen(QPen(QColor(240, 240, 240), 1))
            y += grid_size
            
    def draw_qubit_wires(self, num_qubits):
        """Draw horizontal qubit wires."""
        # Clear existing wires
        for item in self._scene.items():
            if isinstance(item, QubitWire):
                self._scene.removeItem(item)
                
        # Draw new wires
        wire_spacing = 80
        start_y = 100
        wire_length = 1800
        
        for i in range(num_qubits):
            y = start_y + i * wire_spacing
            
            # Wire line
            wire = QubitWire(QPoint(100, y), QPoint(100 + wire_length, y), i)
            self._scene.addItem(wire)
            
            # Qubit label
            label = self._scene.addText(f"|q{i}⟩", QFont("Arial", 12))
            label.setPos(50, y - 10)
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("quantum_gate:"):
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("quantum_gate:"):
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("quantum_gate:"):
            gate_type = event.mimeData().text().split(":")[1]
            
            # Convert drop position to scene coordinates
            scene_pos = self.mapToScene(event.pos())
            
            # Snap to nearest qubit wire
            snapped_pos = self.snap_to_qubit_wire(scene_pos)
            
            if snapped_pos:
                self.add_gate_to_circuit(gate_type, snapped_pos)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
            
    def snap_to_qubit_wire(self, pos):
        """Snap position to nearest qubit wire."""
        wire_spacing = 80
        start_y = 100
        num_qubits = self.circuit_data["qubits"]
        
        # Find nearest wire
        for i in range(num_qubits):
            wire_y = start_y + i * wire_spacing
            if abs(pos.y() - wire_y) < 40:  # Snap tolerance
                # Snap to grid on x-axis
                grid_x = round(pos.x() / 20) * 20
                return QPointF(grid_x, wire_y), i
                
        return None
        
    def add_gate_to_circuit(self, gate_type, snap_result):
        """Add a quantum gate to the circuit at the specified position."""
        pos, qubit_index = snap_result
        
        # Create gate object
        gate = QuantumGate(gate_type, [qubit_index])
        
        # Position gate (center on wire)
        gate.setPos(pos.x() - gate.width/2, pos.y() - gate.height/2)
        
        # Add to scene
        self._scene.addItem(gate)
        
        # Update circuit data
        self.circuit_data["gates"].append({
            "type": gate_type,
            "qubits": [qubit_index],
            "position": {"x": pos.x(), "y": pos.y()}
        })
        
    def set_qubit_count(self, count):
        """Set the number of qubits and redraw wires."""
        self.circuit_data["qubits"] = count
        self.draw_qubit_wires(count)
        
    def clear_circuit(self):
        """Clear all gates from the circuit."""
        # Remove all gates
        for item in self._scene.items():
            if isinstance(item, QuantumGate):
                self._scene.removeItem(item)
                
        self.circuit_data["gates"] = []
        
    def export_circuit_code(self):
        """Export the visual circuit to Python code."""
        code = "from qubo.circuit import QuantumCircuit\n\n"
        code += f"# Visual circuit with {self.circuit_data['qubits']} qubits\n"
        code += f"qc = QuantumCircuit({self.circuit_data['qubits']})\n\n"
        
        # Sort gates by x position for proper order
        gates = sorted(self.circuit_data["gates"], key=lambda g: g["position"]["x"])
        
        for gate in gates:
            gate_type = gate["type"]
            qubits = gate["qubits"]
            
            if gate_type in ["H", "X", "Y", "Z", "S", "T"]:
                code += f"qc.add_gate('{gate_type}', targets={qubits})\n"
            elif gate_type in ["RX", "RY", "RZ"]:
                code += f"qc.add_gate('{gate_type}', targets={qubits}, params=[0.5])\n"
            elif gate_type == "CNOT":
                code += f"qc.add_gate('CNOT', targets=[0, 1])  # Adjust target qubits\n"
            elif gate_type == "M":
                code += f"qc.add_gate('M', targets={qubits})\n"
            else:
                code += f"# {gate_type} gate - implement as needed\n"
                
        return code
        
    def save_circuit(self, filename):
        """Save circuit to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.circuit_data, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save circuit: {e}")
            return False
            
    def load_circuit(self, filename):
        """Load circuit from JSON file."""
        try:
            with open(filename, 'r') as f:
                self.circuit_data = json.load(f)
                
            # Rebuild visual circuit
            self.clear_circuit()
            self.set_qubit_count(self.circuit_data["qubits"])
            
            for gate_data in self.circuit_data["gates"]:
                gate = QuantumGate(gate_data["type"], gate_data["qubits"])
                pos = gate_data["position"]
                gate.setPos(pos["x"] - gate.width/2, pos["y"] - gate.height/2)
                self._scene.addItem(gate)
                
            return True
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load circuit: {e}")
            return False

class CircuitDesigner(QMainWindow):
    """Main window for the visual quantum circuit designer."""
    
    code_generated = pyqtSignal(str)  # Signal to send code back to main GUI
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_gui = parent
        self.setWindowTitle("Quantum Circuit Designer - Visual Editor")
        self.setGeometry(100, 100, 1400, 800)
        self.setup_ui()
        self.setup_toolbar()
        
    def setup_ui(self):
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Gate palette
        palette_widget = QWidget()
        palette_widget.setFixedWidth(250)
        palette_widget.setStyleSheet("background-color: #f8f9fa; border-right: 1px solid #dee2e6;")
        
        palette_layout = QVBoxLayout(palette_widget)
        self.gate_palette = GatePalette()
        palette_layout.addWidget(self.gate_palette)
        
        splitter.addWidget(palette_widget)
        
        # Right panel - Circuit canvas
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Canvas controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Qubits:"))
        
        self.qubit_spinbox = QSpinBox()
        self.qubit_spinbox.setRange(1, 20)
        self.qubit_spinbox.setValue(4)
        self.qubit_spinbox.valueChanged.connect(self.on_qubit_count_changed)
        controls_layout.addWidget(self.qubit_spinbox)
        
        controls_layout.addStretch()
        
        clear_btn = QPushButton("Clear Circuit")
        clear_btn.clicked.connect(self.clear_circuit)
        controls_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("Export Code")
        export_btn.clicked.connect(self.export_code)
        controls_layout.addWidget(export_btn)
        
        # Send to main editor button
        if self.parent_gui:
            send_btn = QPushButton("Send to Editor")
            send_btn.clicked.connect(self.send_to_main_editor)
            send_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
            controls_layout.addWidget(send_btn)
        
        # Help button
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.show_help)
        help_btn.setStyleSheet("background-color: #17a2b8; color: white;")
        controls_layout.addWidget(help_btn)
        
        canvas_layout.addLayout(controls_layout)
        
        # Main canvas
        self.canvas = CircuitCanvas()
        canvas_layout.addWidget(self.canvas)
        
        splitter.addWidget(canvas_widget)
        splitter.setSizes([250, 1150])
        
        # Initialize with default qubit count
        self.canvas.set_qubit_count(4)
        
    def setup_toolbar(self):
        """Setup main toolbar."""
        toolbar = self.addToolBar("Main")
        
        # File operations
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_circuit)
        toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_circuit)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_circuit)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # View operations
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(lambda: self.canvas.scale(1.2, 1.2))
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(lambda: self.canvas.scale(0.8, 0.8))
        toolbar.addAction(zoom_out_action)
        
        fit_action = QAction("Fit to Window", self)
        fit_action.triggered.connect(self.canvas.fitInView)
        toolbar.addAction(fit_action)
        
    def on_qubit_count_changed(self, value):
        """Handle qubit count change."""
        self.canvas.set_qubit_count(value)
        
    def clear_circuit(self):
        """Clear the circuit."""
        reply = QMessageBox.question(self, "Clear Circuit", 
                                   "Are you sure you want to clear the circuit?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.canvas.clear_circuit()
            
    def export_code(self):
        """Export circuit to Python code."""
        code = self.canvas.export_circuit_code()
        
        # Show in dialog
        from PyQt5.QtWidgets import QDialog, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Exported Python Code")
        dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(code)
        text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(text_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(code))
        button_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.exec_()
        
    def show_help(self):
        """Show the help dialog."""
        try:
            from .designer_help import DesignerHelpDialog
            help_dialog = DesignerHelpDialog(self)
            help_dialog.exec_()
        except ImportError:
            QMessageBox.information(
                self, 
                "Help", 
                "Help system not available. Please check the installation."
            )
    
    def send_to_main_editor(self):
        """Send generated circuit code to main editor."""
        if self.parent_gui:
            code = self.canvas.export_circuit_code()
            self.parent_gui.editor.setPlainText(code)
            self.parent_gui.output_panel.appendPlainText('[Designer] Circuit code imported from Visual Designer')
            
            # Show success message
            QMessageBox.information(self, "Code Imported", 
                                  "Circuit code has been imported to the main editor!")
        else:
            QMessageBox.warning(self, "No Parent", 
                              "No main editor available to send code to.")
        
    def new_circuit(self):
        """Create new circuit."""
        self.canvas.clear_circuit()
        self.qubit_spinbox.setValue(4)
        
    def open_circuit(self):
        """Open circuit from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Circuit", "", "JSON files (*.json)")
        if filename:
            if self.canvas.load_circuit(filename):
                self.qubit_spinbox.setValue(self.canvas.circuit_data["qubits"])
                
    def save_circuit(self):
        """Save circuit to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Circuit", "circuit.json", "JSON files (*.json)")
        if filename:
            self.canvas.save_circuit(filename)

def main():
    """Test the circuit designer."""
    app = QApplication(sys.argv)
    
    designer = CircuitDesigner()
    designer.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
