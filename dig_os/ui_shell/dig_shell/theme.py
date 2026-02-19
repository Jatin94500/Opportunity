def build_stylesheet() -> str:
    return """
    QWidget {
        color: #F1F0F8;
        background: transparent;
        font-family: Inter, "Noto Sans", "Segoe UI", sans-serif;
        font-size: 11px;
        font-weight: 400;
    }

    QMainWindow {
        background-color: #17142A;
    }

    QFrame#topBar {
        background-color: rgba(15, 13, 28, 205);
        border-bottom: 1px solid rgba(255, 255, 255, 22);
    }

    QLabel#topCenterStatus {
        color: #FBFAFF;
        font-size: 11px;
        font-weight: 600;
    }

    QLabel#trayLabel {
        color: #E8E4F5;
        font-size: 11px;
        font-weight: 500;
        padding: 0 3px;
    }

    QPushButton#flatTopButton {
        border: 1px solid rgba(255, 255, 255, 24);
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 10);
        color: #FBFAFF;
        padding: 2px 10px;
        font-weight: 500;
    }

    QPushButton#workspaceButton {
        border: 1px solid rgba(255, 255, 255, 18);
        border-radius: 8px;
        min-width: 24px;
        min-height: 20px;
        max-width: 24px;
        max-height: 20px;
        background-color: rgba(255, 255, 255, 9);
        padding: 0px;
        font-weight: 600;
    }

    QPushButton#workspaceButton:checked {
        border: 1px solid rgba(255, 194, 225, 110);
        background-color: rgba(255, 194, 225, 35);
    }

    QFrame#bottomDock {
        background-color: rgba(10, 9, 20, 188);
        border: 1px solid rgba(255, 255, 255, 26);
        border-radius: 12px;
    }

    QToolButton#startButton {
        border: 1px solid rgba(255, 194, 225, 95);
        border-radius: 9px;
        background-color: rgba(255, 188, 221, 22);
        padding: 4px;
    }

    QToolButton#startButton:hover {
        background-color: rgba(255, 188, 221, 40);
        border: 1px solid rgba(255, 217, 236, 130);
    }

    QToolButton#dockButton {
        border: 1px solid transparent;
        border-radius: 9px;
        background-color: transparent;
        padding: 5px;
    }

    QToolButton#dockButton:hover {
        border: 1px solid rgba(255, 255, 255, 28);
        background-color: rgba(255, 255, 255, 14);
    }

    QToolButton#shellControl,
    QToolButton#shellControlClose {
        min-width: 22px;
        min-height: 22px;
        max-width: 22px;
        max-height: 22px;
        border-radius: 7px;
        font-size: 12px;
        font-weight: 600;
        padding: 0px;
    }

    QToolButton#shellControl {
        border: 1px solid rgba(255, 255, 255, 24);
        background-color: rgba(255, 255, 255, 10);
        color: #F7F5FF;
    }

    QToolButton#shellControl:hover {
        border: 1px solid rgba(255, 255, 255, 34);
        background-color: rgba(255, 255, 255, 16);
    }

    QToolButton#shellControlClose {
        border: 1px solid rgba(255, 120, 133, 80);
        background-color: rgba(255, 90, 120, 28);
        color: #FFD6DE;
    }

    QToolButton#shellControlClose:hover {
        border: 1px solid rgba(255, 120, 133, 130);
        background-color: rgba(255, 90, 120, 40);
    }

    QFrame#panelWindow {
        background-color: rgba(15, 13, 28, 178);
        border: 1px solid rgba(255, 255, 255, 24);
        border-radius: 10px;
    }

    QFrame#panelHeader {
        background-color: rgba(24, 21, 45, 226);
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
        border-bottom: 1px solid rgba(255, 255, 255, 18);
    }

    QLabel#panelTitle {
        color: #FAF9FF;
        font-size: 11px;
        font-weight: 600;
    }

    QPushButton#windowControl {
        border: 1px solid rgba(255, 255, 255, 24);
        border-radius: 4px;
        background-color: rgba(255, 255, 255, 10);
        color: #EDE8F8;
        font-size: 10px;
        font-weight: 600;
        padding: 0px;
    }

    QPushButton#windowControl:hover {
        border: 1px solid rgba(255, 255, 255, 34);
        background-color: rgba(255, 255, 255, 16);
    }

    QFrame#panelBody {
        background-color: rgba(13, 12, 25, 164);
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
    }

    QLabel#sectionTitle {
        color: #FFFFFF;
        font-size: 13px;
        font-weight: 600;
    }

    QLabel#minorText {
        color: #E0DAF0;
        font-size: 11px;
        font-weight: 500;
    }

    QLabel#metricLabel {
        color: #FFFFFF;
        font-weight: 700;
    }

    QFrame#metricTile {
        background-color: rgba(21, 18, 40, 210);
        border: 1px solid rgba(255, 255, 255, 22);
        border-radius: 8px;
    }

    QFrame#balanceStrip {
        background-color: rgba(13, 11, 30, 210);
        border: 1px solid rgba(255, 255, 255, 25);
        border-radius: 12px;
    }

    QLabel#balanceValue {
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 700;
    }

    QLabel#balanceDelta {
        color: #B7F4CB;
        background-color: rgba(183, 244, 203, 24);
        border: 1px solid rgba(183, 244, 203, 80);
        border-radius: 9999px;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: 700;
    }

    QFrame#balanceBar {
        background-color: rgba(136, 192, 208, 80);
        border-radius: 1px;
    }

    QFrame#pathRow {
        background-color: rgba(22, 19, 42, 205);
        border: 1px solid rgba(255, 255, 255, 22);
        border-radius: 6px;
    }

    QToolButton#fileGridItem {
        border: 1px solid transparent;
        border-radius: 6px;
        min-width: 72px;
        min-height: 68px;
        padding: 4px;
        font-weight: 500;
    }

    QToolButton#fileGridItem:hover {
        border: 1px solid rgba(255, 255, 255, 30);
        background-color: rgba(255, 255, 255, 12);
    }

    QFrame#lockCard {
        min-width: 440px;
        background-color: rgba(18, 16, 37, 220);
        border: 1px solid rgba(255, 255, 255, 26);
        border-radius: 12px;
    }

    QLabel#bootTitle {
        color: #FFFFFF;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    QLabel#bootText {
        color: #F2ECFB;
        font-size: 12px;
        font-weight: 500;
    }

    QPushButton {
        border: 1px solid rgba(255, 255, 255, 24);
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 10);
        color: #FCF7FF;
        padding: 5px 10px;
        font-weight: 500;
    }

    QPushButton:hover {
        border: 1px solid rgba(255, 255, 255, 36);
        background-color: rgba(255, 255, 255, 16);
    }

    QPushButton:pressed {
        background-color: rgba(255, 255, 255, 22);
    }

    QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTabWidget::pane {
        background-color: rgba(14, 13, 30, 188);
        border: 1px solid rgba(255, 255, 255, 22);
        border-radius: 8px;
        color: #FCF7FF;
        font-weight: 400;
    }

    QPlainTextEdit#terminalOutput {
        font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
        background-color: rgba(12, 12, 23, 230);
        border: 1px solid rgba(255, 255, 255, 20);
    }

    QTabBar::tab {
        background: rgba(255, 255, 255, 10);
        border: 1px solid rgba(255, 255, 255, 18);
        border-radius: 8px;
        padding: 6px 10px;
        margin-right: 4px;
        font-weight: 500;
    }

    QTabBar::tab:selected {
        border: 1px solid rgba(255, 255, 255, 34);
        background: rgba(255, 255, 255, 18);
    }

    QSlider::groove:horizontal {
        border: 1px solid rgba(255, 255, 255, 22);
        height: 6px;
        background: rgba(15, 13, 29, 210);
        border-radius: 3px;
    }

    QSlider::handle:horizontal {
        background: #FFC2E1;
        border: 1px solid rgba(255, 194, 225, 150);
        width: 12px;
        margin: -5px 0;
        border-radius: 6px;
    }

    QMenu {
        background-color: rgba(14, 13, 30, 238);
        border: 1px solid rgba(255, 255, 255, 24);
        border-radius: 10px;
        padding: 6px;
    }

    QMenu::item {
        font-weight: 500;
    }

    QMenu::item:selected {
        background-color: rgba(255, 255, 255, 12);
        border-radius: 6px;
    }

    QMenu#startMenu::item {
        padding: 8px 10px;
    }

    QFrame#browserChrome {
        background-color: rgba(244, 247, 252, 240);
        border: 1px solid rgba(20, 20, 20, 38);
        border-radius: 10px;
    }

    QFrame#browserTabChip {
        background-color: rgba(255, 255, 255, 225);
        border: 1px solid rgba(20, 20, 20, 38);
        border-radius: 8px;
        color: #1E2230;
        font-weight: 600;
    }

    QToolButton#browserNavButton {
        background-color: rgba(0, 0, 0, 0);
        border: 1px solid rgba(20, 20, 20, 28);
        border-radius: 8px;
        color: #1E2230;
        padding: 5px;
        font-weight: 500;
    }

    QToolButton#browserNavButton:hover {
        background-color: rgba(19, 110, 245, 25);
        border: 1px solid rgba(19, 110, 245, 60);
    }

    QFrame#browserAddressBar {
        background-color: rgba(255, 255, 255, 230);
        border: 1px solid rgba(20, 20, 20, 30);
        border-radius: 12px;
    }

    QLineEdit#browserUrlInput {
        background: transparent;
        border: none;
        color: #1E2230;
        font-size: 12px;
        font-weight: 500;
    }

    QToolButton#browserOpenButton {
        border: 1px solid rgba(20, 20, 20, 30);
        border-radius: 8px;
        padding: 5px 10px;
        background-color: rgba(255, 255, 255, 220);
        color: #1E2230;
        font-weight: 600;
    }

    QToolButton#browserOpenButton:hover {
        background-color: rgba(19, 110, 245, 22);
        border: 1px solid rgba(19, 110, 245, 60);
    }

    QLabel#browserStatus {
        color: #E8E4F5;
        font-size: 11px;
        font-weight: 500;
        padding-left: 4px;
    }

    QFrame#jupyterControls {
        background: transparent;
    }
    """
