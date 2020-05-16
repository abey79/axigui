from dataclasses import dataclass

from PySide2.QtCore import QSettings
from PySide2.QtWidgets import (
    QFormLayout,
    QComboBox,
    QSpinBox,
    QDialog,
    QDialogButtonBox,
)

from .axy import axy


@dataclass
class SettingsMixin:
    settings: QSettings
    key: str


class AxySettingsSpinBox(SettingsMixin, QSpinBox):
    # noinspection PyTypeChecker
    def __init__(self, settings, key, default, parent=None):
        super().__init__(settings, key)
        QSpinBox.__init__(self, parent=parent)

        self.valueChanged.connect(lambda value: self._update_value(value))
        self.setValue(self.settings.value(key, default))

    def _update_value(self, value: int):
        self.settings.setValue(self.key, value)
        axy.set_option(self.key, value)


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        options = {
            #"pen_pos_down": ("Pen position down:", (0, 100), 40),
            #"pen_pos_up": ("Pen position up:", (0, 100), 60),
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

        for key, (label, (min_val, max_val), default) in options.items():
            spin_box = AxySettingsSpinBox(settings, key, default)
            spin_box.setRange(min_val, max_val)
            spin_box.setSingleStep(1)
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
        model.currentIndexChanged.connect(lambda index: settings.setValue("model", index))
        layout.addRow("Model:", model)

        btn_box = QDialogButtonBox()
        btn_box.setStandardButtons(QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

        self.setLayout(layout)
