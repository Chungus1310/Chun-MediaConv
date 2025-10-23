class StyleSheet:
    @staticmethod
    def get_main_stylesheet() -> str:
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #424740, stop:0.5 #3a3d36, stop:1 #2e312c);
            }
            
            QWidget {
                color: #dfcca9;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            
            QLabel {
                color: #dfcca9;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8ea262, stop:1 #f5ad5b);
                color: #424740;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9fb574, stop:1 #ffbd6d);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7d9150, stop:1 #e39c49);
            }
            
            QPushButton:disabled {
                background: rgba(147, 147, 147, 0.3);
                color: rgba(223, 204, 169, 0.5);
            }
            
            QComboBox {
                background: rgba(66, 71, 64, 0.6);
                border: 2px solid rgba(142, 162, 98, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                color: #dfcca9;
                min-height: 25px;
            }
            
            QComboBox:hover {
                border: 2px solid rgba(245, 173, 91, 0.7);
                background: rgba(66, 71, 64, 0.8);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #f5ad5b;
                margin-right: 8px;
            }
            
            QComboBox QAbstractItemView {
                background: #424740;
                border: 2px solid #8ea262;
                selection-background-color: rgba(245, 173, 91, 0.4);
                selection-color: #dfcca9;
                color: #dfcca9;
                padding: 4px;
            }
            
            QComboBox QAbstractItemView::item {
                min-height: 30px;
                padding: 4px 8px;
                color: #dfcca9;
                background: transparent;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background: rgba(142, 162, 98, 0.3);
                color: #dfcca9;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background: rgba(245, 173, 91, 0.4);
                color: #dfcca9;
            }
            
            QSpinBox, QDoubleSpinBox {
                background: rgba(66, 71, 64, 0.6);
                border: 2px solid rgba(142, 162, 98, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                color: #dfcca9;
                min-height: 25px;
            }
            
            QSpinBox:hover, QDoubleSpinBox:hover {
                border: 2px solid rgba(245, 173, 91, 0.7);
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background: rgba(142, 162, 98, 0.3);
                border: none;
                width: 20px;
            }
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background: rgba(245, 173, 91, 0.5);
            }
            
            QLineEdit {
                background: rgba(66, 71, 64, 0.6);
                border: 2px solid rgba(142, 162, 98, 0.5);
                border-radius: 6px;
                padding: 8px 12px;
                color: #dfcca9;
                selection-background-color: rgba(245, 173, 91, 0.5);
            }
            
            QLineEdit:focus {
                border: 2px solid rgba(245, 173, 91, 0.7);
                background: rgba(66, 71, 64, 0.8);
            }
            
            QTextEdit {
                background: rgba(66, 71, 64, 0.4);
                border: 2px solid rgba(142, 162, 98, 0.3);
                border-radius: 8px;
                padding: 10px;
                color: #dfcca9;
                selection-background-color: rgba(245, 173, 91, 0.5);
            }
            
            QCheckBox {
                color: #dfcca9;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid rgba(142, 162, 98, 0.5);
                border-radius: 4px;
                background: rgba(66, 71, 64, 0.6);
            }
            
            QCheckBox::indicator:hover {
                border: 2px solid rgba(245, 173, 91, 0.7);
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8ea262, stop:1 #f5ad5b);
                border: 2px solid #8ea262;
            }
            
            QRadioButton {
                color: #dfcca9;
                spacing: 8px;
            }
            
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid rgba(142, 162, 98, 0.5);
                border-radius: 10px;
                background: rgba(66, 71, 64, 0.6);
            }
            
            QRadioButton::indicator:hover {
                border: 2px solid rgba(245, 173, 91, 0.7);
            }
            
            QRadioButton::indicator:checked {
                background: qradial-gradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.5, stop:0 #f5ad5b, stop:0.5 #8ea262, stop:1 rgba(66, 71, 64, 0.6));
                border: 2px solid #8ea262;
            }
            
            QScrollBar:vertical {
                background: rgba(66, 71, 64, 0.3);
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(142, 162, 98, 0.5);
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(245, 173, 91, 0.6);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background: rgba(66, 71, 64, 0.3);
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(142, 162, 98, 0.5);
                border-radius: 6px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: rgba(245, 173, 91, 0.6);
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            QScrollArea {
                border: none;
                background: transparent;
            }
            
            QSplitter::handle {
                background: rgba(142, 162, 98, 0.3);
            }
            
            QSplitter::handle:hover {
                background: rgba(245, 173, 91, 0.5);
            }
            
            QMessageBox {
                background: #424740;
            }
            
            QMessageBox QLabel {
                color: #dfcca9;
            }
            
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """
