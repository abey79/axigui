import sys
from typing import Tuple

import vpype
from PySide2.QtCore import QSettings
from PySide2.QtGui import QPalette, QColor, Qt
from PySide2.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QApplication,
    QWidget,
    QFormLayout,
    QComboBox,
    QTabWidget,
    QSpinBox,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
)

from .axy_stub import Axy
from .vector_data_plot_widget import VectorDataPlotWidget

axy = Axy()


def _mm_to_px(x: float, y: float) -> Tuple[float, float]:
    return x * 96.0 / 25.4, y * 96.0 / 25.4


PAGE_FORMATS = {
    "A6": _mm_to_px(105.0, 148.0),
    "A5": _mm_to_px(148.0, 210.0),
    "A4": _mm_to_px(210.0, 297.0),
    "A3": _mm_to_px(297.0, 420.0),
    "Letter": _mm_to_px(215.9, 279.4),
    "Legal": _mm_to_px(215.9, 355.6),
    "Executive": _mm_to_px(185.15, 266.7),
}


class ConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        options = {
            "pen_pos_down": ("Pen position down:", (0, 100), 40),
            "pen_pos_up": ("Pen position up:", (0, 100), 60),
            "pen_rate_lower": ("Pen rate lower:", (1, 100), 50),
            "pen_rate_raise": ("Pen rate raise:", (1, 100), 75),
            "pen_delay_down": ("Pen delay down:", (-500, 500), 0),
            "pen_delay_up": ("Pen delay up:", (-500, 500), 0),
            "speed_pendown": ("Speed (pen down):", (1, 110), 25),
            "speed_penup": ("Speed (pen up):", (1, 110), 75),
            "accel": ("Acceleration:", (1, 100), 75),
        }

        settings = QSettings()
        layout = QFormLayout()

        class SettingUpdater:
            def __init__(self, k):
                self.key = k

            def __call__(self, value):
                settings.setValue(self.key, value)

        for key, (label, (min_val, max_val), default) in options.items():
            spin_box = QSpinBox()
            spin_box.setRange(min_val, max_val)
            spin_box.valueChanged.connect(lambda value: axy.set_option(key, value))
            spin_box.setValue(settings.value(key, default))
            spin_box.setSingleStep(1)
            spin_box.valueChanged.connect(SettingUpdater(key))
            layout.addRow(label, spin_box)

        model = QComboBox()
        model.addItem("Axidraw V2 or V3", 1)
        model.addItem("Axidraw V3/A3 or SE/A3", 2)
        model.addItem("Axidraw V3 XLX", 3)
        model.addItem("Axidraw MiniKit", 4)
        model.currentIndexChanged.connect(
            lambda index: axy.set_option("model", model.itemData(index))
        )
        model.setCurrentIndex(settings.value("model", 0))
        model.currentIndexChanged.connect(
            lambda index: settings.setValue("model", index)
        )
        layout.addRow("Model:", model)

        self.setLayout(layout)


class PlotControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # setup button
        pen_up_btn = QPushButton("UP")
        pen_down_btn = QPushButton("DOWN")
        pen_up_btn.clicked.connect(lambda: axy.pen_up())
        pen_down_btn.clicked.connect(lambda: axy.pen_down())

        # setup plot
        self.plot = VectorDataPlotWidget()
        vd = vpype.VectorData()
        vd.add(vpype.LineCollection([(0, 100), (200, 101 + 101j)]), 1)
        self.plot.vector_data = vd
        self.plot.page_format = PAGE_FORMATS['A4']

        # button layout
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(pen_up_btn)
        btn_layout.addWidget(pen_down_btn)
        btn_layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)

        # setup layout
        root_layout = QHBoxLayout()
        root_layout.addWidget(self.plot)
        root_layout.addWidget(btn_widget)
        self.setLayout(root_layout)


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._tab_widget = QTabWidget()
        self._tab_widget.addTab(PlotControlWidget(), "Plot")
        self._tab_widget.addTab(ConfigWidget(), "Config")

        layout = QVBoxLayout()
        layout.addWidget(self._tab_widget)
        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)

    # styling
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    app.setStyleSheet(
        """
QSpinBox {
    padding-right: 1px; /* make room for the arrows */
    padding-left: 1px; /* make room for the arrows */
}

QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top left; /* position at the top right corner */

    width: 32px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
    height: 24px
}

QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right; /* position at bottom right corner */
    width: 32px;
    height: 24px;
}

QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }
"""
    )

    app.setApplicationName("axigui")
    app.setOrganizationName("Antoine Beyeler")
    app.setOrganizationDomain("ab-ware.com")

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
