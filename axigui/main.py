import sys
from typing import Tuple

import vpype
from PySide2.QtGui import QPalette, QColor, Qt
from PySide2.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QApplication,
    QWidget,
    QTabWidget,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy, QToolBar,
)

from .axy import axy
from .config_dialog import ConfigDialog
from .vector_data_plot_widget import VectorDataPlotWidget


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


class PlotControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        vd = vpype.VectorData()
        vd.add(vpype.LineCollection([(0, 100), (200, 101 + 101j)]), 1)
        self.base_vector_data = vd
        self.vector_data = vd
        self.page_format = "A4"
        self.plot = VectorDataPlotWidget()
        self.update_plot()

        # setup button
        pen_up_btn = QPushButton("UP")
        pen_down_btn = QPushButton("DOWN")
        pen_up_btn.clicked.connect(lambda: axy.pen_up())
        pen_down_btn.clicked.connect(lambda: axy.pen_down())

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
        root_layout.setSpacing(0)
        root_layout.setMargin(0)
        root_layout.addWidget(self.plot)
        root_layout.addWidget(btn_widget)
        self.setLayout(root_layout)

    def update_plot(self):
        self.vector_data = vpype.VectorData()
        self.vector_data.extend(self.base_vector_data)
        self.plot.vector_data = self.vector_data
        self.plot.page_format = PAGE_FORMATS["A4"]


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._toolbar = QToolBar()
        load_act = self._toolbar.addAction("Load")
        config_act = self._toolbar.addAction("Config")
        config_act.triggered.connect(lambda: ConfigDialog().exec_())

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(PlotControlWidget())
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
