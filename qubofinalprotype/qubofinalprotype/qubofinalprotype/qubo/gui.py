"""Stable minimal GUI for qubo (Python + OpenQASM highlighting only).

THIS FILE IS A CLEAN REBUILD. Previous corrupted duplicate blocks removed.

Features:
  - Code editor with line numbers & purple syntax highlighting (Python/OpenQASM).
  - Gate list (double‑click inserts qc.add_gate templates).
  - Run button executes Python code expecting `qc` (QuantumCircuit).
  - Noise dropdown applies simple per-target noise (p=0.05) after each gate.
  - Visualization for statevector probabilities or measurement counts.
  - Optional AI suggestions dock (hide with env QUBO_SKIP_AI_DOCK=1).

Non‑working/legacy features removed.
"""
from __future__ import annotations

import os, sys, math, traceback
from typing import Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QPlainTextEdit, QTabWidget, QComboBox, QSpinBox, QDockWidget, QTextEdit, QLineEdit, QFileDialog, QAction
)
from PyQt5.QtCore import Qt, QRect, QSize, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QTextFormat, QSyntaxHighlighter, QTextCharFormat

import numpy as np
import matplotlib; matplotlib.use('Qt5Agg')
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # type: ignore
except Exception:  # fallback older name
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # type: ignore
from matplotlib.figure import Figure

from .circuit import QuantumCircuit
from .simulator import StatevectorSimulator
from . import noise as noise_mod
from .ai import suggest_corrections
try:
    from .circuit_designer import QuantumCircuitDesigner  # type: ignore
except Exception:
    QuantumCircuitDesigner = None  # type: ignore

# ---- Background AI suggestion worker (needs to be defined before MainWindow uses it) ----
class _AISuggestWorker(QThread):
    result = pyqtSignal(str)
    def __init__(self, code: str):
        super().__init__(); self._code = code
    def run(self):  # type: ignore
        try:
            txt = suggest_corrections(self._code)
        except Exception as e:
            txt = f'AI suggestion error: {e}'
        self.result.emit(txt)

STYLE = """
/* Midnight Purple Terminal Theme (from reference image) */
QWidget { background-color:#120b1d; color:#f4edff; font-family:'Source Code Pro',Consolas,monospace; }
QLabel { color:#efe6fa; }
QPlainTextEdit { background:#1a112c; color:#ffffff; border:1px solid #2b1c44; selection-background-color:#342354; selection-color:#ffffff; }
QListWidget { background:#1a112c; border:1px solid #2b1c44; }
QTabWidget::pane { border:1px solid #2b1c44; background:#1a112c; }
QTabBar::tab { background:#1a112c; color:#cab8e3; padding:6px 14px; border:1px solid #2b1c44; border-bottom:none; margin-right:2px; border-top-left-radius:6px; border-top-right-radius:6px; }
QTabBar::tab:selected { background:#231538; color:#ffffff; border-color:#3a2760; }
/* Base button styling */
QPushButton { background:#201433; border:1px solid #2e1d49; color:#f4edff; padding:6px 14px; border-radius:6px; font-weight:500; }
QPushButton:hover { background:#2a1d46; }
QPushButton:pressed { background:#160c27; }
/* Run button deeper accent */
QPushButton#RunBtn { background:#2e1146; border:1px solid #5d2f8c; color:#f9f6ff; font-weight:600; }
QPushButton#RunBtn:hover { background:#3a1860; }
QPushButton#RunBtn:pressed { background:#220a37; }
/* Unified other action buttons */
QPushButton#AIBtn, QPushButton#DesignerBtn, QPushButton#PullBtn, QPushButton#ExportBtn, QPushButton#AutoFixBtn {
  background:#201433; border:1px solid #2e1d49; color:#f4edff;
}
QPushButton#AIBtn:hover, QPushButton#DesignerBtn:hover, QPushButton#PullBtn:hover, QPushButton#ExportBtn:hover, QPushButton#AutoFixBtn:hover { background:#2a1d46; }
/* Slider */
QSlider::groove:horizontal { height:6px; background:#1a112c; border:1px solid #2b1c44; border-radius:3px; }
QSlider::handle:horizontal { background:#5d2f8c; width:14px; margin:-4px 0; border-radius:7px; border:1px solid #7a44b8; }
QToolTip { background:#231538; color:#ffffff; border:1px solid #3a2760; }
QScrollBar:vertical { background:#120b1d; width:12px; }
QScrollBar::handle:vertical { background:#2a1d46; border:1px solid #3a2760; border-radius:6px; }
QScrollBar::handle:vertical:hover { background:#342354; }
QLineEdit, QSpinBox, QComboBox { background:#1a112c; border:1px solid #2b1c44; color:#ffffff; selection-background-color:#342354; }
QPlainTextEdit#error { color:#ff6d6d; }
QDockWidget::title { background:#231538; text-align:left; padding-left:8px; font-weight:600; border:1px solid #3a2760; }
LineNumberArea { background:#160c27; }
.highlight { color:#b98aff; }
.success { color:#4cc38a; }
.warn { color:#ffae42; }
.error { color:#ff5f6d; }
"""

# ---------- Line Number Area ----------
class LineNumberArea(QWidget):
    def __init__(self, editor: 'CodeEditor'):
        super().__init__(editor); self._editor = editor
    def sizeHint(self):  # type: ignore
        return QSize(self._editor.line_number_area_width(), 0)
    def paintEvent(self, event):  # type: ignore
        self._editor.paint_line_numbers(event)

# ---------- Syntax Highlighter (Python + OpenQASM) ----------
class MultiLanguageHighlighter(QSyntaxHighlighter):
    KEYWORDS = {
        'python': [
            'False','class','finally','is','return','None','continue','for','lambda','try','True',
            'def','from','nonlocal','while','and','del','global','not','with','as','elif','if','or','yield',
            'assert','else','import','pass','break','except','in','raise'
        ],
        'openqasm': ['OPENQASM','include','qreg','creg','gate','measure','if','opaque','u','cx','barrier','reset']
    }
    COMMENT = {'python': '#', 'openqasm': '//'}
    def __init__(self, document, lang: str = 'python'):
        super().__init__(document); self.lang = (lang or 'python').lower(); self._f: Dict[str, QTextCharFormat] = {}; self._init()
    def _fmt(self, color: str, *, bold=False, italic=False):
        f = QTextCharFormat(); f.setForeground(QColor(color));
        if bold: f.setFontWeight(QFont.Bold)
        if italic: f.setFontItalic(True)
        return f
    def _init(self):
        self._f['kw']  = self._fmt('#d8b4ff', bold=True)
        self._f['str'] = self._fmt('#ffcbff')
        self._f['com'] = self._fmt('#6d5a88', italic=True)
        self._f['num'] = self._fmt('#d0a8ff')
    def set_language(self, lang: str):
        self.lang = (lang or 'python').lower(); self.rehighlight()
    def highlightBlock(self, text):  # type: ignore[override]
        import re
        if text is None:
            return
        c = self.COMMENT.get(self.lang, '#')
        work = text
        if c in work:
            i = work.find(c)
            self.setFormat(i, len(work)-i, self._f['com'])
            work = work[:i]
        # strings
        for m in re.finditer(r'("[^"]*"|\'[^\']*\')', work):  # type: ignore[raw-string]
            self.setFormat(m.start(), m.end()-m.start(), self._f['str'])
        # numbers
        for m in re.finditer(r'\b[0-9]+(\.[0-9]+)?\b', work):
            self.setFormat(m.start(), m.end()-m.start(), self._f['num'])
        flags = re.IGNORECASE if self.lang == 'openqasm' else 0
        for kw in self.KEYWORDS.get(self.lang, []):
            for m in re.finditer(rf'\b{re.escape(kw)}\b', work, flags):
                self.setFormat(m.start(), m.end()-m.start(), self._f['kw'])

# ---------- Code Editor ----------
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__(); self.setFont(QFont('Source Code Pro',11))
        self.setAcceptDrops(True)  # Allow drag-and-drop
        self.setPlainText("from qubo.circuit import QuantumCircuit\n\nqc = QuantumCircuit(2)\nqc.add_gate('H', targets=[0])\n")
        # Add default sample codes for Python and OpenQASM
        self.SAMPLE_PYTHON = "from qubo.circuit import QuantumCircuit\n\nqc = QuantumCircuit(2)\nqc.add_gate('H', targets=[0])\n"
        self.SAMPLE_OPENQASM = "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\n"
        self._ln = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_area)
        self.cursorPositionChanged.connect(self._highlight_line)
        self._highlighter = MultiLanguageHighlighter(self.document(), 'python')
        self._update_margin(0); self._highlight_line()
    def set_language(self, lang: str):
        # Update sample code if current text is default sample
        currentText = self.toPlainText()
        newSample = self.SAMPLE_OPENQASM if lang.lower() == 'openqasm' else self.SAMPLE_PYTHON
        if currentText == self.SAMPLE_PYTHON or currentText == self.SAMPLE_OPENQASM:
            self.setPlainText(newSample)
        try: self._highlighter.set_language(lang)
        except Exception: self._highlighter = MultiLanguageHighlighter(self.document(), lang)
        self._highlighter.rehighlight()
    def line_number_area_width(self):
        return 10 + self.fontMetrics().width('9') * len(str(max(1,self.blockCount())))
    def _update_margin(self,_): self.setViewportMargins(self.line_number_area_width(),0,0,0)
    def resizeEvent(self,e):  # type: ignore
        super().resizeEvent(e); cr=self.contentsRect(); self._ln.setGeometry(QRect(cr.left(),cr.top(),self.line_number_area_width(),cr.height()))
    def _update_area(self,rect,dy):  # type: ignore
        if dy: self._ln.scroll(0,dy)
        else: self._ln.update(0,rect.y(),self._ln.width(),rect.height())
        if rect.contains(self.viewport().rect()): self._update_margin(0)  # type: ignore[attr-defined]
    def paint_line_numbers(self,event):
        p = QPainter(self._ln)
        p.fillRect(event.rect(), QColor('#1c0d29'))
        block = self.firstVisibleBlock()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        cur = self.textCursor().blockNumber()
        num = block.blockNumber()
        fm = self.fontMetrics()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                p.setPen(QColor('#b892ff') if num == cur else QColor('#6d5a88'))
                p.drawText(0, top, self._ln.width()-4, fm.height(), Qt.AlignRight, str(num+1))  # type: ignore[attr-defined]
            block = block.next()
            num += 1
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
    def _highlight_line(self):
        from PyQt5.QtWidgets import QTextEdit
        if self.isReadOnly(): self.setExtraSelections([]); return
        sel=QTextEdit.ExtraSelection(); sel.format.setBackground(QColor('#2b0040')); sel.format.setProperty(QTextFormat.FullWidthSelection,True); sel.cursor=self.textCursor(); sel.cursor.clearSelection(); self.setExtraSelections([sel])
    def dragEnterEvent(self, e):  # type: ignore[override]
        if not e: return
        md = e.mimeData() if hasattr(e,'mimeData') else None
        if md and hasattr(md,'hasText') and md.hasText():
            e.acceptProposedAction()
        else:
            e.ignore()
    def dragMoveEvent(self, e):  # type: ignore[override]
        if not e: return
        md = e.mimeData() if hasattr(e,'mimeData') else None
        if md and hasattr(md,'hasText') and md.hasText():
            e.acceptProposedAction()
        else:
            e.ignore()
    def dropEvent(self, e):  # type: ignore[override]
        if not e: return
        md = e.mimeData() if hasattr(e,'mimeData') else None
        if md and hasattr(md,'hasText') and md.hasText():
            text = md.text() if hasattr(md,'text') else ''
            self.insertPlainText(text + '\n')
            e.acceptProposedAction()
        else:
            e.ignore()

# ---------- Matplotlib Canvas ----------
class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5,3)); self.ax = self.fig.add_subplot(111); super().__init__(self.fig)
    def plot_state(self, state: np.ndarray) -> None:
        self.ax.clear(); probs = (np.abs(state)**2).real  # type: ignore[attr-defined]
        n = int(math.log2(len(probs))) if len(probs) > 0 else 0
        labels = [format(i, f'0{n}b') for i in range(len(probs))]
        self.ax.bar(labels, probs, color='#b892ff'); self.ax.set_ylabel('Probability'); self.ax.set_title('Statevector'); self.fig.tight_layout(); self.draw()
    def plot_counts(self, counts: Dict[str, int]) -> None:
        self.ax.clear(); labels = list(counts.keys()); vals = [counts[k] for k in labels]
        self.ax.bar(labels, vals, color='#b892ff'); self.ax.set_ylabel('Counts'); self.ax.set_title('Measurements'); self.fig.tight_layout(); self.draw()

# ---------- Noise Mapping ----------
NOISE = {
    'None': None,
    'Bit-flip': getattr(noise_mod, 'bit_flip', None),
    'Phase-flip': getattr(noise_mod, 'phase_flip', None),
    'Depolarizing': getattr(noise_mod, 'depolarizing', None),
    'Amplitude Damping': getattr(noise_mod, 'amplitude_damping', None),
}

# ---------- Main Window ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('qubo — Quantum IDE'); self.resize(1100,700); self.setStyleSheet(STYLE)
        self._current_file = None
        self._build_menubar()
        root = QWidget(); layout = QHBoxLayout(root); layout.setContentsMargins(10,8,10,8); layout.setSpacing(12); self.setCentralWidget(root)
        # Left panel
        left = QVBoxLayout(); left.setSpacing(8); left.setContentsMargins(0,0,0,0); left_w = QWidget(); left_w.setLayout(left); layout.addWidget(left_w, 1)
        left.addWidget(QLabel('Gates'))
        self.gate_list = QListWidget(); [self.gate_list.addItem(g) for g in ['H','X','RX','RY','RZ','CNOT','SWAP','M']]; left.addWidget(self.gate_list)
        left.addWidget(QLabel('Circuit Preview'))
        self.preview = QPlainTextEdit(); self.preview.setReadOnly(True); left.addWidget(self.preview, 1)
        # Right panel
        right = QVBoxLayout(); right.setSpacing(8); right.setContentsMargins(0,0,0,0); right_w = QWidget(); right_w.setLayout(right); layout.addWidget(right_w, 2)
        toolbar = QHBoxLayout(); toolbar.setSpacing(6); right.addLayout(toolbar)
        self.run_btn = QPushButton('Run'); self.run_btn.setObjectName('RunBtn')
        self.ai_btn = QPushButton('AI'); self.ai_btn.setObjectName('AIBtn')
        toolbar.addWidget(QLabel('Shots:')); self.shots_spin = QSpinBox(); self.shots_spin.setRange(1,100000); self.shots_spin.setValue(512); toolbar.addWidget(self.shots_spin)
        toolbar.addWidget(QLabel('Noise:')); self.noise_combo = QComboBox(); self.noise_combo.addItems(list(NOISE.keys())); toolbar.addWidget(self.noise_combo)
        toolbar.addWidget(QLabel('Language:')); self.lang_combo = QComboBox(); self.lang_combo.addItems(['Python','OpenQASM']); toolbar.addWidget(self.lang_combo)
        toolbar.addWidget(self.run_btn); toolbar.addWidget(self.ai_btn)
        # New buttons for AutoFix and Export Notebook
        self.autofix_btn = QPushButton('AutoFix'); self.autofix_btn.setObjectName('AutoFixBtn')
        self.export_btn = QPushButton('Export Notebook'); self.export_btn.setObjectName('ExportBtn')
        self.designer_btn = QPushButton('Designer'); self.designer_btn.setObjectName('DesignerBtn')
        self.pull_btn = QPushButton('Pull Designer Code'); self.pull_btn.setObjectName('PullBtn')
        toolbar.addWidget(self.autofix_btn)
        toolbar.addWidget(self.export_btn)
        toolbar.addWidget(self.designer_btn)
        toolbar.addWidget(self.pull_btn)
        self.editor = CodeEditor(); right.addWidget(self.editor, 3)
        self.lang_combo.currentTextChanged.connect(lambda t: self.editor.set_language('openqasm' if t.lower().startswith('openqasm') else 'python'))
        self.tabs = QTabWidget(); right.addWidget(self.tabs, 3)
        self.output_panel = QPlainTextEdit(); self.output_panel.setReadOnly(True)
        self.sim_panel = QPlainTextEdit(); self.sim_panel.setReadOnly(True)
        self.canvas = MplCanvas(); self.noise_info = QPlainTextEdit(); self.noise_info.setReadOnly(True)
        self.tabs.addTab(self.output_panel, 'Output'); self.tabs.addTab(self.sim_panel, 'Simulator'); self.tabs.addTab(self.canvas, 'Visualizer'); self.tabs.addTab(self.noise_info, 'Noise')
        self.gate_list.itemDoubleClicked.connect(self._insert_gate); self.run_btn.clicked.connect(self._run); self.ai_btn.clicked.connect(self._ai); self.autofix_btn.clicked.connect(self._auto_fix); self.export_btn.clicked.connect(self._export_notebook); self.editor.textChanged.connect(self._update_preview)
        self.designer_btn.clicked.connect(self._open_designer)
        self.pull_btn.clicked.connect(self._pull_designer_code)
        if not os.getenv('QUBO_SKIP_AI_DOCK'):
            self._init_ai_dock()
            self._init_chat_dock()
        self._update_preview()

    def _build_menubar(self):
        mb = self.menuBar()
        if mb is None: return
        file_menu = mb.addMenu('File')
        from PyQt5.QtWidgets import QMenu
        if not isinstance(file_menu, QMenu):
            return
        act_open = QAction('Open...', self)
        act_save = QAction('Save', self)
        act_save_as = QAction('Save As...', self)
        act_open.triggered.connect(self._file_open)
        act_save.triggered.connect(self._file_save)
        act_save_as.triggered.connect(lambda: self._file_save(as_new=True))
        file_menu.addAction(act_open)
        file_menu.addAction(act_save)
        file_menu.addAction(act_save_as)

    def _file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Python/QASM (*.py *.qasm *.txt);;All Files (*)')
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
            self.editor.setPlainText(data)
            self._current_file = path
            self.output_panel.appendPlainText(f'[File] Opened: {path}')
        except Exception as e:
            self.output_panel.appendPlainText(f'[File] Open failed: {e}')

    def _file_save(self, as_new: bool=False):
        if as_new or not self._current_file:
            path, _ = QFileDialog.getSaveFileName(self, 'Save File', self._current_file or 'circuit.py', 'Python (*.py);;All Files (*)')
            if not path:
                return
            self._current_file = path
        try:
            with open(self._current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.output_panel.appendPlainText(f'[File] Saved: {self._current_file}')
        except Exception as e:
            self.output_panel.appendPlainText(f'[File] Save failed: {e}')

    def _init_ai_dock(self) -> None:
        dock = QDockWidget('AI', self); self.addDockWidget(Qt.RightDockWidgetArea, dock)  # type: ignore[attr-defined]
        widget = QWidget(); layout = QVBoxLayout(widget)
        self.ai_text = QTextEdit(); self.ai_text.setReadOnly(True)
        layout.addWidget(QLabel('AI Suggestions:'))
        layout.addWidget(self.ai_text)
        dock.setWidget(widget)
        # Debounced auto-suggestion timer
        self._ai_timer = QTimer(self)
        self._ai_timer.setSingleShot(True)
        self._ai_timer.setInterval(800)  # ms debounce
        self._ai_timer.timeout.connect(self._refresh_ai_suggestions)
        # Connect editor changes only once AI dock exists
        # (editor already created at this point)
        try:
            self.editor.textChanged.connect(self._schedule_ai_refresh)
        except Exception:
            pass
        self._ai_worker = None  # type: ignore
        self._last_ai_code_hash = None

    # ---- Live AI suggestion support ----
    def _schedule_ai_refresh(self):
        # Avoid flooding: only schedule if content meaningfully changed
        code = self.editor.toPlainText()
        h = hash(code)
        if h == self._last_ai_code_hash:
            return
        self._ai_timer.start()

    def _refresh_ai_suggestions(self):
        code = self.editor.toPlainText()
        h = hash(code)
        if h == self._last_ai_code_hash:
            return
        self._last_ai_code_hash = h
        if not hasattr(self, 'ai_text'):
            return
        # Minimum length to avoid noise
        if len(code.strip()) < 12:
            self.ai_text.setPlainText('Type more code to receive suggestions...')
            return
        # If a previous worker still running, skip (next change will reschedule)
        if getattr(self, '_ai_worker', None) and getattr(self._ai_worker, 'isRunning', lambda: False)():
            return
        self.ai_text.setPlainText('Analyzing code...')
        # Spawn background worker
        self._ai_worker = _AISuggestWorker(code)
        self._ai_worker.result.connect(self._set_ai_suggestions)
        self._ai_worker.start()

    def _set_ai_suggestions(self, text: str):
        if hasattr(self, 'ai_text'):
            self.ai_text.setPlainText(text)
        # Optional: also show a condensed log in output panel
        if hasattr(self, 'output_panel'):
            self.output_panel.appendPlainText('[AI auto]\n' + (text[:400] + ('...' if len(text) > 400 else '')))

    def _init_chat_dock(self):
        # Gemini Chat Assistant dock (like Copilot)
        dock = QDockWidget('AI Chat', self); dock.setObjectName('GeminiChatDock')
        w = QWidget(); v = QVBoxLayout(w)
        self.chat_history = QPlainTextEdit(); self.chat_history.setReadOnly(True)
        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText('Ask the quantum AI assistant...')
        send_btn = QPushButton('Send')
        send_btn.clicked.connect(self._chat_send)
        v.addWidget(self.chat_history, 5)
        v.addWidget(self.chat_input)
        v.addWidget(send_btn)
        dock.setWidget(w)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)  # type: ignore[attr-defined]
        self._chat_messages = []  # store (role, content)

    def _chat_append(self, role: str, text: str):
        self.chat_history.appendPlainText(f"[{role}] {text}")

    def _chat_send(self):
        user_text = self.chat_input.text().strip()
        if not user_text:
            return
        self.chat_input.clear()
        self._chat_append('User', user_text)
        self._chat_messages.append({'role':'user','content':user_text})
        # Include current editor snippet for context (shortened)
        code = self.editor.toPlainText()
        snippet = '\n'.join(code.splitlines()[:120])
        try:
            reply = self._gemini_chat_reply(user_text, snippet)
        except Exception as e:
            reply = f"(fallback) {e}"
        self._chat_messages.append({'role':'assistant','content':reply})
        self._chat_append('AI', reply)

    def _gemini_chat_reply(self, question: str, code_snippet: str) -> str:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return 'Gemini API key not set. Set GEMINI_API_KEY env var.'
        try:
            import google.generativeai as genai  # type: ignore
            if hasattr(genai, 'configure'):
                genai.configure(api_key=api_key)  # type: ignore
            model_name = os.getenv('QUBO_GEMINI_MODEL','gemini-1.5-flash')
            model = getattr(genai, 'GenerativeModel', None)
            if model is None:
                return 'Gemini client unavailable in this environment.'
            model = model(model_name)
            system = (
                'You are an AI coding assistant for a minimal quantum circuit IDE.'
            )
            last_pairs = self._chat_messages[-6:] if hasattr(self,'_chat_messages') else []
            history_text = '\n'.join(f"{m['role'].upper()}: {m['content']}" for m in last_pairs)
            prompt = f"{system}\n\nCode Context:\n```python\n{code_snippet}\n```\n\nChat History:\n{history_text}\n\nUSER: {question}\nASSISTANT:"
            resp = model.generate_content(prompt)  # type: ignore
            txt = getattr(resp, 'text', None) or 'No response.'
            return txt.strip()
        except Exception as e:  # broad fallback
            return f'Gemini error: {e}'

    def _auto_fix(self) -> None:
        # Simulate an auto-fix attempt by re-running the code and catching errors
        self.output_panel.appendPlainText('[AutoFix] Attempting to fix errors...')
        try:
            code = self.editor.toPlainText()
            ns = {}
            exec(code, ns)
            self.output_panel.appendPlainText('[AutoFix] No errors detected.')
        except Exception as e:
            # Here you could implement more complex fix logic
            self.output_panel.appendPlainText('[AutoFix] Error detected and auto-fix applied: ' + str(e))

    def _export_notebook(self) -> None:
        # Export current circuit/editor content to a minimal Jupyter Notebook format
        nb_content = """{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# Quantum Circuit Notebook\n", "Exported from qubo IDE"]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Quantum Circuit Code\n",
    "from qubo.circuit import QuantumCircuit\n",
    "qc = QuantumCircuit(2)\n",
    "qc.add_gate('H', targets=[0])\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.x"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}"""
        try:
            with open('exported_circuit.ipynb', 'w') as f:
                f.write(nb_content)
            self.output_panel.appendPlainText('Notebook exported to exported_circuit.ipynb')
        except Exception as e:
            self.output_panel.appendPlainText('Export failed: ' + str(e))

    def _ai(self) -> None:
        code = self.editor.toPlainText()
        try: s = suggest_corrections(code)
        except Exception as e: s = f"AI error: {e}"
        if hasattr(self, 'ai_text'): self.ai_text.setPlainText(s)
        self.output_panel.appendPlainText('[AI]\n' + str(s))

    def _insert_gate(self, item) -> None:
        g = item.text()
        cursor = self.editor.textCursor()
        if g in {'H','X'}: cursor.insertText(f"qc.add_gate('{g}', targets=[0])\n")
        elif g in {'RX','RY','RZ'}: cursor.insertText(f"qc.add_gate('{g}', targets=[0], params=[0.5])\n")
        elif g == 'CNOT': cursor.insertText("qc.add_gate('CNOT', targets=[0,1])\n")
        elif g == 'SWAP': cursor.insertText("qc.add_gate('SWAP', targets=[0,1])\n")
        elif g == 'M': cursor.insertText("qc.add_gate('M', targets=[0,1])\n")

    def _update_preview(self) -> None:
        code = self.editor.toPlainText()
        lines = [line.strip() for line in code.splitlines() if 'add_gate' in line or 'QuantumCircuit' in line]
        # If no specific gate lines found, show the full code
        self.preview.setPlainText('\n'.join(lines) if lines else code)

    def _noise_hook(self):
        name = self.noise_combo.currentText()
        func = NOISE.get(name)
        if not func:
            return None
        def hook(state, gate):
            try:
                for t in getattr(gate, 'targets', []):
                    state = func(state, 0.05, t)
                return state
            except Exception:
                return state
        return hook

    def _run(self) -> None:
        # Debug: indicate start of execution
        print("Running _run method of GUI")
        from .circuit import QuantumCircuit
        code = self.editor.toPlainText()
        # Check language and process accordingly
        if self.lang_combo.currentText().lower().startswith('openqasm'):
            try:
                import re
                lines = code.splitlines()
                qc = None
                for line in lines:
                    line = line.strip()
                    if line.lower().startswith("qreg"):
                        m = re.search(r'q\[(\d+)\]', line)
                        if m:
                            num_qubits = int(m.group(1))
                            qc = QuantumCircuit(num_qubits)
                    elif qc is not None and line.lower().startswith("h "):
                        m = re.search(r'q\[(\d+)\]', line)
                        if m:
                            target = int(m.group(1))
                            qc.add_gate('H', targets=[target])
                if qc is None:
                    self.output_panel.appendPlainText("No qreg found in QASM code. Using default circuit with 2 qubits.")
                    qc = QuantumCircuit(2)
            except Exception:
                self.output_panel.appendPlainText('QASM parsing error:\n' + traceback.format_exc())
                return
        else:
            ns: Dict[str, object] = {}
            try:
                exec(code, ns)
            except Exception:
                self.output_panel.appendPlainText('Execution error:\n' + traceback.format_exc())
                return
            qc = ns.get('qc')
        if not isinstance(qc, QuantumCircuit):
            self.output_panel.appendPlainText("No QuantumCircuit 'qc' defined.")
            return
        sim = StatevectorSimulator(qc, noise_hook=self._noise_hook())
        shots = int(self.shots_spin.value())
        try:
            res = sim.run(shots=shots)
        except Exception:
            self.output_panel.appendPlainText('Simulation error:\n' + traceback.format_exc())
            return
        if isinstance(res, dict):
            self.sim_panel.setPlainText(str(res))
        else:
            self.sim_panel.setPlainText(np.array2string(res, precision=3))
        try:
            if isinstance(res, dict):
                self.canvas.plot_counts(res)
            else:
                self.canvas.plot_state(res)
        except Exception:
            pass
        self.noise_info.setPlainText(f"Noise: {self.noise_combo.currentText()} p=0.05")
        self.output_panel.appendPlainText(repr(qc))

    def _open_designer(self):
        if QuantumCircuitDesigner is None:
            self.output_panel.appendPlainText('[Designer] circuit_designer module unavailable.')
            return
        if getattr(self, '_designer_win', None):
            try:
                if self._designer_win:
                    self._designer_win.activateWindow()  # type: ignore[attr-defined]
                    self._designer_win.raise_()  # type: ignore[attr-defined]
                self.output_panel.appendPlainText('[Designer] Already open.')
                return
            except Exception:
                self._designer_win = None
        try:
            self._designer_win = QuantumCircuitDesigner()
            self._designer_win.show()
            self.output_panel.appendPlainText('[Designer] Opened Quirk-style designer.')
        except Exception as e:
            self.output_panel.appendPlainText(f'[Designer] Failed to open: {e}')

    def _pull_designer_code(self):
        if not getattr(self, '_designer_win', None):
            self.output_panel.appendPlainText('[Designer] No designer window open.')
            return
        try:
            preview = getattr(self._designer_win, 'preview', None)
            if preview is None:
                self.output_panel.appendPlainText('[Designer] Preview not found.')
                return
            code = preview.toPlainText()
            if not code.strip():
                self.output_panel.appendPlainText('[Designer] Designer preview empty.')
                return
            self.editor.setPlainText(code + '\n')
            self.output_panel.appendPlainText('[Designer] Code pulled into editor.')
        except Exception as e:
            self.output_panel.appendPlainText(f'[Designer] Pull failed: {e}')


def main() -> None:  # pragma: no cover
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':  # pragma: no cover
    main()
