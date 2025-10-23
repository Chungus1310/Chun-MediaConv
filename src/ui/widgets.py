from PySide6.QtWidgets import QFrame, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, Property
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient

class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(66, 71, 64, 0.7),
                    stop:1 rgba(66, 71, 64, 0.5));
                border: 2px solid rgba(142, 162, 98, 0.3);
                border-radius: 12px;
            }
        """)
        
class AnimatedButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._glow_intensity = 0
        
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8ea262, stop:1 #f5ad5b);
                color: #424740;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
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
        """)
        
    def get_glow(self):
        return self._glow_intensity
        
    def set_glow(self, value):
        self._glow_intensity = value
        self.update()
        
    glow = Property(int, get_glow, set_glow)
    
    def enterEvent(self, event):
        self.animation = QPropertyAnimation(self, b"glow")
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animation = QPropertyAnimation(self, b"glow")
        self.animation.setDuration(200)
        self.animation.setStartValue(100)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        super().leaveEvent(event)

class PresetCard(QFrame):
    clicked = Signal()
    
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        
        self.setFixedHeight(90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(66, 71, 64, 0.6),
                    stop:1 rgba(66, 71, 64, 0.4));
                border: 2px solid rgba(142, 162, 98, 0.4);
                border-radius: 10px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(142, 162, 98, 0.5),
                    stop:1 rgba(142, 162, 98, 0.3));
                border: 2px solid rgba(245, 173, 91, 0.6);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f5ad5b;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11px; color: #dfcca9;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        current = self.geometry()
        target = QRect(current.x() - 2, current.y() - 2, current.width() + 4, current.height() + 4)
        self.animation.setStartValue(current)
        self.animation.setEndValue(target)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        current = self.geometry()
        target = QRect(current.x() + 2, current.y() + 2, current.width() - 4, current.height() - 4)
        self.animation.setStartValue(current)
        self.animation.setEndValue(target)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        super().leaveEvent(event)

class GradientBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(147, 147, 147, 255))
        gradient.setColorAt(0.25, QColor(223, 204, 169, 255))
        gradient.setColorAt(0.5, QColor(142, 162, 98, 255))
        gradient.setColorAt(0.75, QColor(245, 173, 91, 255))
        gradient.setColorAt(1, QColor(66, 71, 64, 255))
        
        painter.fillRect(self.rect(), gradient)
