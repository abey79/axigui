# noinspection PyUnresolvedReferences
import matplotlib.backends.backend_qt5agg  # prevent a bug if loaded after PySide2 on RPi

from .main import main

main()


