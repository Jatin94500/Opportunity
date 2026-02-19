#!/usr/bin/env python3
"""Quirk-style (extended) visual circuit designer.
Adds:
- Column-based grid with auto append / manual insert
- Undo / Redo stack
- Rotation parameter editor (RX/RY/RZ)
- Live lightweight statevector simulation (<=8 qubits) + amplitude panel
- Probability heat overlay per qubit (|1> marginal) like intensity
- Gate selection & editing
- Column compaction & reordering
- JSON import/export compatible structure
- Tooltips on hover
"""
from __future__ import annotations
import math, sys, json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from PyQt5.QtCore import Qt, QRectF, QPoint, QSize, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QCursor, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget, QMainWindow, QListWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QPlainTextEdit, QApplication, QMessageBox,
    QFileDialog, QDoubleSpinBox, QSlider, QSplitter, QToolTip
)

# ---------------- Data Model ----------------
@dataclass
class GateSlot:
    name: str
    targets: List[int]
    params: List[float] = field(default_factory=list)
    color: str = '#ffffff'

Column = Dict[int, GateSlot]

GATE_COLORS = {
    'H': '#10b981', 'X': '#ef4444', 'Y': '#f59e0b', 'Z': '#6366f1',
    'S': '#8b5cf6', 'T': '#d946ef', 'RX': '#0ea5e9', 'RY': '#06b6d4', 'RZ': '#0891b2',
    'CNOT': '#ec4899', 'SWAP': '#f97316', 'M': '#334155'
}

SINGLE_GATES = ['H','X','Y','Z','S','T','RX','RY','RZ','M']
TWO_QUBIT_GATES = ['CNOT','SWAP']
ROTATION_GATES = {'RX','RY','RZ'}

# ---------------- Simple simulation ----------------
import numpy as _np

_gate_mats = {
    'H': (1/math.sqrt(2))*_np.array([[1,1],[1,-1]],dtype=complex),
    'X': _np.array([[0,1],[1,0]],dtype=complex),
    'Y': _np.array([[0,-1j],[1j,0]],dtype=complex),
    'Z': _np.array([[1,0],[0,-1]],dtype=complex),
    'S': _np.array([[1,0],[0,1j]],dtype=complex),
    'T': _np.array([[1,0],[0, _np.exp(1j*math.pi/4)]],dtype=complex),
}

def rotation(axis: str, theta: float):
    c = math.cos(theta/2); s = math.sin(theta/2)
    if axis == 'X':
        return _np.array([[c, -1j*s],[-1j*s, c]],dtype=complex)
    if axis == 'Y':
        return _np.array([[c, -s],[s, c]],dtype=complex)
    if axis == 'Z':
        return _np.array([[_np.exp(-1j*theta/2),0],[0,_np.exp(1j*theta/2)]],dtype=complex)
    return _gate_mats['H']

# Apply single qubit gate matrix to state

def apply_single(state, mat, target, n):
    dim = 1<<n
    new = _np.zeros_like(state)
    bit = 1<<target
    for i in range(dim):
        if i & bit:
            base = i & ~bit
            new[i] += mat[1,1]*state[i] + mat[1,0]*state[base]
            new[base] += mat[0,1]*state[i] + mat[0,0]*state[base]
        else:
            base = i
    return new

def apply_cnot(state, c, t, n):
    dim = 1<<n; bitc=1<<c; bitt=1<<t
    new = state.copy()
    for i in range(dim):
        if i & bitc:
            j = i ^ bitt
            new[i], new[j] = new[j], new[i]
    return new

def apply_swap(state, a, b, n):
    if a==b: return state
    dim=1<<n; ba=1<<a; bb=1<<b
    new = state.copy()
    for i in range(dim):
        ia = (i & ba)!=0; ib=(i & bb)!=0
        if ia!=ib:
            j = i ^ ba ^ bb
            if i<j:
                new[i], new[j] = new[j], new[i]
    return new

def simulate(columns: List[Column], num_qubits: int, max_qubits: int=8):
    if num_qubits>max_qubits:
        return None, None
    state = _np.zeros(1<<num_qubits, dtype=complex); state[0]=1
    for col in columns:
        # unique gate slots
        seen=set()
        gate_objs=[]
        for g in col.values():
            if id(g) in seen: continue
            seen.add(id(g)); gate_objs.append(g)
        for g in gate_objs:
            if len(g.targets)==1:
                name=g.name
                if name in ROTATION_GATES:
                    theta = g.params[0] if g.params else math.pi/4
                    mat = rotation(name[-1], theta)
                else:
                    mat = _gate_mats.get(name)
                    if mat is None and name=='M':
                        continue
                state = apply_single(state, mat, g.targets[0], num_qubits)
            elif len(g.targets)==2:
                a,b=g.targets
                if g.name=='CNOT':
                    state = apply_cnot(state,a,b,num_qubits)
                elif g.name=='SWAP':
                    state = apply_swap(state,a,b,num_qubits)
    probs = _np.abs(state)**2
    # marginal p(|1>) per qubit
    p1=[]
    for q in range(num_qubits):
        mask=1<<q
        p1.append(float(sum(probs[i] for i in range(len(probs)) if i & mask)))
    return state, p1

# ---------------- Canvas ----------------
DARK_BG = '#120b1d'
PANEL_BG = '#1a112c'
MID_BG = '#201433'
ALT_BG = '#2a1d46'
ACCENT = '#5d2f8c'
ACCENT_ALT = '#2e1146'
GOOD = '#4cc38a'
WARN = '#ffae42'
ERROR = '#ff5f6d'
TEXT_FG = '#f4edff'
GRID_LINE = '#2b1c44'
DARK_BG_2 = '#160c27'

class GridCanvas(QWidget):
    def __init__(self, parent: 'QuantumCircuitDesigner'):
        super().__init__(parent)
        self.designer = parent
        self.setMouseTracking(True)
        self.cell_w = 70
        self.cell_h = 46
        self.top_margin = 30
        self.left_margin = 70
        self.hover_col = -1
        self.hover_row = -1

    def sizeHint(self):
        return QSize(900, 500)

    def _grid_rect(self, col: int, row: int) -> QRectF:
        return QRectF(self.left_margin + col * self.cell_w,
                      self.top_margin + row * self.cell_h - self.cell_h/2,
                      self.cell_w, self.cell_h)

    def paintEvent(self, a0):  # type: ignore[override]
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(DARK_BG))
        # heat overlay wires
        if self.designer.p1_cache:
            for q, val in enumerate(self.designer.p1_cache):
                y = self.top_margin + q * self.cell_h - self.cell_h/2
                p.fillRect(int(self.left_margin-20), int(y), int(self.designer.num_columns()*self.cell_w+120), int(self.cell_h), QColor(123,93,252,int(30+160*val)))
        # wires
        wire_pen = QPen(QColor(GRID_LINE), 2)
        for q in range(self.designer.num_qubits):
            y = self.top_margin + q * self.cell_h
            p.setPen(wire_pen)
            p.drawLine(self.left_margin - 10, y, self.left_margin + max(1,self.designer.num_columns())*self.cell_w + 40, y)
            p.setPen(QPen(QColor(TEXT_FG)))
            p.setFont(QFont('Source Code Pro', 10))
            p.drawText(10, y+4, f'q{q}')
        # vertical separators
        p.setPen(QPen(QColor(DARK_BG_2), 1))
        for c in range(self.designer.num_columns()+1):
            x = self.left_margin + c * self.cell_w
            p.drawLine(x, self.top_margin - self.cell_h, x, self.top_margin + (self.designer.num_qubits-1)*self.cell_h + self.cell_h)
        # gates
        for c, col in enumerate(self.designer.columns):
            for q, gate in col.items():
                base_rect = self._grid_rect(c, q)
                if gate.name == 'CNOT' and len(gate.targets)==2:
                    t0,t1=gate.targets
                    ctrl, tgt = min(t0,t1), max(t0,t1)
                    y_ctrl = self.top_margin + ctrl*self.cell_h
                    y_tgt = self.top_margin + tgt*self.cell_h
                    x_center = int(base_rect.center().x())
                    p.setPen(QPen(QColor(ACCENT),3))
                    p.drawLine(x_center, int(y_ctrl), x_center, int(y_tgt))
                    p.setBrush(QBrush(QColor(ACCENT)))
                    p.drawEllipse(QPoint(x_center, int(y_ctrl)),7,7)
                    p.setBrush(QBrush())
                    p.drawEllipse(QPoint(x_center, int(y_tgt)),11,11)
                    p.drawLine(x_center-11,int(y_tgt),x_center+11,int(y_tgt))
                    p.drawLine(x_center,int(y_tgt)-11,x_center,int(y_tgt)+11)
                    continue
                if gate.name=='SWAP' and len(gate.targets)==2:
                    t0,t1=gate.targets
                    x_center=None
                    for tq in gate.targets:
                        r=self._grid_rect(c,tq)
                        cx=int(r.center().x()); cy=int(r.center().y())
                        if x_center is None: x_center=cx
                        p.setPen(QPen(QColor(ACCENT),3))
                        size=18
                        p.drawLine(cx-int(size/2), cy-int(size/2), cx+int(size/2), cy+int(size/2))
                        p.drawLine(cx-int(size/2), cy+int(size/2), cx+int(size/2), cy-int(size/2))
                    if x_center is not None:
                        p.drawLine(x_center, int(self.top_margin+t0*self.cell_h), x_center, int(self.top_margin+t1*self.cell_h))
                    continue
                color = QColor(gate.color or '#ffffff')
                color = QColor('#23303a') if gate.name not in ['H','X','Y','Z','RX','RY','RZ'] else QColor('#2e3d49')
                p.setPen(QPen(QColor('#b98aff'), 1.2))
                p.setBrush(QBrush(color))
                rect = base_rect.adjusted(6,6,-6,-6)
                p.drawRoundedRect(rect,8,8)
                label = gate.name
                if gate.name in ROTATION_GATES and gate.params:
                    label += f"\n{gate.params[0]:.2f}"
                p.setFont(QFont('Source Code Pro', 9, QFont.DemiBold))
                p.setPen(QPen(QColor(TEXT_FG)))
                p.drawText(rect, Qt.AlignCenter, label)  # type: ignore[attr-defined]
                if self.designer.selected == (c,q):
                    p.setPen(QPen(QColor(ACCENT),2, Qt.DashLine))  # type: ignore[attr-defined]
                    p.setBrush(QBrush())
                    p.drawRoundedRect(rect.adjusted(-3,-3,3,3),10,10)
        if self.hover_col>=0 and self.hover_row>=0 and self.hover_row < self.designer.num_qubits and self.hover_col <= self.designer.num_columns():
            rect = self._grid_rect(self.hover_col, self.hover_row)
            p.setBrush(QColor(76,195,138,70)); p.setPen(Qt.NoPen)  # type: ignore[attr-defined]
            p.drawRoundedRect(rect.adjusted(4,4,-4,-4),6,6)

    def _col_row_at(self, pos) -> Tuple[int,int]:
        col = int((pos.x()-self.left_margin)/self.cell_w + 0.0)
        row = int((pos.y()-self.top_margin)/self.cell_h + 0.5)
        return col,row

    def mouseMoveEvent(self, a0):  # type: ignore[override]
        e = a0
        if e is None:
            return
        self.hover_col,self.hover_row = self._col_row_at(e.pos())
        # tooltip if over gate
        if 0 <= self.hover_col < self.designer.num_columns() and 0<=self.hover_row< self.designer.num_qubits:
            slot = self.designer.columns[self.hover_col].get(self.hover_row)
            if slot:
                txt = f"{slot.name} targets={slot.targets}"
                if slot.params:
                    txt += f" params={slot.params}"
                QToolTip.showText(QCursor.pos(), txt, self)
        self.update()

    def leaveEvent(self,a0):  # type: ignore[override]
        self.hover_col=-1; self.hover_row=-1; self.update()

    def mousePressEvent(self, a0: QMouseEvent):  # type: ignore[override]
        e = a0
        if e.button()!=Qt.LeftButton: return  # type: ignore[attr-defined]
        col,row = self._col_row_at(e.pos())
        if row<0 or row>=self.designer.num_qubits: return
        if col == self.designer.num_columns():
            self.designer.add_empty_column()
        if col<0: return
        pal_gate = self.designer.current_palette_gate
        if pal_gate:
            self.designer.push_undo()
            if pal_gate in SINGLE_GATES:
                self.designer.ensure_column(col)
                params=[]
                if pal_gate in ROTATION_GATES:
                    params=[math.pi/4]
                self.designer.columns[col][row]=GateSlot(pal_gate,[row],params,GATE_COLORS.get(pal_gate,'#53b670'))
                self.designer.selected=(col,row)
            elif pal_gate in TWO_QUBIT_GATES:
                if self.designer._pending_two_qubit is None:  # type: ignore[attr-defined]
                    self.designer._pending_two_qubit=(pal_gate,row,col)  # type: ignore[attr-defined]
                    self.designer.status('Select second qubit for 2-qubit gate')
                else:
                    name,r0,c0 = self.designer._pending_two_qubit  # type: ignore[attr-defined]
                    if c0!=col:
                        self.designer.status('Must use same column for multi-qubit gate')
                    else:
                        self.designer.ensure_column(col)
                        tq0,tq1=sorted([r0,row])
                        slot=GateSlot(name,[tq0,tq1],[],GATE_COLORS.get(name,'#53b670'))
                        self.designer.columns[col][tq0]=slot
                        self.designer.columns[col][tq1]=slot
                        self.designer._pending_two_qubit=None  # type: ignore[attr-defined]
                        self.designer.selected=(col,tq0)
        else:
            # selection / delete if clicking existing
            if col < self.designer.num_columns() and row in self.designer.columns[col]:
                if self.designer.selected == (col,row):
                    # second click deletes
                    self.designer.push_undo()
                    gate_obj = self.designer.columns[col][row]
                    # remove all references of multi-qubit gate in col
                    del_keys=[k for k,v in self.designer.columns[col].items() if v is gate_obj]
                    for k in del_keys: del self.designer.columns[col][k]
                    self.designer.selected=None
                else:
                    self.designer.selected=(col,row)
            else:
                self.designer.selected=None
        self.designer.refresh_preview()
        self.update()

# ---------------- Main Window ----------------
class QuantumCircuitDesigner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Quirk-Style Circuit Designer (Extended)')
        self.resize(1400, 780)
        # Core state (was missing -> caused AttributeError)
        self.columns: List[Column] = []
        self.num_qubits: int = 3
        self.current_palette_gate: Optional[str] = None
        self._pending_two_qubit: Optional[Tuple[str,int,int]] = None
        self.selected: Optional[Tuple[int,int]] = None
        self.p1_cache: Optional[List[float]] = None
        self.undo_stack: List[str] = []
        self.redo_stack: List[str] = []
        # Layout
        root = QHBoxLayout(); container=QWidget(); container.setLayout(root); self.setCentralWidget(container)

        # Left palette / actions
        left_layout = QVBoxLayout()
        self.palette = QListWidget(); self.palette.addItems(SINGLE_GATES + TWO_QUBIT_GATES)
        self.palette.currentTextChanged.connect(self._select_gate)
        left_layout.addWidget(QLabel('Gate Palette'))
        left_layout.addWidget(self.palette,3)

        add_q = QPushButton('Add Qubit'); add_q.clicked.connect(self._add_qubit); left_layout.addWidget(add_q)
        ins_col = QPushButton('Insert Column Before Sel'); ins_col.clicked.connect(self._insert_column); left_layout.addWidget(ins_col)
        compact = QPushButton('Compact Columns'); compact.clicked.connect(self._compact); left_layout.addWidget(compact)
        move_left = QPushButton('Move Column ◀'); move_left.clicked.connect(lambda: self._move_column(-1)); left_layout.addWidget(move_left)
        move_right= QPushButton('Move Column ▶'); move_right.clicked.connect(lambda: self._move_column(1)); left_layout.addWidget(move_right)
        clr_sel = QPushButton('Clear Gate Selection'); clr_sel.clicked.connect(self._clear_gate_sel); left_layout.addWidget(clr_sel)

        undo_btn=QPushButton('Undo'); undo_btn.clicked.connect(self.undo); left_layout.addWidget(undo_btn)
        redo_btn=QPushButton('Redo'); redo_btn.clicked.connect(self.redo); left_layout.addWidget(redo_btn)

        export_btn = QPushButton('Export → Code'); export_btn.clicked.connect(self._export_code); left_layout.addWidget(export_btn)
        save_json = QPushButton('Save JSON'); save_json.clicked.connect(self._save_json); left_layout.addWidget(save_json)
        load_json = QPushButton('Load JSON'); load_json.clicked.connect(self._load_json); left_layout.addWidget(load_json)

        # Rotation editor
        self.rot_label = QLabel('Rotation (rad)')
        self.rot_spin = QDoubleSpinBox(); self.rot_spin.setRange(-6.283,6.283); self.rot_spin.setSingleStep(0.05)
        self.rot_spin.valueChanged.connect(self._update_rotation_param)
        self.rot_slider = QSlider(Qt.Horizontal); self.rot_slider.setRange(-314,314)  # type: ignore[attr-defined]
        self.rot_slider.valueChanged.connect(lambda v: self.rot_spin.setValue(v/100))
        left_layout.addWidget(self.rot_label); left_layout.addWidget(self.rot_spin); left_layout.addWidget(self.rot_slider)
        self._rotation_editor_set_enabled(False)

        left_widget = QWidget(); left_widget.setLayout(left_layout)
        root.addWidget(left_widget,0)

        # Center canvas
        self.canvas = GridCanvas(self); root.addWidget(self.canvas,1)

        # Right side: preview + amplitudes + log
        right_layout = QVBoxLayout()
        self.preview = QPlainTextEdit(); self.preview.setReadOnly(True)
        right_layout.addWidget(QLabel('Circuit Preview'))
        right_layout.addWidget(self.preview,2)
        self.amplitudes = QPlainTextEdit(); self.amplitudes.setReadOnly(True)
        right_layout.addWidget(QLabel('Statevector / Amplitudes (<=8 qubits)'))
        right_layout.addWidget(self.amplitudes,2)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        right_layout.addWidget(QLabel('Log'))
        right_layout.addWidget(self.log,1)
        right_widget = QWidget(); right_widget.setLayout(right_layout)
        root.addWidget(right_widget,0)

        # Apply individual widget overrides (after creation)
        common_style = f"background:{PANEL_BG}; color:{TEXT_FG}; border:1px solid {GRID_LINE};"
        self.preview.setStyleSheet(common_style)
        self.amplitudes.setStyleSheet(common_style)
        self.log.setStyleSheet(common_style)

        self.setStyleSheet(f"""
QWidget {{ background:{DARK_BG}; color:{TEXT_FG}; font-family:'Source Code Pro', Consolas, monospace; }}
QLabel {{ color:{TEXT_FG}; font-weight:500; }}
QPushButton {{ background:{MID_BG}; color:{TEXT_FG}; border:1px solid {GRID_LINE}; padding:5px 12px; border-radius:6px; }}
QPushButton:hover {{ background:{ALT_BG}; }}
QPushButton:pressed {{ background:{DARK_BG_2}; }}
QPushButton#RunSim {{ background:{ACCENT_ALT}; border:1px solid {ACCENT}; color:#f9f6ff; }}
QPushButton#RunSim:hover {{ background:{ACCENT}; }}
QPushButton#UndoBtn {{ background:{MID_BG}; border:1px solid {GRID_LINE}; }}
QPushButton#RedoBtn {{ background:{MID_BG}; border:1px solid {GRID_LINE}; }}
QPushButton#ExportBtn {{ background:{ACCENT_ALT}; border:1px solid {ACCENT}; }}
QPushButton#ExportBtn:hover {{ background:{ACCENT}; }}
QPushButton#JsonSave {{ background:{ALT_BG}; border:1px solid {GRID_LINE}; }}
QPushButton#JsonLoad {{ background:{ALT_BG}; border:1px solid {GRID_LINE}; }}
QListWidget, QPlainTextEdit {{ background:{PANEL_BG}; border:1px solid {GRID_LINE}; selection-background-color:{ALT_BG}; }}
QLineEdit, QSpinBox, QComboBox {{ background:{PANEL_BG}; border:1px solid {GRID_LINE}; color:{TEXT_FG}; selection-background-color:{ALT_BG}; }}
QSlider::groove:horizontal {{ height:6px; background:{PANEL_BG}; border:1px solid {GRID_LINE}; border-radius:3px; }}
QSlider::handle:horizontal {{ background:{ACCENT}; width:14px; margin:-4px 0; border-radius:7px; border:1px solid #7a44b8; }}
QDockWidget::title {{ background:{MID_BG}; text-align:left; padding-left:8px; font-weight:600; border:1px solid {GRID_LINE}; }}
QToolTip {{ background:{MID_BG}; color:{TEXT_FG}; border:1px solid {GRID_LINE}; }}
QFrame#Legend {{ background:{MID_BG}; border:1px solid {GRID_LINE}; border-radius:6px; }}
        """)

        self.status_bar = self.statusBar()

        self.refresh_preview()  # also sim
        self.status('Ready')

    # ---------- State serialization ----------
    def serialize(self) -> str:
        data = {
            'num_qubits': self.num_qubits,
            'columns': []
        }
        for col in self.columns:
            uniq=[]; seen=set()
            for slot in col.values():
                if id(slot) in seen: continue
                seen.add(id(slot))
                uniq.append({'name': slot.name,'targets': slot.targets,'params': slot.params,'color': slot.color})
            data['columns'].append(uniq)
        return json.dumps(data)

    def deserialize(self, s: str):
        data = json.loads(s)
        self.num_qubits = data['num_qubits']
        self.columns=[]
        for col_list in data['columns']:
            col: Column = {}
            for g in col_list:
                slot = GateSlot(g['name'], g['targets'], g.get('params',[]), g.get('color','#fff'))
                for tq in slot.targets:
                    col[tq]=slot
            self.columns.append(col)
        self.selected=None

    def push_undo(self):
        self.undo_stack.append(self.serialize())
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack: return
        cur = self.serialize()
        last = self.undo_stack.pop()
        self.redo_stack.append(cur)
        self.deserialize(last)
        self.refresh_preview(); self.canvas.update(); self.status('Undo')

    def redo(self):
        if not self.redo_stack: return
        cur=self.serialize(); nxt=self.redo_stack.pop()
        self.undo_stack.append(cur)
        self.deserialize(nxt)
        self.refresh_preview(); self.canvas.update(); self.status('Redo')

    # ---------- Utility ----------
    def status(self,msg:str):
        if self.status_bar:
            self.status_bar.showMessage(msg)
        self.log.appendPlainText(msg)

    def num_columns(self): return len(self.columns)

    def ensure_column(self,col:int):
        while len(self.columns)<=col:
            self.columns.append({})

    def add_empty_column(self):
        self.push_undo(); self.columns.append({}); self.canvas.update(); self.refresh_preview()

    def _rotation_editor_set_enabled(self,en:bool):
        self.rot_label.setEnabled(en); self.rot_spin.setEnabled(en); self.rot_slider.setEnabled(en)

    # ---------- Actions ----------
    def _select_gate(self,text:str):
        self.current_palette_gate = text or None
        self._pending_two_qubit=None
        self.status(f'selected: {self.current_palette_gate}')

    def _clear_gate_sel(self):
        self.palette.clearSelection()  # type: ignore
        self.current_palette_gate=None; self._pending_two_qubit=None; self.selected=None
        self._rotation_editor_set_enabled(False)
        self.status('selection cleared')

    def _add_qubit(self):
        self.push_undo(); self.num_qubits+=1; self.status(f'qubit added -> {self.num_qubits}')
        self.refresh_preview(); self.canvas.update()

    def _insert_column(self):
        if not self.selected:
            self.status('Select a column first (by selecting gate)')
            return
        col,_=self.selected
        self.push_undo(); self.columns.insert(col,{}); self.status(f'Inserted column {col}')
        self.refresh_preview(); self.canvas.update()

    def _compact(self):
        self.push_undo()
        # remove trailing empties
        while self.columns and not self.columns[-1]: self.columns.pop()
        self.status('Compacted columns')
        self.refresh_preview(); self.canvas.update()

    def _move_column(self,delta:int):
        if not self.selected: return
        col,_=self.selected
        new_col = col+delta
        if new_col<0 or new_col>=len(self.columns): return
        self.push_undo()
        self.columns[col], self.columns[new_col] = self.columns[new_col], self.columns[col]
        self.selected=(new_col, self.selected[1])
        self.status(f'Moved column {col} -> {new_col}')
        self.refresh_preview(); self.canvas.update()

    def _update_rotation_param(self,val:float):
        if not self.selected: return
        col,row=self.selected
        slot = self.columns[col].get(row)
        if not slot or slot.name not in ROTATION_GATES: return
        slot.params=[val]
        self.rot_slider.blockSignals(True); self.rot_slider.setValue(int(val*100)); self.rot_slider.blockSignals(False)
        self.refresh_preview(); self.canvas.update()

    def _maybe_enable_rotation_editor(self):
        if not self.selected: self._rotation_editor_set_enabled(False); return
        col,row=self.selected; slot=self.columns[col].get(row)
        if slot and slot.name in ROTATION_GATES:
            self._rotation_editor_set_enabled(True)
            cur = slot.params[0] if slot.params else math.pi/4
            self.rot_spin.blockSignals(True); self.rot_slider.blockSignals(True)
            self.rot_spin.setValue(cur); self.rot_slider.setValue(int(cur*100))
            self.rot_spin.blockSignals(False); self.rot_slider.blockSignals(False)
        else:
            self._rotation_editor_set_enabled(False)

    def refresh_preview(self):
        lines=[f"from qubo.circuit import QuantumCircuit", f"qc = QuantumCircuit({self.num_qubits})"]
        for col in self.columns:
            seen=set()
            for slot in col.values():
                if id(slot) in seen: continue
                seen.add(id(slot))
                if len(slot.targets)==1:
                    if slot.name in ROTATION_GATES and slot.params:
                        lines.append(f"qc.add_gate('{slot.name}', targets={slot.targets}, params={[round(slot.params[0],4)]})")
                    else:
                        lines.append(f"qc.add_gate('{slot.name}', targets={slot.targets})")
                else:
                    lines.append(f"qc.add_gate('{slot.name}', targets={slot.targets})")
        self.preview.setPlainText('\n'.join(lines))
        # simulation
        st, p1 = simulate(self.columns, self.num_qubits)
        self.p1_cache = p1
        if st is None:
            self.amplitudes.setPlainText('Simulation skipped (>8 qubits)')
        else:
            probs = _np.abs(st)**2
            n=self.num_qubits; out_lines=[]
            for i, amp in enumerate(st):
                if probs[i]<1e-6: continue
                out_lines.append(f"|{i:0{n}b}>  amp={amp.real:+.3f}{amp.imag:+.3f}i  p={probs[i]:.4f}")
            if p1:
                out_lines.append('\nMarginal p(|1>): '+ ', '.join(f"q{k}={p1[k]:.3f}" for k in range(len(p1))))
            self.amplitudes.setPlainText('\n'.join(out_lines))
        self._maybe_enable_rotation_editor()

    def _export_code(self):
        code=self.preview.toPlainText()
        if not code.strip(): QMessageBox.warning(self,'Export','Nothing to export'); return
        try:
            with open('exported_from_designer.py','w') as f: f.write(code+'\n')
            self.status('exported → exported_from_designer.py')
        except Exception as e:
            self.status(f'export failed: {e}')

    def _save_json(self):
        path, _ = QFileDialog.getSaveFileName(self,'Save JSON','circuit.json','JSON (*.json)')
        if not path: return
        try:
            with open(path,'w') as f: f.write(self.serialize())
            self.status(f'Saved {path}')
        except Exception as e:
            self.status(f'Save failed: {e}')

    def _load_json(self):
        path,_ = QFileDialog.getOpenFileName(self,'Load JSON','','JSON (*.json)')
        if not path: return
        try:
            with open(path) as f: data=f.read()
            self.push_undo(); self.deserialize(data)
            self.refresh_preview(); self.canvas.update(); self.status(f'Loaded {path}')
        except Exception as e:
            self.status(f'Load failed: {e}')

# Standalone dev
if __name__ == '__main__':
    app = QApplication.instance() or QApplication(sys.argv)
    w = QuantumCircuitDesigner(); w.show()
    sys.exit(app.exec_())
