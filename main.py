import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.core.config_manager import ConfigManager
from src.utils.logger import setup_logger
from src.utils.paths import resource_path

QCoreApplication.setOrganizationName("Chun")
QCoreApplication.setOrganizationDomain("github.com/Chungus1310")
QCoreApplication.setApplicationName("Chun MediaConv")
QCoreApplication.setApplicationVersion("1.0.0")

def main():
    setup_logger()
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = resource_path("icons", "icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    config = ConfigManager()
    config.initialize()
    
    # Pass initialized config manager into the UI to avoid uninitialized state
    window = MainWindow(config)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
