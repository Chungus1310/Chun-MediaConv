from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton, QWidget
from PySide6.QtCore import Qt


class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None, initial: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.values = initial.copy() if initial else {}

        layout = QVBoxLayout(self)

        # Video section
        vbox = QVBoxLayout()
        hlay = QHBoxLayout()
        hlay.addWidget(QLabel("Scale W:"))
        self.scale_w = QSpinBox(); self.scale_w.setRange(-2, 7680)
        self.scale_w.setValue(self.values.get("scale_width", -2))
        hlay.addWidget(self.scale_w)
        hlay.addWidget(QLabel("H:"))
        self.scale_h = QSpinBox(); self.scale_h.setRange(-2, 4320)
        self.scale_h.setValue(self.values.get("scale_height", -2))
        hlay.addWidget(self.scale_h)
        vbox.addLayout(hlay)

        hlay2 = QHBoxLayout()
        hlay2.addWidget(QLabel("Framerate:"))
        self.fps = QDoubleSpinBox(); self.fps.setRange(0, 240); self.fps.setDecimals(2)
        self.fps.setValue(float(self.values.get("framerate", 0) or 0))
        hlay2.addWidget(self.fps)
        hlay2.addWidget(QLabel("Pixel Format:"))
        self.pix_fmt = QComboBox(); self.pix_fmt.addItems(["", "yuv420p", "yuv422p", "yuv444p", "p010le"]) 
        self.pix_fmt.setCurrentText(self.values.get("pixel_format", ""))
        hlay2.addWidget(self.pix_fmt)
        vbox.addLayout(hlay2)

        self.video_copy = QCheckBox("Copy Video Stream (no re-encode)")
        self.video_copy.setChecked(bool(self.values.get("video_copy", False)))
        vbox.addWidget(self.video_copy)

        layout.addLayout(vbox)

        # Audio section
        abox = QVBoxLayout()
        hlay3 = QHBoxLayout()
        hlay3.addWidget(QLabel("Sample Rate:"))
        self.ar = QSpinBox(); self.ar.setRange(0, 192000)
        self.ar.setValue(int(self.values.get("audio_sample_rate", 0) or 0))
        hlay3.addWidget(self.ar)
        hlay3.addWidget(QLabel("Channels:"))
        self.ac = QSpinBox(); self.ac.setRange(0, 8)
        self.ac.setValue(int(self.values.get("audio_channels", 0) or 0))
        hlay3.addWidget(self.ac)
        abox.addLayout(hlay3)

        self.audio_copy = QCheckBox("Copy Audio Stream (no re-encode)")
        self.audio_copy.setChecked(bool(self.values.get("audio_copy", False)))
        abox.addWidget(self.audio_copy)

        layout.addLayout(abox)

        # Trim section
        tbox = QHBoxLayout()
        tbox.addWidget(QLabel("Start (hh:mm:ss)"))
        # Simple text-based entry to avoid complex time widgets
        from PySide6.QtWidgets import QLineEdit
        self.ss = QLineEdit(self.values.get("start_time", ""))
        tbox.addWidget(self.ss)
        tbox.addWidget(QLabel("Duration (hh:mm:ss)"))
        self.t = QLineEdit(self.values.get("duration", ""))
        tbox.addWidget(self.t)
        layout.addLayout(tbox)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        ok = QPushButton("Apply")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

    def get_values(self) -> dict:
        vals = {
            "scale_width": self.scale_w.value(),
            "scale_height": self.scale_h.value(),
            "framerate": int(self.fps.value()) if self.fps.value() else None,
            "pixel_format": self.pix_fmt.currentText() or None,
            "video_copy": self.video_copy.isChecked(),
            "audio_sample_rate": self.ar.value() or None,
            "audio_channels": self.ac.value() or None,
            "audio_copy": self.audio_copy.isChecked(),
            "start_time": self.ss.text().strip() or None,
            "duration": self.t.text().strip() or None,
        }
        # Clean Nones to avoid noisy job_config
        return {k: v for k, v in vals.items() if v not in (None, "", 0)}
