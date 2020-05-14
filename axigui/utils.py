import vpype
from PySide2.QtWidgets import QComboBox, QDoubleSpinBox


class UnitComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        for unit in ["px", "cm", "mm", "in", "pc"]:
            self.addItem(unit, vpype.convert(unit))
