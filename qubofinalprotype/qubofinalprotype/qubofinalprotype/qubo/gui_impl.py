"""GUI implementation for qubo (internal module).

Contains the full clean GUI code (CodeEditor, highlighter, MainWindow, etc.).
This file is intended to be imported by the public shim `gui.py` so tests import `qubo.gui` work.
"""

from __future__ import annotations

import sys
import os
import traceback
        return

        if isinstance(res, dict):
            self.sim_panel.setPlainText(str(res))
            try:
                self.canvas.plot_counts(res)
            except Exception:
                pass
        else:
            self.sim_panel.setPlainText(np.array2string(res, precision=3))
            try:
                self.canvas.plot_state(res)
            except Exception:
                pass

        self.noise_info.setPlainText(f"Noise: {self.noise_combo.currentText()} p=0.05")
        self.output_panel.appendPlainText(repr(qc))


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':  # pragma: no cover
    main()
"""


class LineNumberArea(QWidget):
    def __init__(self, editor: 'CodeEditor'):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # type: ignore
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):  # type: ignore
        self._editor.paint_line_numbers(event)


class MultiLanguageHighlighter(QSyntaxHighlighter):
    KEYWORDS = {
        'python': [
            'False','class','finally','is','return','None','continue','for','lambda','try','True',
            'def','from','nonlocal','while','and','del','global','not','with','as','elif','if','or','yield',
            'assert','else','import','pass','break','except','in','raise'
        ],
        'openqasm': [
            'OPENQASM','include','qreg','creg','gate','measure','if','opaque','u','cx','barrier','reset'
        ]
    }

    COMMENT = {'python': '#', 'openqasm': '//'}

    def __init__(self, document, lang: str = 'python'):
        super().__init__(document)
        self.lang = (lang or 'python').lower()
        self._formats: Dict[str, QTextCharFormat] = {}
        self._define_formats()

    def _format(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _define_formats(self) -> None:
        self._formats['keyword'] = self._format('#d8b4ff', bold=True)
        self._formats['string'] = self._format('#ffcbff')
        self._formats['comment'] = self._format('#6d5a88', italic=True)
        self._formats['number'] = self._format('#d0a8ff')

    def set_language(self, lang: str) -> None:
        self.lang = (lang or 'python').lower()
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # type: ignore
        import re
        comment_tok = self.COMMENT.get(self.lang, '#')
        if comment_tok and comment_tok in text:
            idx = text.find(comment_tok)
            self.setFormat(idx, len(text) - idx, self._formats['comment'])
            text = text[:idx]

        for m in re.finditer(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', text):
            self.setFormat(m.start(), m.end() - m.start(), self._formats['string'])

        for m in re.finditer(r'\b[0-9]+(\.[0-9]+)?\b', text):
            self.setFormat(m.start(), m.end() - m.start(), self._formats['number'])

        kws = self.KEYWORDS.get(self.lang, [])
        flags = 0
        if self.lang == 'openqasm':
            flags = __import__('re').IGNORECASE
        for kw in kws:
            for m in __import__('re').finditer(rf'\b{__import__('re').escape(kw)}\b', text, flags):
                self.setFormat(m.start(), m.end() - m.start(), self._formats['keyword'])


class CodeEditor(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setFont(QFont('Consolas', 11))
        self.setPlainText("from qubo.circuit import QuantumCircuit\n\nqc = QuantumCircuit(2)\nqc.add_gate('H', targets=[0])\n")

        self._ln = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_area)
        self.cursorPositionChanged.connect(self._highlight_line)

        self._highlighter = MultiLanguageHighlighter(self.document(), 'python')
        self._update_margin(0)
        self._highlight_line()

    def set_language(self, lang: str) -> None:
        lang = (lang or 'python').lower()
        try:
            self._highlighter.set_language(lang)
        except Exception:
            self._highlighter = MultiLanguageHighlighter(self.document(), lang)
        self._highlighter.rehighlight()

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().width('9') * digits

    def _update_margin(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def resizeEvent(self, e) -> None:  # type: ignore
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._ln.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def _update_area(self, rect, dy):  # type: ignore
        if dy:
            self._ln.scroll(0, dy)
        else:
            self._ln.update(0, rect.y(), self._ln.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_margin(0)

    def paint_line_numbers(self, event) -> None:
        p = QPainter(self._ln)
        p.fillRect(event.rect(), QColor('#1c0d29'))
        block = self.firstVisibleBlock()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        cur_block_no = self.textCursor().blockNumber()
        block_no = block.blockNumber()
        fm = self.fontMetrics()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = QColor('#b892ff') if block_no == cur_block_no else QColor('#6d5a88')
                p.setPen(color)
                p.drawText(0, top, self._ln.width() - 4, fm.height(), Qt.AlignRight, str(block_no + 1))
            block = block.next()
            block_no += 1
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())

    def _highlight_line(self) -> None:
        from PyQt5.QtWidgets import QTextEdit
        if self.isReadOnly():
            self.setExtraSelections([])
            return
        sel = QTextEdit.ExtraSelection()
        col = QColor('#2b0040')
        sel.format.setBackground(col)
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])


class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 3))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def plot_state(self, state: np.ndarray) -> None:
        self.ax.clear()
        probs = (np.abs(state) ** 2).real
        n = int(math.log2(len(probs))) if len(probs) > 0 else 0
        labels = [format(i, f'0{n}b') for i in range(len(probs))]
        self.ax.bar(labels, probs, color='#b892ff')
        self.ax.set_ylabel('Probability')
        self.ax.set_title('Statevector')
        self.fig.tight_layout()
        self.draw()

    def plot_counts(self, counts: Dict[str, int]) -> None:
        self.ax.clear()
        labels = list(counts.keys())
        vals = [counts[k] for k in labels]
        self.ax.bar(labels, vals, color='#b892ff')
        self.ax.set_ylabel('Counts')
        self.ax.set_title('Measurements')
        self.fig.tight_layout()
        self.draw()


NOISE = {
    'None': None,
    'Bit-flip': getattr(noise_mod, 'bit_flip', None),
    'Phase-flip': getattr(noise_mod, 'phase_flip', None),
    'Depolarizing': getattr(noise_mod, 'depolarizing', None),
    'Amplitude Damping': getattr(noise_mod, 'amplitude_damping', None),
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('qubo — Quantum IDE')
        self.resize(1100, 700)
        self.setStyleSheet(STYLE)

        root = QWidget()
        layout = QHBoxLayout(root)
        self.setCentralWidget(root)

        left = QVBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(left)
        layout.addWidget(left_widget, 1)

        left.addWidget(QLabel('Gates'))
        self.gate_list = QListWidget()
        for g in ['H', 'X', 'RX', 'RY', 'RZ', 'CNOT', 'SWAP', 'M']:
            self.gate_list.addItem(g)
        left.addWidget(self.gate_list)

        left.addWidget(QLabel('Circuit Preview'))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        left.addWidget(self.preview, 1)

        right_box = QVBoxLayout()
        right_widget = QWidget()
        right_widget.setLayout(right_box)
        layout.addWidget(right_widget, 2)

        toolbar = QHBoxLayout()
        right_box.addLayout(toolbar)

        self.run_btn = QPushButton('Run')
        self.ai_btn = QPushButton('AI')
        toolbar.addWidget(QLabel('Shots:'))
        self.shots_spin = QSpinBox()
        self.shots_spin.setRange(1, 100000)
        self.shots_spin.setValue(512)
        toolbar.addWidget(self.shots_spin)

        toolbar.addWidget(QLabel('Noise:'))
        self.noise_combo = QComboBox()
        self.noise_combo.addItems(list(NOISE.keys()))
        toolbar.addWidget(self.noise_combo)

        toolbar.addWidget(QLabel('Language:'))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['Python', 'OpenQASM'])
        toolbar.addWidget(self.lang_combo)
        toolbar.addWidget(self.run_btn)
        toolbar.addWidget(self.ai_btn)

        self.editor = CodeEditor()
        right_box.addWidget(self.editor, 3)

        self.lang_combo.currentTextChanged.connect(self._on_language_change)

        self.tabs = QTabWidget()
        right_box.addWidget(self.tabs, 3)
        self.output_panel = QPlainTextEdit()
        self.output_panel.setReadOnly(True)
        self.sim_panel = QPlainTextEdit()
        self.sim_panel.setReadOnly(True)
        self.canvas = MplCanvas()
        self.noise_info = QPlainTextEdit()
        self.noise_info.setReadOnly(True)
        self.tabs.addTab(self.output_panel, 'Output')
        self.tabs.addTab(self.sim_panel, 'Simulator')
        self.tabs.addTab(self.canvas, 'Visualizer')
        self.tabs.addTab(self.noise_info, 'Noise')

        self.gate_list.itemDoubleClicked.connect(self._insert_gate)
        self.run_btn.clicked.connect(self._run)
        self.ai_btn.clicked.connect(self._ai)
        self.editor.textChanged.connect(self._update_preview)

        if not os.getenv('QUBO_SKIP_AI_DOCK'):
            self._init_ai_dock()

        self.lang_combo.setCurrentText('Python')
        self._update_preview()

    def _on_language_change(self, text: str) -> None:
        mode = 'openqasm' if text.lower().startswith('openqasm') else 'python'
        self.editor.set_language(mode)

    def _init_ai_dock(self) -> None:
        dock = QDockWidget('AI Suggestions', self)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        w = QWidget()
        lay = QVBoxLayout(w)
        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        btn = QPushButton('Analyze Code')
        btn.clicked.connect(self._ai)
        lay.addWidget(btn)
        lay.addWidget(self.ai_text)
        dock.setWidget(w)

    def _ai(self) -> None:
        code = self.editor.toPlainText()
        try:
            suggestions = suggest_corrections(code)
        except Exception as e:
            suggestions = f"AI error: {e}"
        try:
            self.ai_text.setPlainText(suggestions)
        except Exception:
            pass
        self.output_panel.appendPlainText('[AI]\n' + str(suggestions))

    def _insert_gate(self, item) -> None:
        g = item.text()
        cur = self.editor.textCursor()
        if g in {'H', 'X'}:
            cur.insertText(f"qc.add_gate('{g}', targets=[0])\n")
        elif g in {'RX', 'RY', 'RZ'}:
            cur.insertText(f"qc.add_gate('{g}', targets=[0], params=[0.5])\n")
        elif g == 'CNOT':
            cur.insertText("qc.add_gate('CNOT', targets=[0,1])\n")
        elif g == 'SWAP':
            cur.insertText("qc.add_gate('SWAP', targets=[0,1])\n")
        elif g == 'M':
            cur.insertText("qc.add_gate('M', targets=[0,1])\n")

    def _update_preview(self) -> None:
        code = self.editor.toPlainText()
        lines = [l.strip() for l in code.splitlines() if 'add_gate' in l or 'QuantumCircuit' in l]
        self.preview.setPlainText('\n'.join(lines) if lines else '(no gates)')

    def _noise_hook(self):
        name = self.noise_combo.currentText()
        func = NOISE.get(name)
        if not func:
            return None

        def hook(state, gate):
            try:
                return func(state, 0.05)
            except Exception:
                return state

        return hook

    def _run(self) -> None:
        code = self.editor.toPlainText()
        ns = {}
        try:
            exec(code, ns)
        except Exception:
            self.output_panel.appendPlainText('Execution error:\n' + traceback.format_exc())
            return

        qc = ns.get('qc')
        if not isinstance(qc, QuantumCircuit):
            self.output_panel.appendPlainText("No QuantumCircuit 'qc' defined.")
            return

        shots = int(self.shots_spin.value())
        sim = StatevectorSimulator(qc, noise_hook=self._noise_hook())
        try:
            res = sim.run(shots=shots)
        except Exception:
            self.output_panel.appendPlainText('Simulation error:\n' + traceback.format_exc())
            return

        if isinstance(res, dict):
            self.sim_panel.setPlainText(str(res))
            try:
                self.canvas.plot_counts(res)
            except Exception:
                pass
        else:
            self.sim_panel.setPlainText(np.array2string(res, precision=3))
            try:
                self.canvas.plot_state(res)
            except Exception:
                pass

        self.noise_info.setPlainText(f"Noise: {self.noise_combo.currentText()} p=0.05")
        self.output_panel.appendPlainText(repr(qc))


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':  # pragma: no cover
    main()
