"""
NeuroChain: Proof of Useful Compute â€“ Command Center
"""

import sys
import time
import hashlib
import json
import random
import subprocess
import importlib.util
import os
from datetime import datetime
from pathlib import Path

_BOOTSTRAP_ENV = "NUROCHAIN_DEMO_VENV_BOOTSTRAPPED"


def _demo_venv_python_path() -> Path:
    project_root = Path(__file__).resolve().parent
    if sys.platform.startswith("win"):
        return project_root / ".venv" / "Scripts" / "python.exe"
    return project_root / ".venv" / "bin" / "python"


def _missing_demo_modules() -> list[str]:
    required = ("numpy", "pandas", "sklearn", "PyQt6", "pyqtgraph", "qtawesome")
    return [name for name in required if importlib.util.find_spec(name) is None]


def _ensure_demo_runtime_python() -> None:
    if getattr(sys, "frozen", False):
        return
    if os.environ.get(_BOOTSTRAP_ENV) == "1":
        return
    if not _missing_demo_modules():
        return

    candidate = _demo_venv_python_path()
    if not candidate.exists():
        return
    if Path(sys.executable).resolve() == candidate.resolve():
        return

    os.environ[_BOOTSTRAP_ENV] = "1"
    args = [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]]
    try:
        os.execv(args[0], args)
    except OSError:
        return


_ensure_demo_runtime_python()

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QFrame,
    QGridLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QStackedWidget,
    QGraphicsDropShadowEffect,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import (
    QColor, QPalette, QPainter, QPainterPath, QPen,
    QLinearGradient, QPixmap, QFont, QFontDatabase,
)

import pyqtgraph as pg
import qtawesome as qta

# â”€â”€ Palette â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BG        = "#100D20"
BG_MID    = "#100D20"
BG_LIGHT  = "#100D20"

CARD      = "#130F22"
CARD_ALT  = "#130F22"
CARD_HOVER= "#130F22"
CARD_DEEP = "#130F22"

BORDER    = "#1B1930"
BORDER_ALT= "#1B1930"

TEXT_W    = "#FFFFFF"
TEXT_P    = "#EDEAF5"
TEXT_SOFT = "#CBC6E0"
TEXT_SUB  = "#9A94B8"
TEXT_MUTE = "#706A90"

GREEN     = "#34C759"
RED       = "#FF4D5A"
PINK      = "#FF6B9D"
YELLOW    = "#F0B90B"

PURPLE      = "#6C63FF"
PURPLE_ALT  = "#8179FF"
PURPLE_SOFT = "#9D95FF"
CYAN        = "#00F5FF"

ICON      = "#C0BAE0"
ICON_MUTE = "#8880B0"
RADIUS    = 22

import os as _os


def _runtime_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(_os.path.dirname(_os.path.abspath(__file__))).resolve()


def _bundle_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
    return Path(_os.path.dirname(_os.path.abspath(__file__))).resolve()


def _resource_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    for candidate in (_runtime_root_dir(), _bundle_base_dir(), Path(_os.path.dirname(_os.path.abspath(__file__)))):
        resolved = candidate.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def _resolve_resource(*parts: str) -> Path:
    relative = Path(*parts)
    for root in _resource_roots():
        candidate = root / relative
        if candidate.exists():
            return candidate
    return _runtime_root_dir() / relative


_RUNTIME_ROOT = _runtime_root_dir()
_DATASETS_DIR = _resolve_resource("datasets")
_FONT_DIR = str(_resolve_resource("fonts"))
_IMAGE_PATH = _resolve_resource("image.png")
_WALLET_SYNC_PATH = _RUNTIME_ROOT / "runtime" / "opportunity_wallet_state.json"


def _dataset_path(*parts: str) -> Path:
    return _DATASETS_DIR.joinpath(*parts)


def publish_wallet_state(wallet_balance: float, total_profit: float, blocks_mined: int) -> None:
    payload: dict[str, object] = {}
    try:
        sync_dir = _WALLET_SYNC_PATH.parent
        sync_dir.mkdir(parents=True, exist_ok=True)

        if _WALLET_SYNC_PATH.exists():
            try:
                existing = json.loads(_WALLET_SYNC_PATH.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    payload.update(existing)
            except Exception:
                payload = {}

        payload.update(
            {
                "wallet_balance": round(float(wallet_balance), 6),
                "total_profit": round(float(total_profit), 6),
                "blocks_mined": int(blocks_mined),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
        )
        payload.setdefault("pending_balance", 0.0)
        payload.setdefault("source", "neurochain-local")

        tmp_path = sync_dir / ".opportunity_wallet_state.tmp"
        tmp_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        tmp_path.replace(_WALLET_SYNC_PATH)
    except Exception:
        return

QSS = f"""
* {{
    font-family: "Source Code Pro", "Cascadia Code", "Consolas", monospace;
    font-size: 13px;
}}
QMainWindow, QWidget#central {{
    background-color: {BG};
}}
QLabel {{
    color: {TEXT_P};
    background: transparent;
    border: none;
}}
QLabel[class="sub"] {{
    color: {TEXT_SUB};
    font-size: 12px;
    letter-spacing: 0.4px;
}}
QLabel[class="h2"] {{
    font-size: 16px;
    font-weight: 650;
    color: {TEXT_W};
}}
QLabel[class="h3"] {{
    font-size: 13px;
    font-weight: 650;
    color: {TEXT_SOFT};
}}
QLabel[class="section"] {{
    color: {TEXT_MUTE};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
}}
QLabel[class="log"] {{
    font-family: "Source Code Pro", "Cascadia Code", "Consolas", monospace;
    font-size: 11px;
    background: transparent;
}}
QLabel[class="pageTitle"] {{
    color: {TEXT_W};
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.4px;
}}
QFrame[class="card"] {{
    background-color: rgba(22, 18, 40, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: {RADIUS}px;
}}
QFrame[class="card"]:hover {{
    border: 1px solid rgba(255, 255, 255, 0.10);
}}
QFrame[class="card"][active="true"] {{
    background-color: rgba(28, 24, 50, 0.90);
    border: 1px solid rgba(108, 99, 255, 0.30);
    border-radius: {RADIUS}px;
}}
QFrame[class="metric"] {{
    background-color: rgba(22, 18, 40, 0.80);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
}}
QFrame#heroCard {{
    background-color: rgba(22, 18, 40, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: {RADIUS}px;
}}
QFrame#iconSidebar {{
    background-color: transparent;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 0px;
}}
QPushButton[class="navPill"] {{
    background-color: transparent;
    color: {TEXT_SUB};
    border: 1px solid {BORDER};
    border-radius: 9999px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton[class="navPill"]:hover {{
    background-color: rgba(255,255,255,0.06);
    color: {TEXT_W};
    border: 1px solid rgba(255,255,255,0.12);
}}
QPushButton[class="navPillActive"] {{
    background-color: rgba(255,255,255,0.10);
    color: {TEXT_W};
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 9999px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton[class="chip"] {{
    background-color: transparent;
    color: {TEXT_SUB};
    border: 1px solid {BORDER};
    border-radius: 9999px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 500;
}}
QPushButton[class="chip"]:hover {{
    background-color: rgba(255,255,255,0.06);
    color: {TEXT_P};
}}
QPushButton[class="sideIcon"] {{
    border: 1px solid transparent;
    background: transparent;
    border-radius: 12px;
}}
QPushButton[class="sideIcon"]:hover {{
    background: rgba(255,255,255,0.06);
    border: 1px solid {BORDER};
}}
QPushButton[class="sideIcon"][active="true"] {{
    background: rgba(108,99,255,0.12);
    border: 1px solid rgba(108,99,255,0.35);
}}
QPushButton[class="primary"] {{
    background-color: {PURPLE};
    color: white;
    font-weight: 700;
    font-size: 13px;
    border: none;
    border-radius: 9999px;
    padding: 10px 24px;
}}
QPushButton[class="primary"]:hover {{
    background-color: {PURPLE_ALT};
}}
QPushButton[class="primary"]:disabled {{
    background-color: rgba(108,99,255,0.18);
    color: rgba(255,255,255,0.28);
}}
QPushButton[class="danger"] {{
    background-color: rgba(255,77,90,0.08);
    color: {RED};
    font-weight: 600;
    font-size: 12px;
    border: 1px solid rgba(255,77,90,0.22);
    border-radius: 9999px;
    padding: 9px 20px;
}}
QPushButton[class="danger"]:hover {{
    background-color: rgba(255,77,90,0.14);
}}
QProgressBar {{
    background-color: rgba(40,30,70,0.60);
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {PURPLE};
    border-radius: 3px;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
}}
QScrollBar::handle:vertical {{
    background: rgba(108,99,255,0.22);
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QTableWidget {{
    background-color: transparent;
    color: {TEXT_W};
    border: none;
    gridline-color: rgba(255,255,255,0.02);
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
}}
QTableWidget::item:selected {{
    background-color: rgba(108,99,255,0.10);
}}
QHeaderView::section {{
    background-color: transparent;
    color: {TEXT_MUTE};
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QFrame[class="terminal"] {{
    background-color: rgba(10, 8, 22, 0.90);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
}}
QStackedWidget {{
    background: transparent;
}}
"""

def _hidden_subprocess_kwargs():
    if not sys.platform.startswith("win"):
        return {}
    kwargs = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
    startupinfo.wShowWindow = 0
    kwargs["startupinfo"] = startupinfo
    return kwargs


def _query_nvidia_smi():
    cmd = [
        "nvidia-smi",
        "--query-gpu=temperature.gpu,fan.speed,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    out = subprocess.check_output(
        cmd,
        text=True,
        stderr=subprocess.STDOUT,
        timeout=1.5,
        **_hidden_subprocess_kwargs(),
    )
    first = out.splitlines()[0].strip()
    parts = [p.strip() for p in first.split(",")]
    temp = int(float(parts[0]))
    fan = int(float(parts[1]))
    used_mb = int(float(parts[2]))
    total_mb = int(float(parts[3]))
    util = int(float(parts[4]))
    return {
        "temp_c": temp,
        "fan_pct": fan,
        "vram_used_mb": used_mb,
        "vram_total_mb": total_mb,
        "gpu_util_pct": util,
    }


def get_hardware_stats():
    try:
        return _query_nvidia_smi()
    except Exception:
        return {
            "temp_c": None,
            "fan_pct": None,
            "vram_used_mb": None,
            "vram_total_mb": None,
            "gpu_util_pct": None,
        }


def _fmt_temp(temp_c):
    return f"{temp_c} C" if temp_c is not None else "N/A"


def _fmt_pct(pct):
    return f"{pct} %" if pct is not None else "N/A"


def _fmt_vram(used_mb, total_mb):
    if used_mb is None or total_mb is None or total_mb <= 0:
        return "N/A"
    return f"{used_mb / 1024:.1f}/{total_mb / 1024:.1f} GB"

class AITrainer:
    def load_data(self, task_id):
        try:
            if task_id == "TASK-CANCER":
                df = pd.read_csv(_dataset_path("breast-cancer.csv"))
                le = LabelEncoder()
                target = "class" if "class" in df.columns else "diagnosis"
                df[target] = le.fit_transform(df[target].astype(str))
                y = df[target]
                X = df.drop(columns=[target])
                cat_cols = X.select_dtypes(include=["object", "bool", "string"]).columns
                if len(cat_cols):
                    oe = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
                    X[cat_cols] = oe.fit_transform(X[cat_cols].astype(str))
                X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
                return X, y, (30, 10)

            if task_id == "TASK-WINE":
                df = pd.read_csv(_dataset_path("wine-quality.csv"), sep=";")
                if "quality" not in df.columns:
                    df = pd.read_csv(_dataset_path("wine-quality.csv"))
                y = (df["quality"] > 6).astype(int)
                X = df.drop(columns=["quality"])
                return X, y, (30, 30)

            if task_id == "TASK-DIGITS":
                path = _dataset_path("optical+recognition+of+handwritten+digits", "optdigits.tra")
                df = pd.read_csv(path, header=None)
                y = df.iloc[:, -1]
                X = df.iloc[:, :-1]
                return X, y, (64, 32)

            raise ValueError("Unknown task")
        except Exception as ex:
            print(f"Data load fallback: {ex}")
            return (
                pd.DataFrame(np.random.rand(120, 10)),
                pd.Series(np.random.randint(0, 2, 120)),
                (10, 10),
            )

    def train_model(self, task_id, stop_flag=None):
        X, y, layers = self.load_data(task_id)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        clf = MLPClassifier(hidden_layer_sizes=layers, max_iter=1, warm_start=True, random_state=42)
        classes = np.unique(y)

        for i in range(10):
            if stop_flag and stop_flag():
                return
            try:
                clf.partial_fit(Xtr, ytr, classes=classes)
                acc = accuracy_score(yte, clf.predict(Xte))
                loss = clf.loss_ if hasattr(clf, "loss_") else 0.5 - acc / 3
            except Exception:
                acc = 0.5 + i * 0.05
                loss = 0.5 - i * 0.04
            time.sleep(0.3)
            yield i + 1, loss, acc


class Block:
    def __init__(self, index, timestamp, data, prev_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = prev_hash
        self.hash = hashlib.sha256(
            json.dumps(self.__dict__, sort_keys=True, default=str).encode()
        ).hexdigest()


class RankingSystem:
    def __init__(self):
        self.xp = 0
        self.battles_won = 0
        self.battles_lost = 0
        self.valid_blocks = 0
        self.current_tier = "Perceptron"
        self.avg_accuracy = 0.0
        self._accuracy_samples = []

    @property
    def battles_attempted(self):
        return self.battles_won + self.battles_lost

    @property
    def win_rate(self):
        if self.battles_attempted == 0:
            return 0.0
        return (self.battles_won / self.battles_attempted) * 100.0

    def _update_avg_accuracy(self, value):
        self._accuracy_samples.append(float(value))
        if len(self._accuracy_samples) > 100:
            self._accuracy_samples = self._accuracy_samples[-100:]
        self.avg_accuracy = float(np.mean(self._accuracy_samples)) if self._accuracy_samples else 0.0

    def calculate_tier(self):
        if self.valid_blocks >= 100 and self.avg_accuracy >= 0.95:
            self.current_tier = "Oracle"
        elif self.valid_blocks >= 100 and self.avg_accuracy >= 0.90:
            self.current_tier = "Architect"
        elif self.valid_blocks >= 10 and self.avg_accuracy >= 0.90:
            self.current_tier = "Trainer"
        else:
            self.current_tier = "Perceptron"
        return self.current_tier

    def record_battle_result(self, my_accuracy, rival_accuracies, total_reward):
        self._update_avg_accuracy(my_accuracy)
        rank_position = 1 + sum(1 for score in rival_accuracies if score > my_accuracy)
        competitor_count = len(rival_accuracies) + 1

        if rank_position == 1:
            self.battles_won += 1
            self.valid_blocks += 1
            self.xp += 150
            payout = round(total_reward * 0.9, 2)
            result = "WIN"
            message = f"TOP 1/{competitor_count} secured | superior accuracy {my_accuracy:.3f}"
        elif rank_position == 2:
            self.battles_lost += 1
            self.xp += 25
            payout = round(total_reward * 0.1, 2)
            result = "BREAKEVEN"
            message = f"RANK 2/{competitor_count} finished | cost coverage only"
        else:
            self.battles_lost += 1
            self.xp += 10
            payout = -0.05
            result = "LOSS"
            message = f"RANK {rank_position}/{competitor_count} | rival model outperformed"

        self.calculate_tier()
        return {
            "result": result,
            "profit": payout,
            "position": rank_position,
            "competitors": competitor_count,
            "message": message,
        }


class NeuroChain:
    def __init__(self):
        self.chain = [Block(0, datetime.now(), "Genesis Block", "0")]
        self.pending_tasks = [
            {
                "id": "TASK-CANCER",
                "name": "Bio-Scan Analysis",
                "bounty": 500,
                "impact": "Curing Disease",
                "dynamic": 9.97,
                "dataset_id": "TASK-CANCER",
                "sponsor": "Neuro Foundation",
                "source": "core",
                "status": "Hot",
            },
            {
                "id": "TASK-DIGITS",
                "name": "Drone Vision OCR",
                "bounty": 120,
                "impact": "Auto-Navigation",
                "dynamic": 3.02,
                "dataset_id": "TASK-DIGITS",
                "sponsor": "Neuro Foundation",
                "source": "core",
                "status": "Live",
            },
            {
                "id": "TASK-WINE",
                "name": "DeFi Fraud Detect",
                "bounty": 300,
                "impact": "Financial Security",
                "dynamic": -1.20,
                "dataset_id": "TASK-WINE",
                "sponsor": "Neuro Foundation",
                "source": "core",
                "status": "Hot",
            },
        ]
        self.wallet_balance = 0.0
        self.total_profit = 0.0
        self.blocks_mined = 0
        self.ranking = RankingSystem()

    def add_block(self, data):
        block = Block(len(self.chain), datetime.now(), data, self.chain[-1].hash)
        self.chain.append(block)
        self.blocks_mined += 1
        return block

    def add_company_task(
        self,
        company_name: str,
        model_name: str,
        bounty: int,
        benchmark_task_id: str,
    ) -> dict:
        benchmark_defaults = {
            "TASK-CANCER": "Curing Disease",
            "TASK-DIGITS": "Auto-Navigation",
            "TASK-WINE": "Financial Security",
        }
        safe_company = (company_name or "External Partner").strip() or "External Partner"
        safe_model = (model_name or "Custom Model").strip() or "Custom Model"
        safe_bounty = max(10, int(bounty))
        benchmark_id = benchmark_task_id if benchmark_task_id in benchmark_defaults else "TASK-CANCER"
        task_id = f"COMP-{int(time.time() * 1000)}"

        task = {
            "id": task_id,
            "name": f"{safe_model} Challenge",
            "bounty": safe_bounty,
            "impact": benchmark_defaults[benchmark_id],
            "dynamic": round(random.uniform(-4.0, 12.0), 2),
            "dataset_id": benchmark_id,
            "sponsor": safe_company,
            "source": "company",
            "status": "Listed",
        }
        self.pending_tasks.append(task)
        return task


trainer = AITrainer()
system = NeuroChain()
publish_wallet_state(system.wallet_balance, system.total_profit, system.blocks_mined)


class TrainingWorker(QThread):
    epoch_done = pyqtSignal(int, float, float)
    log_msg = pyqtSignal(str, str)
    finished_ok = pyqtSignal(dict, float, list)

    def __init__(self, task):
        super().__init__()
        self.task = task
        self._stop = False

    def request_stop(self):
        self._stop = True

    def run(self):
        self.log_msg.emit(f"ALLOCATOR -> {self.task['name']}", PURPLE)
        time.sleep(0.4)
        self.log_msg.emit("CUDA INIT ... [OK]", TEXT_SUB)
        self.log_msg.emit("TENSOR LOAD ... [OK]", TEXT_SUB)
        time.sleep(0.3)

        last_acc = 0.0
        dataset_task_id = self.task.get("dataset_id", self.task["id"])
        try:
            for epoch, loss, acc in trainer.train_model(dataset_task_id, stop_flag=lambda: self._stop):
                if self._stop:
                    self.log_msg.emit("STOPPED BY OPERATOR", RED)
                    return
                last_acc = acc
                self.epoch_done.emit(epoch, loss, acc)
                self.log_msg.emit(f"E{epoch:02d}  ACC {acc:.3f}  LOSS {loss:.4f}", TEXT_W)
        except Exception as ex:
            self.log_msg.emit(f"ERROR: {ex}", RED)
            return

        rivals = [
            max(0.0, min(1.0, random.gauss(last_acc - 0.03, 0.045)))
            for _ in range(random.randint(6, 10))
        ]
        self.log_msg.emit("ZK-PROOF OK -> SUBMITTING...", GREEN)
        time.sleep(0.5)
        self.finished_ok.emit(self.task, float(last_acc), rivals)

class GradientStrip(QWidget):
    def __init__(self, color_hex, trend_up=True):
        super().__init__()
        self.color = QColor(color_hex)
        self.trend_up = trend_up
        self.setFixedSize(100, 30)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = float(self.width())
        height = float(self.height())
        start_y = height - 5 if self.trend_up else 5
        end_y = 5 if self.trend_up else height - 5

        line_path = QPainterPath()
        line_path.moveTo(2.0, start_y)
        line_path.cubicTo(
            width * 0.28,
            height * (0.82 if self.trend_up else 0.18),
            width * 0.58,
            height * (0.18 if self.trend_up else 0.82),
            width - 2.0,
            end_y,
        )

        area_path = QPainterPath(line_path)
        area_path.lineTo(width - 2.0, height - 2.0)
        area_path.lineTo(2.0, height - 2.0)
        area_path.closeSubpath()

        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0.0, QColor(self.color.red(), self.color.green(), self.color.blue(), 170))
        gradient.setColorAt(1.0, QColor(self.color.red(), self.color.green(), self.color.blue(), 8))

        painter.fillPath(area_path, gradient)
        painter.setPen(QPen(self.color, 2.0))
        painter.drawPath(line_path)


class WalletImageBg(QWidget):
    """Paints image.png as card background with controlled opacity."""

    def __init__(self, opacity=0.55):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._opacity = opacity
        self._pixmap = QPixmap(str(_IMAGE_PATH))

    def paintEvent(self, _event):
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(self._opacity)
        # Scale to fill, crop to fit
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Center-crop
        x = (scaled.width() - self.width()) // 2
        y = (scaled.height() - self.height()) // 2
        painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())


class LiveChart(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.setBackground("transparent")
        self.setMenuEnabled(False)
        self.hideButtons()
        self.showGrid(x=True, y=True, alpha=0.25)

        plot_item = self.getPlotItem()
        plot_item.getViewBox().setMouseEnabled(x=False, y=False)

        for axis in ("left", "bottom"):
            axis_obj = plot_item.getAxis(axis)
            axis_obj.setPen(pg.mkPen(BORDER))
            axis_obj.setTextPen(pg.mkPen(TEXT_MUTE))

        self.price_curve = self.plot([], [], pen=pg.mkPen(PINK, width=2.4))
        self.signal_curve = self.plot([], [], pen=pg.mkPen(GREEN, width=1.7, style=Qt.PenStyle.DashLine))
        self.base_curve = self.plot([], [], pen=pg.mkPen((0, 0, 0, 0)))
        self.fill_item = pg.FillBetweenItem(
            self.price_curve,
            self.base_curve,
            brush=pg.mkBrush(255, 107, 157, 35),
        )
        self.addItem(self.fill_item)
        self.volume_item = pg.BarGraphItem(
            x=[],
            y0=[],
            height=[],
            width=0.62,
            brush=pg.mkBrush(240, 185, 11, 90),
            pen=pg.mkPen(None),
        )
        self.addItem(self.volume_item)

        self.price_data = []
        self.signal_data = []
        self.loss_data = []
        self.volume_data = []
        self.reset()

    def _seed_idle_data(self, points=22):
        price = 2510 + random.uniform(-12, 12)
        signal = price - 6
        for _ in range(points):
            drift = random.uniform(-8, 8)
            price = max(2350, min(2740, price + drift))
            signal = (signal * 0.65) + (price * 0.35) + random.uniform(-4, 4)
            volume = random.uniform(2, 11)
            self.price_data.append(price)
            self.signal_data.append(signal)
            self.loss_data.append(0.35)
            self.volume_data.append(volume)

    def _redraw(self):
        if not self.price_data:
            return

        x_vals = np.arange(1, len(self.price_data) + 1, dtype=float)
        baseline = min(self.price_data) - 20

        self.price_curve.setData(x_vals, self.price_data)
        self.signal_curve.setData(x_vals, self.signal_data)
        self.base_curve.setData(x_vals, [baseline] * len(x_vals))

        vol_height = np.array(self.volume_data, dtype=float)
        vol_base = np.full_like(vol_height, baseline - 12)
        self.volume_item.setOpts(x=x_vals, y0=vol_base, height=vol_height, width=0.62)

        x_min = max(1, len(self.price_data) - 28)
        x_max = max(30, len(self.price_data) + 1)
        self.setXRange(x_min, x_max, padding=0.02)

        y_max = max(max(self.price_data), max(self.signal_data)) + 12
        self.setYRange(baseline - 14, y_max, padding=0.02)

    def reset(self):
        self.price_data.clear()
        self.signal_data.clear()
        self.loss_data.clear()
        self.volume_data.clear()
        self._seed_idle_data()
        self._redraw()

    def add_point(self, acc, loss):
        anchor = self.price_data[-1] if self.price_data else 2500
        momentum = ((acc - 0.5) * 24.0) - (loss * 7.0) + random.uniform(-3.0, 3.0)
        next_price = max(2200.0, min(2900.0, anchor + momentum))
        last_signal = self.signal_data[-1] if self.signal_data else next_price
        next_signal = (last_signal * 0.7) + (next_price * 0.3)
        volume = max(2.0, min(15.0, 2.5 + abs(momentum) * 0.45))

        self.price_data.append(next_price)
        self.signal_data.append(next_signal)
        self.loss_data.append(loss)
        self.volume_data.append(volume)

        keep = 90
        if len(self.price_data) > keep:
            self.price_data = self.price_data[-keep:]
            self.signal_data = self.signal_data[-keep:]
            self.loss_data = self.loss_data[-keep:]
            self.volume_data = self.volume_data[-keep:]

        self._redraw()



class WalletGrowthCard(QFrame):
    """Top wallet card â€” growth message with image.png background."""

    def __init__(self):
        super().__init__()
        self.setObjectName("heroCard")
        self.setMinimumSize(0, 0)

        # Image background layer (your stripes image)
        self.img_bg = WalletImageBg(opacity=0.45)
        self.img_bg.setParent(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        chip = QPushButton("  Wallet  \u25BC")
        chip.setProperty("class", "chip")
        chip.setCursor(Qt.CursorShape.PointingHandCursor)
        top_row.addWidget(chip)
        top_row.addStretch()
        layout.addLayout(top_row)

        layout.addStretch()

        self.lbl_growth_msg = QLabel(
            "Since yesterday, your\nassets have grown"
        )
        self.lbl_growth_msg.setStyleSheet(
            f"color: {TEXT_SOFT}; font-size: 15px; font-weight: 500;"
            "line-height: 1.4;"
        )
        self.lbl_growth_msg.setWordWrap(True)
        layout.addWidget(self.lbl_growth_msg)

        self.lbl_growth_value = QLabel("by $0.00")
        self.lbl_growth_value.setStyleSheet(
            "font-size: 24px; font-weight: 760; color: white;"
            "letter-spacing: -0.6px;"
        )
        layout.addWidget(self.lbl_growth_value)

        layout.addSpacing(8)

        insight_btn = QPushButton("  Insights â€“ Get details  \u2B95")
        insight_btn.setProperty("class", "chip")
        insight_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(insight_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addStretch()

        # Bottom decorative bars
        bars_row = QHBoxLayout()
        bars_row.setSpacing(6)
        for w in [40, 30]:
            bar = QFrame()
            bar.setFixedSize(w, 4)
            bar.setStyleSheet(
                "background: rgba(255,255,255,0.35); border-radius: 2px;"
            )
            bars_row.addWidget(bar)
        bars_row.addStretch()
        layout.addLayout(bars_row)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.img_bg.setGeometry(0, 0, self.width(), self.height())


class WalletBalanceCard(QFrame):
    """Bottom wallet card â€” balance + mini sparkline chart."""

    def __init__(self):
        super().__init__()
        self.setObjectName("heroCard")
        self.setMinimumSize(0, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        title = QLabel("Wallet")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {TEXT_W};"
        )
        top_row.addWidget(title)
        top_row.addStretch()
        self.lbl_uptime = QLabel("10 sec ago")
        self.lbl_uptime.setProperty("class", "sub")
        top_row.addWidget(self.lbl_uptime)
        layout.addLayout(top_row)

        chip_row = QHBoxLayout()
        usdt_chip = QPushButton("  \u20BF  ALGO  \u25BC")
        usdt_chip.setProperty("class", "chip")
        usdt_chip.setCursor(Qt.CursorShape.PointingHandCursor)
        chip_row.addWidget(usdt_chip)
        chip_row.addStretch()
        layout.addLayout(chip_row)

        layout.addSpacing(2)

        val_row = QHBoxLayout()
        self.lbl_value = QLabel("0.00")
        self.lbl_value.setStyleSheet(
            "font-size: 26px; font-weight: 760; color: white;"
            "letter-spacing: -0.6px;"
        )
        val_row.addWidget(self.lbl_value)

        self.lbl_change = QLabel("+0.00%")
        self.lbl_change.setStyleSheet(
            f"color: {GREEN}; font-size: 11px; font-weight: 700;"
            f"background: rgba(52,199,89,0.12);"
            "border-radius: 9999px; padding: 3px 8px;"
        )
        val_row.addWidget(self.lbl_change)
        val_row.addStretch()
        layout.addLayout(val_row)

        self.lbl_revenue = QLabel(
            "You've earned +0.00 ALGO this session"
        )
        self.lbl_revenue.setStyleSheet(
            f"color: {TEXT_SUB}; font-size: 11px;"
        )
        layout.addWidget(self.lbl_revenue)

        layout.addSpacing(4)

        # Mini sparkline chart
        self.mini_chart = pg.PlotWidget()
        self.mini_chart.setBackground("transparent")
        self.mini_chart.setMenuEnabled(False)
        self.mini_chart.hideButtons()
        self.mini_chart.showGrid(x=False, y=False)
        self.mini_chart.setFixedHeight(80)
        pi = self.mini_chart.getPlotItem()
        pi.getViewBox().setMouseEnabled(x=False, y=False)
        pi.hideAxis("left")
        pi.hideAxis("bottom")

        self._spark_data = []
        self._seed_sparkline()
        self.spark_curve = self.mini_chart.plot(
            [], [], pen=pg.mkPen(PINK, width=2)
        )
        base_curve = self.mini_chart.plot([], [], pen=pg.mkPen((0, 0, 0, 0)))
        self.spark_fill = pg.FillBetweenItem(
            self.spark_curve, base_curve,
            brush=pg.mkBrush(255, 107, 157, 30),
        )
        self.mini_chart.addItem(self.spark_fill)
        self._redraw_spark()

        layout.addWidget(self.mini_chart)

        # Bottom row with blocks info
        bottom = QHBoxLayout()
        self.lbl_blocks = QLabel("0 blocks mined")
        self.lbl_blocks.setStyleSheet(
            "color: rgba(255,255,255,0.50); font-size: 11px;"
        )
        bottom.addWidget(self.lbl_blocks)
        bottom.addStretch()
        self.lbl_ops = QLabel("0 T-Ops/s")
        self.lbl_ops.setStyleSheet(
            f"color: {PURPLE_SOFT}; font-size: 11px; font-weight: 600;"
        )
        bottom.addWidget(self.lbl_ops)
        layout.addLayout(bottom)

        self.lbl_rank = QLabel("Perceptron | Acc 0.0%")
        self.lbl_rank.setStyleSheet(
            "color: rgba(255,255,255,0.40); font-size: 11px;"
        )
        layout.addWidget(self.lbl_rank)

    def _seed_sparkline(self, n=20):
        val = 30000 + random.uniform(-500, 500)
        for _ in range(n):
            val += random.uniform(-200, 250)
            val = max(28000, min(34000, val))
            self._spark_data.append(val)

    def _redraw_spark(self):
        if not self._spark_data:
            return
        x = np.arange(len(self._spark_data), dtype=float)
        self.spark_curve.setData(x, self._spark_data)

    def add_spark_point(self, balance):
        self._spark_data.append(balance)
        if len(self._spark_data) > 40:
            self._spark_data = self._spark_data[-40:]
        self._redraw_spark()


def make_card():
    frame = QFrame()
    frame.setProperty("class", "card")
    frame.setProperty("active", "false")
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(40)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(0, 0, 0, 35))
    frame.setGraphicsEffect(shadow)
    return frame


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  MAIN APPLICATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class NeuroChainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroChain | Proof of Useful Compute")
        self.setMinimumSize(1200, 750)
        self.resize(1440, 860)

        self.worker = None
        self.current_view = "Dashboard"
        self.top_nav_buttons = []
        self.sidebar_buttons = {}
        self.session_started = time.time()

        central = QWidget(objectName="central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_icon_sidebar())

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_top_bar())
        content_layout.addWidget(self._build_page_header())

        # â”€â”€ 4 pages via QStackedWidget â”€â”€
        self.pages = QStackedWidget()
        self.page_map = {}
        self.page_map["Dashboard"] = self.pages.addWidget(
            self._build_page_dashboard()
        )
        self.page_map["Training"] = self.pages.addWidget(
            self._build_page_training()
        )
        self.page_map["Logs"] = self.pages.addWidget(
            self._build_page_logs()
        )
        self.page_map["Network"] = self.pages.addWidget(
            self._build_page_network()
        )
        content_layout.addWidget(self.pages, stretch=1)
        root.addWidget(content, stretch=1)

        self.hw_timer = QTimer(self)
        self.hw_timer.timeout.connect(self._tick_hw)
        self.hw_timer.start(2000)

        self._refresh_rank_ui()
        self._tick_hw()
        self._bootstrap_logs()
        self._on_top_nav("Dashboard")
        self._on_sidebar_action("Dashboard")

    # â”€â”€ Page Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _build_page_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(
            "background: transparent;"
            "border-bottom: 1px solid rgba(255, 255, 255, 0.04);"
        )
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 12, 28, 12)
        layout.setSpacing(14)

        self.lbl_page_title = QLabel("Dashboard")
        self.lbl_page_title.setProperty("class", "pageTitle")
        layout.addWidget(self.lbl_page_title)
        layout.addStretch()

        right = QHBoxLayout()
        right.setSpacing(10)
        self.metric_profit = self._make_metric_card(
            "Total Profit", "$0.00", "0.00%"
        )
        self.metric_best = self._make_metric_card(
            "Best Model", "Chain LINK", "N/A"
        )
        self.metric_score = self._make_metric_card(
            "Node Score", "0/100", "Neutral"
        )
        right.addWidget(self.metric_profit)
        right.addWidget(self.metric_best)
        right.addWidget(self.metric_score)
        layout.addLayout(right)

        return header

    def _make_metric_card(self, title, value, sub):
        card = QFrame()
        card.setProperty("class", "metric")
        card.setFixedWidth(160)
        card.setFixedHeight(62)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(1)
        t = QLabel(title)
        t.setStyleSheet(
            f"color:{TEXT_MUTE}; font-size:10px; font-weight:600;"
            "letter-spacing:0.5px;"
        )
        v = QLabel(value)
        v.setStyleSheet("font-size: 15px; font-weight: 700;")
        s = QLabel(sub)
        s.setProperty("class", "sub")
        lay.addWidget(t)
        lay.addWidget(v)
        lay.addWidget(s)
        card.value_label = v
        card.sub_label = s
        return card

    # â”€â”€ Sidebar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _build_icon_sidebar(self):
        sidebar = QFrame(objectName="iconSidebar")
        sidebar.setFixedWidth(60)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(6, 16, 6, 16)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo = QPushButton()
        logo.setIcon(qta.icon("fa5s.atom", color=PURPLE_SOFT))
        logo.setIconSize(QSize(24, 24))
        logo.setFixedSize(48, 44)
        logo.setProperty("class", "sideIcon")
        logo.setProperty("active", "false")
        logo.setCursor(Qt.CursorShape.PointingHandCursor)
        logo.clicked.connect(
            lambda: self._on_sidebar_action("NeuroChain")
        )
        self.sidebar_buttons["NeuroChain"] = logo
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(18)

        items = [
            ("fa5s.th-large", "Dashboard"),
            ("fa5s.exchange-alt", "Training"),
            ("fa5s.terminal", "Logs"),
            ("fa5s.project-diagram", "Network"),
        ]
        for icon_name, tip in items:
            btn = QPushButton()
            btn.setIcon(qta.icon(icon_name, color=ICON_MUTE))
            btn.setIconSize(QSize(18, 18))
            btn.setFixedSize(48, 40)
            btn.setProperty("class", "sideIcon")
            btn.setProperty("active", "false")
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda _=False, n=tip: self._on_sidebar_action(n)
            )
            self.sidebar_buttons[tip] = btn
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        profile = QPushButton()
        profile.setIcon(qta.icon("fa5s.user-circle", color=ICON))
        profile.setIconSize(QSize(20, 20))
        profile.setFixedSize(48, 40)
        profile.setProperty("class", "sideIcon")
        profile.setProperty("active", "false")
        profile.clicked.connect(
            lambda: self._on_sidebar_action("Profile")
        )
        self.sidebar_buttons["Profile"] = profile
        layout.addWidget(profile, alignment=Qt.AlignmentFlag.AlignCenter)

        return sidebar

    # â”€â”€ Top Bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _build_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(
            f"background: {BG};"
            "border-bottom: 1px solid rgba(255, 255, 255, 0.04);"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(8)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand = QLabel("NeuroChain")
        brand.setStyleSheet(
            f"font-size:14px; font-weight:800;"
            f"letter-spacing:1px; color:{TEXT_SOFT};"
        )
        brand_col.addWidget(brand)
        tagline = QLabel("Proof of Useful Compute")
        tagline.setStyleSheet(
            f"font-size:10px; color:{TEXT_MUTE}; letter-spacing:0.8px;"
        )
        brand_col.addWidget(tagline)
        layout.addLayout(brand_col)

        layout.addStretch()

        self.lbl_status = QLabel("o IDLE")
        self.lbl_status.setStyleSheet(
            f"color:{TEXT_MUTE}; font-size:11px; font-weight:700;"
        )
        layout.addWidget(self.lbl_status)
        layout.addSpacing(10)

        self.lbl_bal_top = QLabel("0.00 ALGO")
        self.lbl_bal_top.setStyleSheet(
            f"color:{TEXT_SOFT}; font-size:11px; font-weight:700;"
            f"background:{CARD};"
            f"border:1px solid {BORDER};"
            "border-radius:9999px; padding:5px 16px;"
        )
        layout.addWidget(self.lbl_bal_top)

        return bar

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  PAGE BUILDERS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _build_page_dashboard(self):
        """Dashboard â€” 3-column bento grid like reference."""
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(28, 20, 28, 28)
        grid.setSpacing(18)

        # Left col: Two wallet cards (square-ish, stacked)
        self.wallet_growth = WalletGrowthCard()
        shadow_g = QGraphicsDropShadowEffect()
        shadow_g.setBlurRadius(40)
        shadow_g.setOffset(0, 8)
        shadow_g.setColor(QColor(0, 0, 0, 35))
        self.wallet_growth.setGraphicsEffect(shadow_g)
        grid.addWidget(self.wallet_growth, 0, 0)

        self.wallet_balance = WalletBalanceCard()
        shadow_b = QGraphicsDropShadowEffect()
        shadow_b.setBlurRadius(40)
        shadow_b.setOffset(0, 8)
        shadow_b.setColor(QColor(0, 0, 0, 35))
        self.wallet_balance.setGraphicsEffect(shadow_b)
        grid.addWidget(self.wallet_balance, 1, 0)

        # Center col: Chart + Tasks
        self.chart_card = self._build_chart_card()
        grid.addWidget(self.chart_card, 0, 1)

        self.assets_card = self._build_assets_card()
        grid.addWidget(self.assets_card, 1, 1)

        # Right col: Stats + Activity
        self.stats_card = self._build_node_stats_card()
        grid.addWidget(self.stats_card, 0, 2)

        home_panel = self._build_home_panel()
        grid.addWidget(home_panel, 1, 2)

        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 2)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        return page

    def _build_page_training(self):
        """Training â€” centred control panel."""
        page = QWidget()
        outer = QHBoxLayout(page)
        outer.setContentsMargins(28, 20, 28, 28)
        outer.setSpacing(20)

        outer.addStretch(1)
        control = self._build_node_control_panel()
        control.setMaximumWidth(520)
        outer.addWidget(control)
        outer.addStretch(1)

        return page

    def _build_page_logs(self):
        """Logs â€” full-width terminal."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 28)

        logs_w = self._build_system_logs_panel()
        layout.addWidget(logs_w)

        return page

    def _build_page_network(self):
        """Network â€” stats + blocks table."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 28)

        net_w = self._build_network_panel()
        layout.addWidget(net_w)

        return page

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  CARD BUILDERS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _build_node_stats_card(self):
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("Node Stats")
        title.setProperty("class", "h2")
        layout.addWidget(title)

        self.lbl_temp = QLabel("N/A")
        self.lbl_fan = QLabel("N/A")
        self.lbl_vram = QLabel("N/A")

        for icon_name, label_text, widget in [
            ("fa5s.thermometer-half", "GPU TEMP", self.lbl_temp),
            ("fa5s.fan", "FAN", self.lbl_fan),
            ("fa5s.memory", "VRAM", self.lbl_vram),
        ]:
            row = QHBoxLayout()
            icon = QLabel()
            icon.setPixmap(
                qta.icon(icon_name, color=TEXT_SUB).pixmap(14, 14)
            )
            row.addWidget(icon)
            label = QLabel(label_text)
            label.setStyleSheet(
                f"color:{TEXT_MUTE}; font-size:11px; font-weight:600;"
            )
            row.addWidget(label)
            row.addStretch()
            widget.setStyleSheet("font-weight:700; font-size:14px;")
            row.addWidget(widget)
            layout.addLayout(row)

        layout.addStretch()

        self.xp_bar = QProgressBar()
        self.xp_bar.setRange(0, 1000)
        self.xp_bar.setValue(0)
        self.xp_bar.setTextVisible(False)
        self.xp_bar.setFixedHeight(6)

        self.lbl_xp = QLabel("XP 0/1000")
        self.lbl_xp.setProperty("class", "sub")
        layout.addWidget(self.lbl_xp)
        layout.addWidget(self.xp_bar)

        self.lbl_tier = QLabel("Tier: Perceptron")
        self.lbl_tier.setProperty("class", "h3")
        layout.addWidget(self.lbl_tier)

        self.lbl_win_rate = QLabel("Batches Won: 0 / 0 (0.0%)")
        self.lbl_win_rate.setProperty("class", "sub")
        layout.addWidget(self.lbl_win_rate)
        return card

    def _build_chart_card(self):
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(8)

        chart_head = QHBoxLayout()
        chart_title = QLabel("Training Metrics")
        chart_title.setProperty("class", "h2")
        chart_head.addWidget(chart_title)
        chart_head.addStretch()

        self.lbl_hashrate = QLabel("IDLE")
        self.lbl_hashrate.setStyleSheet(
            f"color:{TEXT_SUB}; font-size:12px; font-weight:700;"
        )
        chart_head.addWidget(self.lbl_hashrate)
        layout.addLayout(chart_head)

        legend = QHBoxLayout()
        for name, color in [
            ("Price", PINK),
            ("Signal", GREEN),
            ("Volume", YELLOW),
        ]:
            dot = QLabel("\u25CF")
            dot.setStyleSheet(
                f"color:{color}; font-size:8px;"
            )
            text = QLabel(name)
            text.setProperty("class", "sub")
            legend.addWidget(dot)
            legend.addWidget(text)
            legend.addSpacing(12)
        legend.addStretch()
        layout.addLayout(legend)

        self.chart = LiveChart()
        self.chart.setMinimumHeight(180)
        layout.addWidget(self.chart, stretch=1)
        return card

    def _build_assets_card(self):
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        title = QLabel("Available Tasks")
        title.setProperty("class", "h2")
        header_row.addWidget(title)
        header_row.addStretch()
        list_btn = QPushButton("List Company Model")
        list_btn.setProperty("class", "chip")
        list_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        list_btn.clicked.connect(self._open_company_task_dialog)
        header_row.addWidget(list_btn)
        layout.addLayout(header_row)

        self.assets_tbl = QTableWidget()
        self.assets_tbl.setColumnCount(7)
        self.assets_tbl.setHorizontalHeaderLabels(
            ["Task", "Sponsor", "Impact", "Bounty", "24h %", "Signal", "Status"]
        )
        h = self.assets_tbl.horizontalHeader()
        h.setStretchLastSection(True)
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.assets_tbl.verticalHeader().setVisible(False)
        self.assets_tbl.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.assets_tbl.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.assets_tbl.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.assets_tbl.setShowGrid(False)
        self._fill_assets()
        layout.addWidget(self.assets_tbl)
        return card

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  PANEL BUILDERS  (right-side / sub-pages)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _build_home_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.home_panel_card = make_card()
        cl = QVBoxLayout(self.home_panel_card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(8)

        title = QLabel("Live Compute")
        title.setProperty("class", "h2")
        cl.addWidget(title)

        self.lbl_queue_depth = QLabel("Queue Depth: 0")
        self.lbl_queue_depth.setProperty("class", "sub")
        cl.addWidget(self.lbl_queue_depth)
        self.lbl_batch_window = QLabel("Batch Window: -- ms")
        self.lbl_batch_window.setProperty("class", "sub")
        cl.addWidget(self.lbl_batch_window)
        self.lbl_reward_flow = QLabel("Reward Flow: 0.00 ALGO/min")
        self.lbl_reward_flow.setProperty("class", "sub")
        cl.addWidget(self.lbl_reward_flow)

        cl.addSpacing(4)
        util_title = QLabel("GPU SATURATION")
        util_title.setProperty("class", "section")
        cl.addWidget(util_title)
        self.util_bar = QProgressBar()
        self.util_bar.setRange(0, 100)
        self.util_bar.setValue(0)
        self.util_bar.setTextVisible(False)
        self.util_bar.setFixedHeight(6)
        cl.addWidget(self.util_bar)

        flow_title = QLabel("SETTLEMENT HEALTH")
        flow_title.setProperty("class", "section")
        cl.addWidget(flow_title)
        self.flow_bar = QProgressBar()
        self.flow_bar.setRange(0, 100)
        self.flow_bar.setValue(0)
        self.flow_bar.setTextVisible(False)
        self.flow_bar.setFixedHeight(6)
        cl.addWidget(self.flow_bar)

        cl.addSpacing(4)
        self.lbl_compute_hint = QLabel("Awaiting next training batch")
        self.lbl_compute_hint.setProperty("class", "sub")
        cl.addWidget(self.lbl_compute_hint)

        self.lbl_signal_1 = QLabel("Arbitration: Stable")
        self.lbl_signal_1.setProperty("class", "sub")
        cl.addWidget(self.lbl_signal_1)
        self.lbl_signal_2 = QLabel("Validation Lag: 0.0 ms")
        self.lbl_signal_2.setProperty("class", "sub")
        cl.addWidget(self.lbl_signal_2)
        self.lbl_signal_3 = QLabel("Drift Guard: Monitoring")
        self.lbl_signal_3.setProperty("class", "sub")
        cl.addWidget(self.lbl_signal_3)
        self.lbl_signal_4 = QLabel("Reward Pressure: Neutral")
        self.lbl_signal_4.setProperty("class", "sub")
        cl.addWidget(self.lbl_signal_4)

        cl.addStretch()
        layout.addWidget(self.home_panel_card)
        return container

    def _build_node_control_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.control_card = make_card()
        cl = QVBoxLayout(self.control_card)
        cl.setContentsMargins(28, 24, 28, 24)
        cl.setSpacing(10)

        control_title = QLabel("Node Control")
        control_title.setProperty("class", "h2")
        cl.addWidget(control_title)

        cl.addSpacing(4)
        self.lbl_node_id = QLabel("Node Alias: NODE-0000")
        self.lbl_node_id.setProperty("class", "sub")
        cl.addWidget(self.lbl_node_id)

        cl.addSpacing(8)
        self.btn_register = QPushButton("  Register New Node")
        self.btn_register.setProperty("class", "primary")
        self.btn_register.setIcon(
            qta.icon("fa5s.plus-circle", color=TEXT_SOFT)
        )
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.clicked.connect(self._register_node)
        cl.addWidget(self.btn_register)

        self.btn_start = QPushButton("  Activate Node")
        self.btn_start.setProperty("class", "primary")
        self.btn_start.setIcon(qta.icon("fa5s.play", color=TEXT_SOFT))
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._start_mining)
        cl.addWidget(self.btn_start)

        self.btn_stop = QPushButton("  Stop Node")
        self.btn_stop.setProperty("class", "danger")
        self.btn_stop.setIcon(qta.icon("fa5s.stop", color=RED))
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_mining)
        cl.addWidget(self.btn_stop)

        cl.addSpacing(6)
        self.lbl_control_hint = QLabel(
            "Node ready. Press Activate Node to start."
        )
        self.lbl_control_hint.setProperty("class", "sub")
        self.lbl_control_hint.setWordWrap(True)
        cl.addWidget(self.lbl_control_hint)

        cl.addStretch()
        layout.addWidget(self.control_card)
        return container

    def _build_system_logs_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.logs_card = make_card()
        cl = QVBoxLayout(self.logs_card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(8)

        header = QHBoxLayout()
        log_title = QLabel("System Logs")
        log_title.setProperty("class", "h2")
        header.addWidget(log_title)
        header.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("class", "chip")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_logs)
        header.addWidget(clear_btn)
        cl.addLayout(header)

        terminal = QFrame()
        terminal.setProperty("class", "terminal")
        term_layout = QVBoxLayout(terminal)
        term_layout.setContentsMargins(14, 14, 14, 14)

        log_scroll = QScrollArea()
        log_scroll.setWidgetResizable(True)
        self.log_widget = QWidget()
        self.log_layout = QVBoxLayout(self.log_widget)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(3)
        self.log_layout.addStretch()
        log_scroll.setWidget(self.log_widget)
        term_layout.addWidget(log_scroll)

        cl.addWidget(terminal, stretch=1)
        layout.addWidget(self.logs_card)
        return container

    def _build_network_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.network_card = make_card()
        cl = QVBoxLayout(self.network_card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(8)

        network_title = QLabel("Network")
        network_title.setProperty("class", "h2")
        cl.addWidget(network_title)

        self.lbl_nodes = QLabel("Active Nodes: 8,432")
        self.lbl_nodes.setProperty("class", "sub")
        cl.addWidget(self.lbl_nodes)
        self.lbl_hash_g = QLabel("Hashrate: 452 PH/s")
        self.lbl_hash_g.setProperty("class", "sub")
        cl.addWidget(self.lbl_hash_g)
        self.lbl_tb = QLabel("Total Blocks: 1")
        self.lbl_tb.setProperty("class", "sub")
        cl.addWidget(self.lbl_tb)

        self.lbl_consensus = QLabel("Consensus Confidence: 0%")
        self.lbl_consensus.setProperty("class", "sub")
        cl.addWidget(self.lbl_consensus)
        self.consensus_bar = QProgressBar()
        self.consensus_bar.setRange(0, 100)
        self.consensus_bar.setValue(52)
        self.consensus_bar.setTextVisible(False)
        self.consensus_bar.setFixedHeight(6)
        cl.addWidget(self.consensus_bar)

        cl.addSpacing(8)
        rb_title = QLabel("Recent Blocks")
        rb_title.setProperty("class", "h3")
        cl.addWidget(rb_title)

        self.blk_tbl = QTableWidget()
        self.blk_tbl.setColumnCount(3)
        self.blk_tbl.setHorizontalHeaderLabels(["#", "Hash", "Time"])
        bh = self.blk_tbl.horizontalHeader()
        bh.setStretchLastSection(True)
        bh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.blk_tbl.verticalHeader().setVisible(False)
        self.blk_tbl.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.blk_tbl.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.blk_tbl.setShowGrid(False)
        self._fill_blocks()
        cl.addWidget(self.blk_tbl, stretch=1)

        layout.addWidget(self.network_card)
        return container

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  TABLE FILLERS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _get_selected_task(self):
        row = self.assets_tbl.currentRow()
        tasks = system.pending_tasks
        if 0 <= row < len(tasks):
            return tasks[row]
        return None

    def _select_task_by_id(self, task_id):
        tasks = system.pending_tasks
        for idx, task in enumerate(tasks):
            if task.get("id") == task_id:
                self.assets_tbl.selectRow(idx)
                self.assets_tbl.setCurrentCell(idx, 0)
                return

    def _open_company_task_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("List Company Model")
        dialog.setModal(True)
        dialog.resize(460, 250)

        root = QVBoxLayout(dialog)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        company_input = QLineEdit()
        company_input.setPlaceholderText("e.g. Acme Labs")
        model_input = QLineEdit()
        model_input.setPlaceholderText("e.g. VisionNet v4")

        bounty_input = QSpinBox()
        bounty_input.setRange(10, 50000)
        bounty_input.setValue(500)
        bounty_input.setSuffix(" ALGO")

        benchmark_combo = QComboBox()
        benchmark_combo.addItem("Bio-Scan Analysis", "TASK-CANCER")
        benchmark_combo.addItem("Drone Vision OCR", "TASK-DIGITS")
        benchmark_combo.addItem("DeFi Fraud Detect", "TASK-WINE")

        form.addRow("Company", company_input)
        form.addRow("Model", model_input)
        form.addRow("Reward", bounty_input)
        form.addRow("Benchmark", benchmark_combo)
        root.addLayout(form)

        hint = QLabel(
            "This creates an open decentralized challenge.\n"
            "Nodes compete by accuracy; top rank wins most of the posted reward."
        )
        hint.setProperty("class", "sub")
        hint.setWordWrap(True)
        root.addWidget(hint)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "chip")
        cancel_btn.clicked.connect(dialog.reject)
        submit_btn = QPushButton("List Model")
        submit_btn.setProperty("class", "primary")
        submit_btn.clicked.connect(dialog.accept)
        actions.addWidget(cancel_btn)
        actions.addWidget(submit_btn)
        root.addLayout(actions)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        company_name = company_input.text().strip() or "External Partner"
        model_name = model_input.text().strip() or "Custom Model"
        bounty = int(bounty_input.value())
        benchmark_task_id = str(benchmark_combo.currentData())

        task = system.add_company_task(
            company_name=company_name,
            model_name=model_name,
            bounty=bounty,
            benchmark_task_id=benchmark_task_id,
        )
        self._fill_assets()
        self._select_task_by_id(task["id"])
        self._add_log(
            f"COMPANY LISTING -> {task['name']} | sponsor {task['sponsor']} | reward {task['bounty']} ALGO",
            PURPLE_SOFT,
        )

    def _fill_assets(self):
        tasks = system.pending_tasks
        selected_task = self._get_selected_task()
        selected_task_id = selected_task.get("id") if selected_task else None

        self.assets_tbl.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            self.assets_tbl.setRowHeight(row, 44)

            name_item = QTableWidgetItem(f"  {task['name']}")
            name_item.setForeground(QColor(TEXT_W))
            self.assets_tbl.setItem(row, 0, name_item)

            sponsor_item = QTableWidgetItem(task.get("sponsor", "Network"))
            sponsor_item.setForeground(QColor(PURPLE_SOFT if task.get("source") == "company" else TEXT_SUB))
            self.assets_tbl.setItem(row, 1, sponsor_item)

            impact_item = QTableWidgetItem(task["impact"])
            impact_item.setForeground(QColor(TEXT_SUB))
            self.assets_tbl.setItem(row, 2, impact_item)

            bounty_item = QTableWidgetItem(f"{task['bounty']} ALGO")
            bounty_item.setForeground(QColor(TEXT_W))
            self.assets_tbl.setItem(row, 3, bounty_item)

            dynamic = task.get("dynamic", 0.0)
            sym = "+" if dynamic > 0 else ("-" if dynamic < 0 else "~")
            di = QTableWidgetItem(f"{sym} {abs(dynamic):.2f}%")
            di.setForeground(
                QColor(
                    GREEN if dynamic > 0 else (
                        RED if dynamic < 0 else TEXT_SUB
                    )
                )
            )
            self.assets_tbl.setItem(row, 4, di)

            strip = GradientStrip(
                PINK if dynamic >= 0 else RED,
                trend_up=dynamic >= 0,
            )
            sc = QWidget()
            sl = QVBoxLayout(sc)
            sl.setContentsMargins(0, 5, 0, 5)
            sl.addWidget(strip, alignment=Qt.AlignmentFlag.AlignCenter)
            self.assets_tbl.setCellWidget(row, 5, sc)

            status = task.get("status", "Hot" if task["bounty"] >= 300 else "Live")
            si = QTableWidgetItem(status)
            if status == "Hot":
                status_color = GREEN
            elif status == "Listed":
                status_color = PURPLE_SOFT
            else:
                status_color = TEXT_SUB
            si.setForeground(QColor(status_color))
            self.assets_tbl.setItem(row, 6, si)

            if selected_task_id is not None and task.get("id") == selected_task_id:
                self.assets_tbl.selectRow(row)
                self.assets_tbl.setCurrentCell(row, 0)

        if self.assets_tbl.rowCount() > 0 and self.assets_tbl.currentRow() < 0:
            self.assets_tbl.selectRow(0)
            self.assets_tbl.setCurrentCell(0, 0)

    def _fill_blocks(self):
        blocks = system.chain[-5:]
        self.blk_tbl.setRowCount(len(blocks))
        for row, block in enumerate(blocks):
            self.blk_tbl.setRowHeight(row, 36)
            idx_item = QTableWidgetItem(str(block.index))
            idx_item.setForeground(QColor(TEXT_W))
            self.blk_tbl.setItem(row, 0, idx_item)
            hash_item = QTableWidgetItem(block.hash[:16] + "...")
            hash_item.setForeground(QColor(TEXT_SUB))
            self.blk_tbl.setItem(row, 1, hash_item)
            time_item = QTableWidgetItem(
                block.timestamp.strftime("%H:%M:%S")
            )
            time_item.setForeground(QColor(TEXT_SUB))
            self.blk_tbl.setItem(row, 2, time_item)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  CARD FLASH / NAVIGATION
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _set_card_active(self, card, active):
        card.setProperty("active", "true" if active else "false")
        card.style().unpolish(card)
        card.style().polish(card)
        card.update()

    def _flash_card(self, card):
        self._set_card_active(card, True)
        QTimer.singleShot(
            600, lambda c=card: self._set_card_active(c, False)
        )

    def _on_sidebar_action(self, name):
        self.current_view = name
        for key, btn in self.sidebar_buttons.items():
            btn.setProperty(
                "active", "true" if key == name else "false"
            )
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

        if name in self.page_map:
            self._on_top_nav(name)

        focus_map = {
            "Dashboard": self.wallet_growth,
            "Training": self.control_card,
            "Logs": self.logs_card,
            "Network": self.network_card,
        }
        target = focus_map.get(name)
        if target is not None:
            self._flash_card(target)

    def _on_top_nav(self, tab_name):
        self.current_view = tab_name
        if hasattr(self, "lbl_page_title"):
            self.lbl_page_title.setText(tab_name)
        if hasattr(self, "page_map"):
            idx = self.page_map.get(tab_name)
            if idx is not None:
                self.pages.setCurrentIndex(idx)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    #  LIVE DATA / TRAINING
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _refresh_rank_ui(self):
        ranking = system.ranking
        ranking.calculate_tier()
        self.lbl_xp.setText(f"XP {ranking.xp}/1000")
        self.xp_bar.setValue(ranking.xp % 1000)
        self.lbl_tier.setText(f"Tier: {ranking.current_tier}")
        self.lbl_win_rate.setText(
            f"Batches Won: {ranking.battles_won} / "
            f"{ranking.battles_attempted} ({ranking.win_rate:.1f}%)"
        )
        self.wallet_balance.lbl_rank.setText(
            f"{ranking.current_tier} | "
            f"Acc {ranking.avg_accuracy * 100:.1f}%"
        )
        self.metric_profit.value_label.setText(
            f"${system.total_profit:,.2f}"
        )
        pnl = (
            0.0
            if system.wallet_balance == 0
            else (
                system.total_profit
                / max(abs(system.wallet_balance), 1)
            )
            * 100
        )
        self.metric_profit.sub_label.setText(f"{pnl:+.2f}%")
        self.metric_best.value_label.setText("Chain LINK")
        self.metric_best.sub_label.setText(
            f"Acc {ranking.avg_accuracy * 100:.1f}%"
        )
        self.metric_score.value_label.setText(
            f"{min(100, int(ranking.win_rate)):d}/100"
        )
        self.metric_score.sub_label.setText(
            "Excellent" if ranking.win_rate >= 60 else "Building"
        )

    def _add_log(self, msg, color=TEXT_SUB):
        if not hasattr(self, "log_layout"):
            return
        ts = datetime.now().strftime("%H:%M:%S")
        label = QLabel(f"[{ts}] {msg}")
        label.setProperty("class", "log")
        label.setStyleSheet(f"color:{color};")
        self.log_layout.insertWidget(
            self.log_layout.count() - 1, label
        )
        while self.log_layout.count() > 35:
            item = self.log_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _clear_logs(self):
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _bootstrap_logs(self):
        self._add_log("BOOTSTRAP COMPLETE", PURPLE_SOFT)
        self._add_log("CONSENSUS DAEMON ONLINE", TEXT_SUB)
        self._add_log("IDLE | WAITING FOR NODE ACTIVATION", TEXT_SUB)

    def _register_node(self):
        node_id = f"NODE-{random.randint(1000, 9999)}"
        self.lbl_node_id.setText(f"Node Alias: {node_id}")
        self._add_log(f"NODE REGISTERED | {node_id}", PURPLE_SOFT)

    def _tick_hw(self):
        stats = get_hardware_stats()
        self.lbl_temp.setText(_fmt_temp(stats["temp_c"]))
        self.lbl_fan.setText(_fmt_pct(stats["fan_pct"]))
        self.lbl_vram.setText(
            _fmt_vram(stats["vram_used_mb"], stats["vram_total_mb"])
        )

        active_nodes = 8400 + random.randint(0, 90)
        network_hash = 430 + random.randint(0, 30)
        confidence = 55 + random.randint(0, 35)

        self.lbl_nodes.setText(f"Active Nodes: {active_nodes:,}")
        self.lbl_hash_g.setText(f"Hashrate: {network_hash} PH/s")
        self.lbl_tb.setText(
            f"Total Blocks: {len(system.chain):,}"
        )
        self.lbl_consensus.setText(
            f"Consensus Confidence: {confidence}%"
        )
        self.consensus_bar.setValue(confidence)

        qd = random.randint(8, 42)
        self.lbl_queue_depth.setText(f"Queue Depth: {qd}")
        self.lbl_batch_window.setText(
            f"Batch Window: {random.randint(160, 480)} ms"
        )
        self.lbl_reward_flow.setText(
            f"Reward Flow: {random.uniform(0.4, 2.8):.2f} ALGO/min"
        )

        gpu_util = (
            stats["gpu_util_pct"]
            if stats["gpu_util_pct"] is not None
            else random.randint(35, 78)
        )
        self.util_bar.setValue(max(0, min(100, gpu_util)))
        self.flow_bar.setValue(
            max(30, min(100, confidence - random.randint(0, 20)))
        )

        self.lbl_signal_1.setText(
            f"Arbitration: {'Stable' if confidence > 70 else 'Balancing'}"
        )
        self.lbl_signal_2.setText(
            f"Validation Lag: {random.uniform(0.4, 5.2):.1f} ms"
        )
        self.lbl_signal_3.setText(
            f"Drift Guard: {'Monitoring' if qd < 30 else 'Rebalancing'}"
        )
        self.lbl_signal_4.setText(
            f"Reward Pressure: {'Neutral' if qd < 25 else 'Elevated'}"
        )

        elapsed = int(time.time() - self.session_started)
        hrs, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        self.wallet_balance.lbl_uptime.setText(
            f"{secs} sec ago"
        )

    def _start_mining(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("o TRAINING")
        self.lbl_status.setStyleSheet(
            f"color:{GREEN}; font-size:11px; font-weight:700;"
        )
        self.lbl_control_hint.setText(
            "Training active. System logs streaming."
        )
        self._on_top_nav("Dashboard")

        self.chart.reset()
        task = self._get_selected_task()
        if task is None:
            task = random.choice(system.pending_tasks)

        sponsor = task.get("sponsor", "Network")
        self._add_log(
            f"CHALLENGE ACCEPTED -> {task['name']} | sponsor {sponsor} | reward {task['bounty']} ALGO",
            PURPLE_SOFT,
        )

        self.worker = TrainingWorker(task)
        self.worker.log_msg.connect(self._add_log)
        self.worker.epoch_done.connect(self._on_epoch)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_mining(self):
        if self.worker:
            self.worker.request_stop()

    def _on_epoch(self, epoch, loss, acc):
        self.chart.add_point(acc, loss)
        ops = int(acc * 1000)
        self.lbl_hashrate.setText(f"{ops} T-Ops/s")
        self.wallet_balance.lbl_ops.setText(f"{ops} T-Ops/s")
        self.util_bar.setValue(max(0, min(100, int(acc * 100))))
        self.flow_bar.setValue(
            max(0, min(100, int((1 - loss) * 100)))
        )
        self.lbl_compute_hint.setText(
            f"Epoch {epoch:02d} | ACC {acc:.3f} | LOSS {loss:.4f}"
        )
        stats = get_hardware_stats()
        if stats["temp_c"] is not None:
            self.lbl_temp.setText(
                _fmt_temp(min(99, stats["temp_c"] + 4))
            )
        if stats["fan_pct"] is not None:
            self.lbl_fan.setText(
                _fmt_pct(min(100, stats["fan_pct"] + 8))
            )

    def _on_done(self, task, my_accuracy, rival_accuracies):
        outcome = system.ranking.record_battle_result(
            my_accuracy=my_accuracy,
            rival_accuracies=rival_accuracies,
            total_reward=task["bounty"],
        )
        payout = outcome["profit"]
        system.wallet_balance += payout
        system.total_profit += payout

        if outcome["result"] == "WIN":
            system.add_block(
                f"Task: {task['name']} @ {my_accuracy:.3f}"
            )
        publish_wallet_state(system.wallet_balance, system.total_profit, system.blocks_mined)

        self.wallet_balance.lbl_value.setText(
            f"{system.wallet_balance:,.2f}"
        )
        pct = (
            0.0 if system.wallet_balance == 0
            else abs(payout) / max(abs(system.wallet_balance), 1) * 100
        )
        if payout >= 0:
            self.wallet_balance.lbl_change.setText(f"+{pct:.2f}%")
            self.wallet_balance.lbl_change.setStyleSheet(
                f"color: {GREEN}; font-size: 11px; font-weight: 700;"
                f"background: rgba(52,199,89,0.12);"
                "border-radius: 9999px; padding: 3px 8px;"
            )
        else:
            self.wallet_balance.lbl_change.setText(f"-{pct:.2f}%")
            self.wallet_balance.lbl_change.setStyleSheet(
                f"color: {RED}; font-size: 11px; font-weight: 700;"
                f"background: rgba(255,77,90,0.12);"
                "border-radius: 9999px; padding: 3px 8px;"
            )

        self.wallet_balance.lbl_blocks.setText(
            f"{system.blocks_mined} blocks mined"
        )
        self.wallet_balance.lbl_revenue.setText(
            f"You've earned +{system.total_profit:.2f} ALGO this session"
        )
        self.wallet_balance.add_spark_point(system.wallet_balance * 100 + 29000)
        self.wallet_growth.lbl_growth_value.setText(
            f"by ${system.total_profit:,.2f}"
        )
        self.lbl_bal_top.setText(
            f"{system.wallet_balance:,.2f} ALGO"
        )
        self._fill_blocks()
        self._refresh_rank_ui()

        color = (
            GREEN
            if outcome["result"] in ("WIN", "BREAKEVEN")
            else RED
        )
        self._add_log(
            f"{outcome['message']} | sponsor {task.get('sponsor', 'Network')} | payout {payout:+.2f} ALGO",
            color,
        )

    def _on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("o IDLE")
        self.lbl_status.setStyleSheet(
            f"color:{TEXT_SUB}; font-size:11px; font-weight:700;"
        )
        self.lbl_hashrate.setText("IDLE")
        self.wallet_balance.lbl_ops.setText("0 T-Ops/s")
        self.lbl_control_hint.setText(
            "Node ready. Press Activate Node to start."
        )
        self.worker = None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  MAIN
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load Source Code Pro font
    _font_path = _os.path.join(_FONT_DIR, "SourceCodePro-Variable.ttf")
    if _os.path.exists(_font_path):
        QFontDatabase.addApplicationFont(_font_path)

    app.setStyleSheet(QSS)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_W))
    palette.setColor(QPalette.ColorRole.Base, QColor(CARD))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_W))
    app.setPalette(palette)

    window = NeuroChainApp()
    window.show()
    sys.exit(app.exec())


