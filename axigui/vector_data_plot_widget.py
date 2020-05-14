from typing import Tuple

import matplotlib
import matplotlib.collections
import numpy as np
import vpype
from PySide2.QtCore import QSettings
from PySide2.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QSizePolicy,
    QSpacerItem,
    QLabel,
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure

from axigui.utils import UnitComboBox

COLORS = [
    (0, 0, 1),
    (0, 0.5, 0),
    (1, 0, 0),
    (0, 0.75, 0.75),
    (0, 1, 0),
    (0.75, 0, 0.75),
    (0.75, 0.75, 0),
    (0, 0, 0),
]

matplotlib.use("Qt5Agg")


class VectorDataPlotWidget(QWidget):
    # noinspection PyTypeChecker
    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = QSettings()
        self.settings.beginGroup("plot_display")

        # initialise canvas/figure/axes according to
        # https://matplotlib.org/examples/user_interfaces/embedding_in_qt5.html
        self.fig = Figure(figsize=(10, 10), facecolor=(1, 1, 1), edgecolor=(0, 0, 0))
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.tick_params(pad=-5)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.toolbar = NavigationToolbar(self.canvas, self)

        # plot params
        self._vector_data = vpype.VectorData()
        self._page_format = (100, 100)  # in pixels
        self._init_lims = True

        # settings
        self._unit: str = self.settings.value("unit", "cm")
        self._colorful: bool = self.settings.value("colorful", False)
        self._show_points: bool = self.settings.value("show_points", False)
        self._show_pen_up: bool = self.settings.value("show_pen_up", False)
        self._show_axes: bool = self.settings.value("show_axes", False)
        self._show_grid: bool = self.settings.value("show_grid", False)
        self._show_legend: bool = self.settings.value("show_legend", True)

        # matplotlib hooks to be removed upon redraw
        self.cids = []

        # control bar
        scale = UnitComboBox()
        scale.setCurrentText(self._unit)
        scale.currentTextChanged.connect(lambda text: setattr(self, "unit", text))
        colorful_check = QCheckBox("Colorful")
        colorful_check.setChecked(self._colorful)
        colorful_check.stateChanged.connect(
            lambda: setattr(self, "colorful", colorful_check.isChecked())
        )
        show_points_check = QCheckBox("Show points")
        show_points_check.setChecked(self._show_points)
        show_points_check.stateChanged.connect(
            lambda: setattr(self, "show_points", show_points_check.isChecked())
        )
        show_pen_up_check = QCheckBox("Show pen-up")
        show_pen_up_check.setChecked(self._show_pen_up)
        show_pen_up_check.stateChanged.connect(
            lambda: setattr(self, "show_pen_up", show_pen_up_check.isChecked())
        )
        show_axes_check = QCheckBox("Show axes")
        show_axes_check.setChecked(self._show_axes)
        show_axes_check.stateChanged.connect(
            lambda: setattr(self, "show_axes", show_axes_check.isChecked())
        )
        show_legend_check = QCheckBox("Show legend")
        show_legend_check.setChecked(self._show_legend)
        show_legend_check.stateChanged.connect(
            lambda: setattr(self, "show_legend", show_legend_check.isChecked())
        )

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("Unit:"))
        ctrl_layout.addWidget(scale)
        ctrl_layout.addWidget(colorful_check)
        ctrl_layout.addWidget(show_points_check)
        ctrl_layout.addWidget(show_pen_up_check)
        ctrl_layout.addWidget(show_axes_check)
        ctrl_layout.addWidget(show_legend_check)
        ctrl_layout.addItem(QSpacerItem(5, 5, QSizePolicy.Expanding, QSizePolicy.Minimum))
        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl_layout)

        # setup layout
        layout = QVBoxLayout()
        layout.addWidget(ctrl_widget)
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

    @property
    def vector_data(self):
        return self._vector_data

    @vector_data.setter
    def vector_data(self, vd):
        self._vector_data = vd
        self._init_lims = True
        self._replot()

    @property
    def page_format(self) -> Tuple[float, float]:
        return self._page_format

    @page_format.setter
    def page_format(self, size: Tuple[float, float]):
        self._page_format = size
        self._init_lims = True
        self._replot()

    @property
    def unit(self) -> str:
        return self._unit

    @unit.setter
    def unit(self, value: str):
        self._unit = value
        self.settings.setValue("unit", value)
        self._init_lims = True
        self._replot()

    @property
    def colorful(self) -> bool:
        return self._colorful

    @colorful.setter
    def colorful(self, value: bool):
        self._colorful = value
        self.settings.setValue("colorful", value)
        self._replot()

    @property
    def show_points(self) -> bool:
        return self._show_points

    @show_points.setter
    def show_points(self, value: bool):
        self._show_points = value
        self.settings.setValue("show_points", value)
        self._replot()

    @property
    def show_pen_up(self) -> bool:
        return self._show_pen_up

    @show_pen_up.setter
    def show_pen_up(self, value):
        self._show_pen_up = value
        self.settings.setValue("show_pen_up", value)
        self._replot()

    @property
    def show_axes(self) -> bool:
        return self._show_axes

    @show_axes.setter
    def show_axes(self, value):
        self._show_axes = value
        self._show_grid = value
        self.settings.setValue("show_axes", value)
        self.settings.setValue("show_grid", value)
        self._replot()

    @property
    def show_legend(self) -> bool:
        return self._show_legend

    @show_legend.setter
    def show_legend(self, value):
        self._show_legend = value
        self.settings.setValue("show_legend", value)
        self._replot()

    def _replot(self):

        for cid in self.cids:
            self.canvas.mpl_disconnect(cid)
        if not self._init_lims:
            old_lims = (self.ax.get_xlim(), self.ax.get_ylim())
        else:
            old_lims = None
            self._init_lims = False
        self.ax.cla()

        scale = 1 / vpype.convert(self._unit)

        # draw page
        w = self._page_format[0] * scale
        h = self._page_format[1] * scale
        dw = 10 * scale
        self.ax.plot(
            np.array([0, 1, 1, 0, 0]) * w, np.array([0, 0, 1, 1, 0]) * h, "-k", lw=0.25,
        )
        self.ax.fill(
            np.array([w, w + dw, w + dw, dw, dw, w]),
            np.array([dw, dw, h + dw, h + dw, h, h]),
            "k",
            alpha=0.3,
        )

        color_idx = 0
        collections = {}
        for layer_id, lc in self._vector_data.layers.items():
            if self._colorful:
                color = COLORS[color_idx:] + COLORS[:color_idx]
                marker_color = "k"
                color_idx += len(lc)
            else:
                color = COLORS[color_idx]
                marker_color = [color]
                color_idx += 1
            if color_idx >= len(COLORS):
                color_idx = color_idx % len(COLORS)

            layer_lines = matplotlib.collections.LineCollection(
                (vpype.as_vector(line) * scale for line in lc),
                color=color,
                lw=1,
                alpha=0.5,
                label=str(layer_id),
            )
            collections[layer_id] = [layer_lines]
            self.ax.add_collection(layer_lines)

            if self._show_points:
                points = np.hstack([line for line in lc]) * scale
                layer_points = self.ax.scatter(
                    points.real, points.imag, marker=".", c=marker_color, s=16
                )
                collections[layer_id].append(layer_points)

            if self._show_pen_up:
                pen_up_lines = matplotlib.collections.LineCollection(
                    (
                        (
                            vpype.as_vector(lc[i])[-1] * scale,
                            vpype.as_vector(lc[i + 1])[0] * scale,
                        )
                        for i in range(len(lc) - 1)
                    ),
                    color=(0, 0, 0),
                    lw=0.5,
                    alpha=0.5,
                )
                collections[layer_id].append(pen_up_lines)
                self.ax.add_collection(pen_up_lines)

        self.ax.invert_yaxis()
        self.ax.axis("equal")

        if self._show_legend:
            lgd = self.ax.legend(loc="upper right")
            # we will set up a dict mapping legend line to orig line, and enable
            # picking on the legend line
            line_dict = {}
            for lgd_line, lgd_text in zip(lgd.get_lines(), lgd.get_texts()):
                lgd_line.set_picker(5)  # 5 pts tolerance
                layer_id = int(lgd_text.get_text())
                if layer_id in collections:
                    line_dict[lgd_line] = collections[layer_id]

            def on_pick(event):
                line = event.artist
                vis = not line_dict[line][0].get_visible()
                for ln in line_dict[line]:
                    ln.set_visible(vis)

                if vis:
                    line.set_alpha(1.0)
                else:
                    line.set_alpha(0.2)
                self.canvas.draw()

            self.cids.append(self.canvas.mpl_connect("pick_event", on_pick))

        if self._show_axes or self._show_grid:
            self.ax.axis("on")
            self.ax.set_xlabel(f"[{self._unit}]")
            self.ax.set_ylabel(f"[{self._unit}]")
        else:
            self.ax.axis("off")
        if self._show_grid:
            self.ax.grid("on", alpha=0.2)

        if old_lims is not None:
            self.ax.set_xlim(old_lims[0])
            self.ax.set_ylim(old_lims[1])
        else:
            self.toolbar.update()

        for text in self.ax.get_xticklabels():
            text.set_horizontalalignment("center")
            text.set_verticalalignment("bottom")

        for text in self.ax.get_yticklabels():
            text.set_horizontalalignment("left")
            text.set_verticalalignment("center")
        self.canvas.draw()
