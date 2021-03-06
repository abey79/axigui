import copy
import io
import math
import sys
from typing import Tuple

import vpype
from PySide2.QtCore import QSettings, QSize, QCoreApplication, Qt
from PySide2.QtGui import (
    QPalette,
    QColor,
    QStandardItemModel,
    QStandardItem,
    QPixmap,
    QIcon,
)
from PySide2.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QApplication,
    QWidget,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QToolBar,
    QGroupBox,
    QComboBox,
    QFormLayout,
    QCheckBox,
    QDoubleSpinBox,
    QListView,
    QFileDialog,
)

from .axy import axy
from .config_dialog import ConfigDialog, AxySettingsSpinBox
from .utils import UnitComboBox
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
    # noinspection PyTypeChecker
    def __init__(self, parent=None):
        super().__init__(parent)

        # setup settings for the class
        self.settings = QSettings()
        self.settings.beginGroup("plot_control")

        self.base_vector_data = vpype.VectorData()
        self.vector_data: vpype.VectorData = None

        # settings
        self.page_format: str = self.settings.value("page_format", "A4")
        self.landscape: bool = self.settings.value("landscape", False)
        self.rotated: bool = self.settings.value("rotate", False)
        self.rotated: bool = self.settings.value("rotated", False)
        self.center: bool = self.settings.value("center", True)
        self.fit_page: bool = self.settings.value("fit_page", False)
        self.margin_value: float = self.settings.value("margin_value", 2.0)
        self.margin_unit: str = self.settings.value("margin_unit", "cm")

        # setup plot area
        self.plot = VectorDataPlotWidget()
        self.plot.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        # page layout controls
        page_box = QGroupBox("Page layout")
        page_layout = QFormLayout()
        page_format_combo = QComboBox()
        for k in PAGE_FORMATS:
            page_format_combo.addItem(k)
        page_format_combo.setCurrentText(self.page_format)
        page_format_combo.currentTextChanged.connect(lambda text: self.set_page_format(text))
        landscape_check = QCheckBox("Landscape")
        landscape_check.setChecked(self.landscape)
        landscape_check.stateChanged.connect(
            lambda: self.set_landscape(landscape_check.isChecked())
        )
        rotated_check = QCheckBox("Rotated")
        rotated_check.setChecked(self.landscape)
        rotated_check.stateChanged.connect(lambda: self.set_rotated(rotated_check.isChecked()))
        center_check = QCheckBox("Center on page")
        center_check.setChecked(self.center)
        center_check.stateChanged.connect(lambda: self.set_center(center_check.isChecked()))
        fit_page_check = QCheckBox("Fit to page")
        fit_page_check.setChecked(self.fit_page)
        fit_page_check.stateChanged.connect(
            lambda: self.set_fit_page(fit_page_check.isChecked())
        )
        margin_layout = QHBoxLayout()
        margin_spin = QDoubleSpinBox()
        margin_spin.setValue(self.margin_value)
        margin_spin.valueChanged.connect(
            lambda: self.set_margin(margin_spin.value(), margin_unit.currentText())
        )
        margin_unit = UnitComboBox()
        margin_unit.setCurrentText(self.margin_unit)
        margin_unit.currentTextChanged.connect(
            lambda: self.set_margin(margin_spin.value(), margin_unit.currentText())
        )
        margin_layout.addWidget(margin_spin)
        margin_layout.addWidget(margin_unit)
        page_layout.addRow("Page format:", page_format_combo)
        page_layout.addRow("", landscape_check)
        page_layout.addRow("", rotated_check)
        page_layout.addRow("", center_check)
        page_layout.addRow("", fit_page_check)
        page_layout.addRow("Margin:", margin_layout)
        page_box.setLayout(page_layout)

        # Action buttons
        pen_up_btn = QPushButton("UP")
        pen_down_btn = QPushButton("DOWN")
        pen_up_btn.clicked.connect(lambda: axy.pen_up())
        pen_down_btn.clicked.connect(lambda: axy.pen_down())
        pen_up_spin = AxySettingsSpinBox(self.settings, "pen_pos_up", 60.0)
        pen_down_spin = AxySettingsSpinBox(self.settings, "pen_pos_down", 40.0)
        pen_up_layout = QHBoxLayout()
        pen_up_layout.addWidget(pen_up_spin)
        pen_up_layout.addWidget(pen_up_btn)
        pen_down_layout = QHBoxLayout()
        pen_down_layout.addWidget(pen_down_spin)
        pen_down_layout.addWidget(pen_down_btn)
        shutdown_btn = QPushButton("OFF")
        shutdown_btn.clicked.connect(lambda: axy.shutdown())
        plot_btn = QPushButton("PLOT")
        plot_btn.clicked.connect(lambda: self.plot_svg())
        action_box = QGroupBox("Actions")
        action_layout = QFormLayout()
        action_layout.addRow("Pen up: ", pen_up_layout)
        action_layout.addRow("Pen down: ", pen_down_layout)
        action_layout.addRow("Motor off:", shutdown_btn)
        action_layout.addRow("Plot:", plot_btn)
        action_box.setLayout(action_layout)

        self.list = QListView()
        self.list.setFixedHeight(120)
        self.list.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))

        # controls layout
        controls_layout = QVBoxLayout()
        controls_layout.addWidget(self.list)
        controls_layout.addWidget(page_box)
        controls_layout.addWidget(action_box)
        controls_layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # setup layout
        root_layout = QHBoxLayout()
        root_layout.addWidget(self.plot)
        root_layout.addLayout(controls_layout)
        self.setLayout(root_layout)

        self.update_view()

        # FIXME: stub vector data
        # vd = vpype.VectorData()
        # vd.add(vpype.LineCollection([(0, 100), (200, 1001 + 201j)]), 1)
        # vd.add(vpype.LineCollection([(0, 100 + 100j), (300j, 400j + 100)]), 2)
        self.load_svg("/Users/hhip/Drive/axidraw/wheel_cards/wheel_card_triple_5_40.svg")
        # self.load_svg("/Users/hhip/Downloads/spirograph-grids/spirograph-grid.svg")

    def add_actions(self, toolbar: QToolBar):
        colorful_act = toolbar.addAction(QIcon("images/icons_colorful.png"), "Colorful")
        colorful_act.setCheckable(True)
        colorful_act.setChecked(self.plot.colorful)
        colorful_act.triggered.connect(lambda checked: setattr(self.plot, "colorful", checked))

        show_points_act = toolbar.addAction(QIcon("images/icons_show_points.png"), "Points")
        show_points_act.setCheckable(True)
        show_points_act.setChecked(self.plot.show_points)
        show_points_act.triggered.connect(
            lambda checked: setattr(self.plot, "show_points", checked)
        )

        show_pen_up_act = toolbar.addAction(QIcon("images/icons_show_pen_up.png"), "Pen-Up")
        show_pen_up_act.setCheckable(True)
        show_pen_up_act.setChecked(self.plot.show_pen_up)
        show_pen_up_act.triggered.connect(
            lambda checked: setattr(self.plot, "show_pen_up", checked)
        )

        show_axes_act = toolbar.addAction(QIcon("images/icons_show_axes.png"), "Axes")
        show_axes_act.setCheckable(True)
        show_axes_act.setChecked(self.plot.show_axes)
        show_axes_act.triggered.connect(
            lambda checked: setattr(self.plot, "show_axes", checked)
        )

        scale = UnitComboBox()
        scale.setCurrentText(self.plot.unit)
        scale.currentTextChanged.connect(lambda text: setattr(self.plot, "unit", text))
        toolbar.addWidget(scale)

    def load_svg(self, path: str):
        # TODO: make quantization a parameters
        vd = vpype.read_multilayer_svg(path, 0.05)
        self.set_vector_data(vd)

    def plot_svg(self):
        vd = vpype.VectorData()
        for lid in self.vector_data.layers:
            if self.plot.layer_visible(lid):
                vd.add(self.vector_data.layers[lid], 1)
        svg = io.StringIO()
        vpype.write_svg(svg, vd, page_format=self.plot.page_format)
        axy.plot_svg(svg.getvalue())

    def set_vector_data(self, vector_data: vpype.VectorData):
        self.base_vector_data = vector_data

        self.update_view()
        model = QStandardItemModel()
        for lid in vector_data.layers:
            item = QStandardItem()
            item.setCheckable(True)
            item.setCheckState(Qt.Checked if self.plot.layer_visible(lid) else Qt.Unchecked)
            pixmap = QPixmap(16, 12)
            pixmap.fill(QColor(*[c * 255 for c in self.plot.layer_color(lid)]))
            item.setIcon(QIcon(pixmap))
            item.setText(f"Layer {lid}")
            item.setSelectable(False)
            item.setEditable(False)
            item.setData(lid, Qt.UserRole + 1)
            model.appendRow(item)

        model.itemChanged.connect(
            lambda it: self.plot.set_layer_visible(
                it.data(Qt.UserRole + 1), it.checkState() == Qt.Checked
            )
        )
        self.list.setModel(model)

    def set_page_format(self, page_format: str):
        self.page_format = page_format
        self.settings.setValue("page_format", page_format)
        self.update_view()

    def set_landscape(self, landscape: bool):
        self.landscape = landscape
        self.settings.setValue("landscape", landscape)
        self.update_view()

    def set_rotated(self, rotated: bool):
        self.rotated = rotated
        self.settings.setValue("rotated", rotated)
        self.update_view()

    def set_center(self, center: bool):
        self.center = center
        self.settings.setValue("center", center)
        self.update_view()

    def set_fit_page(self, fit_page: bool):
        self.fit_page = fit_page
        self.settings.setValue("fit_page", fit_page)
        self.update_view()

    def set_margin(self, value: float, unit: str):
        self.margin_value = value
        self.margin_unit = unit
        self.settings.setValue("margin_value", value)
        self.settings.setValue("margin_unit", unit)
        if self.fit_page:
            self.update_view()

    def update_view(self):
        self.vector_data = copy.deepcopy(self.base_vector_data)

        # scale/center according to settings
        width, height = PAGE_FORMATS[str(self.page_format)]
        if self.landscape:
            width, height = height, width
        if self.rotated:
            self.vector_data.rotate(-math.pi / 2)
            self.vector_data.translate(0, height)

        bounds = self.vector_data.bounds()
        if bounds is not None:
            min_x, min_y, max_x, max_y = bounds
            margin = self.margin_value * vpype.convert(self.margin_unit)
            if self.fit_page:
                factor_x = (width - 2 * margin) / (max_x - min_x)
                factor_y = (height - 2 * margin) / (max_y - min_y)
                scale = min(factor_x, factor_y)

                self.vector_data.translate(-min_x, -min_y)
                self.vector_data.scale(scale)
                if factor_x < factor_y:
                    self.vector_data.translate(
                        margin, margin + (height - 2 * margin - (max_y - min_y) * scale) / 2
                    )
                else:
                    self.vector_data.translate(
                        margin + (width - 2 * margin - (max_x - min_x) * scale) / 2, margin
                    )
            elif self.center:
                self.vector_data.translate(
                    (width - (max_x - min_x)) / 2 - min_x,
                    (height - (max_y - min_y)) / 2 - min_y,
                )

        # configure plot widget
        self.plot.vector_data = self.vector_data
        self.plot.page_format = (width, height)


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("AxiGUI")
        self._config_dialog = ConfigDialog()
        self._plot_control = PlotControlWidget()

        # setup toolbar
        self._toolbar = QToolBar()
        self._toolbar.setIconSize(QSize(64, 64))
        load_act = self._toolbar.addAction(QIcon("images/icons_open.png"), "Load")
        load_act.triggered.connect(lambda: self.load_svg())
        config_act = self._toolbar.addAction(QIcon("images/icons_settings.png"), "Config")
        config_act.triggered.connect(lambda: self._config_dialog.exec_())
        self._toolbar.addSeparator()
        self._plot_control.add_actions(self._toolbar)
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self._toolbar.addWidget(empty)
        quit_act = self._toolbar.addAction(QIcon("images/icons_exit.png"), "Quit")
        quit_act.triggered.connect(lambda: QCoreApplication.quit())

        # setup layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._plot_control)
        self.setLayout(layout)

    def load_svg(self):
        # TODO: remember last folder opened in the session
        path = QFileDialog.getOpenFileName(
            self, "Choose SVG file:", "/Users/hhip/Drive/axidraw", "SVG (*.svg)"
        )
        if path[0]:
            self._plot_control.load_svg(path[0])


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
    min-width: 75px;
}

QDoubleSpinBox {
    padding-right: 1px; /* make room for the arrows */
    padding-left: 1px; /* make room for the arrows */
    min-width: 100px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top left; /* position at the top right corner */

    width: 32px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
    height: 24px
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
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
    # TODO: make that an option
    # main_window.show()
    main_window.showFullScreen()
    sys.exit(app.exec_())
