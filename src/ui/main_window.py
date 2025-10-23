from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                               QLineEdit, QTextEdit, QProgressBar, QFileDialog, QScrollArea,
                               QFrame, QSplitter, QGroupBox, QRadioButton, QButtonGroup,
                               QCheckBox, QListWidget, QListWidgetItem, QMessageBox,
                               QSizePolicy, QGridLayout)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QFont, QPalette, QColor, QLinearGradient, QPainter, QBrush, QPen
from PySide6.QtSvgWidgets import QSvgWidget

import copy
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.core.config_manager import ConfigManager
from src.core.conversion_engine import ConversionEngine, ConversionWorker
from src.core.format_compatibility import FormatCompatibility
from src.ui.styles import StyleSheet
from src.ui.widgets import GlassFrame, AnimatedButton, PresetCard
from src.ui.advanced_settings import AdvancedSettingsDialog
from src.utils.logger import get_logger
from src.utils.paths import resource_path

logger = get_logger()

class MainWindow(QMainWindow):
    def __init__(self, config_manager: ConfigManager | None = None):
        super().__init__()
        
        # Use the provided, initialized ConfigManager when available
        self.config_manager = config_manager if config_manager is not None else ConfigManager()
        if self.config_manager.config is None:
            # Ensure configuration and presets are initialized when constructed standalone
            self.config_manager.initialize()
        
        self.conversion_engine = ConversionEngine(self.config_manager)
        self.format_compat = FormatCompatibility()
        
        self.active_conversions = {}
        self.conversion_queue = []
        self.progress_values = {}
        self.advanced_values = {}
        self.current_preset_id: Optional[str] = None
        self.preset_overrides: dict[str, Any] = {}
        
        self.setWindowTitle("Chun MediaConv - Professional Media Converter")
        self.setMinimumSize(1200, 800)
        
        self.setup_ui()
        self.apply_styles()
        self.initialize_hardware()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header = self.create_header()
        main_layout.addWidget(header)
        
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setStretchFactor(0, 2)
        content_splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(content_splitter)
        
        footer = self.create_footer()
        main_layout.addWidget(footer)
        
    def create_header(self) -> QWidget:
        header = GlassFrame()
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Brand SVG logo
        svg_logo = QSvgWidget(str(resource_path("icons", "chun_logo.svg")))
        svg_logo.setFixedSize(48, 48)
        layout.addWidget(svg_logo)
        
        title_layout = QVBoxLayout()
        title = QLabel("Chun MediaConv")
        title.setObjectName("headerTitle")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f5ad5b;")
        
        subtitle = QLabel("Professional Media Converter")
        subtitle.setStyleSheet("font-size: 12px; color: #dfcca9;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        self.hw_status_label = QLabel("⚙️ Detecting hardware...")
        self.hw_status_label.setStyleSheet("color: #8ea262; font-size: 11px;")
        layout.addWidget(self.hw_status_label)
        
        return header
        
    def create_left_panel(self) -> QWidget:
        panel = GlassFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        preset_label = QLabel("Quick Presets")
        preset_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f5ad5b; margin-bottom: 10px;")
        layout.addWidget(preset_label)
        
        preset_scroll = QScrollArea()
        preset_scroll.setWidgetResizable(True)
        preset_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        preset_container = QWidget()
        preset_layout = QVBoxLayout(preset_container)
        preset_layout.setSpacing(10)
        
        presets = self.config_manager.presets
        for preset_id, preset_data in presets.items():
            card = PresetCard(preset_data["name"], preset_data["description"])
            card.clicked.connect(lambda pid=preset_id: self.load_preset(pid))
            preset_layout.addWidget(card)
            
        preset_layout.addStretch()
        preset_scroll.setWidget(preset_container)
        layout.addWidget(preset_scroll)
        
        adv_settings_btn = AnimatedButton("⚙️ Advanced Settings")
        adv_settings_btn.clicked.connect(self.show_advanced_settings)
        layout.addWidget(adv_settings_btn)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        file_section = self.create_file_section()
        layout.addWidget(file_section)
        
        settings_section = self.create_settings_section()
        layout.addWidget(settings_section)
        
        queue_section = self.create_queue_section()
        layout.addWidget(queue_section, 1)
        
        control_section = self.create_control_section()
        layout.addWidget(control_section)
        
        return panel
        
    def create_file_section(self) -> QWidget:
        section = GlassFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        label = QLabel("📁 Input Files")
        label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f5ad5b;")
        layout.addWidget(label)
        
        btn_layout = QHBoxLayout()
        
        self.add_files_btn = AnimatedButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_files_btn)
        
        self.add_folder_btn = AnimatedButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.add_folder_btn)
        
        layout.addLayout(btn_layout)
        
        return section
        
    def create_settings_section(self) -> QWidget:
        section = GlassFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        
        label = QLabel("⚙️ Conversion Settings")
        label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f5ad5b; margin-bottom: 10px;")
        layout.addWidget(label)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll_area, 1)

        scroll_widget = QWidget()
        grid_layout = QGridLayout(scroll_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(10)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 2)

        scroll_area.setWidget(scroll_widget)

        control_min_height = 32

        def configure_control(widget):
            widget.setMinimumHeight(control_min_height)
            widget.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))

        def add_label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return lbl

        row = 0
        self.format_combo = QComboBox()
        configure_control(self.format_combo)
        self.format_combo.blockSignals(True)
        self.format_combo.addItems(self.format_compat.get_all_formats())
        self.format_combo.blockSignals(False)
        grid_layout.addWidget(add_label("Output Format:"), row, 0)
        grid_layout.addWidget(self.format_combo, row, 1)

        row += 1
        self.mode_combo = QComboBox()
        configure_control(self.mode_combo)
        self.mode_combo.blockSignals(True)
        self.mode_combo.addItems(["CRF", "CQ", "Bitrate", "Target Size", "Lossless"])
        self.mode_combo.blockSignals(False)
        grid_layout.addWidget(add_label("Mode:"), row, 0)
        grid_layout.addWidget(self.mode_combo, row, 1)

        row += 1
        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.setValue(23)
        configure_control(self.crf_spin)
        self.crf_label = add_label("Quality (CRF):")
        self.crf_row_widget = QWidget()
        crf_layout = QHBoxLayout(self.crf_row_widget)
        crf_layout.setContentsMargins(0, 0, 0, 0)
        crf_layout.addWidget(self.crf_spin)
        grid_layout.addWidget(self.crf_label, row, 0)
        grid_layout.addWidget(self.crf_row_widget, row, 1)

        row += 1
        self.cq_spin = QSpinBox()
        self.cq_spin.setRange(0, 51)
        self.cq_spin.setValue(20)
        configure_control(self.cq_spin)
        self.cq_label = add_label("Quality (CQ):")
        self.cq_row_widget = QWidget()
        cq_layout = QHBoxLayout(self.cq_row_widget)
        cq_layout.setContentsMargins(0, 0, 0, 0)
        cq_layout.addWidget(self.cq_spin)
        grid_layout.addWidget(self.cq_label, row, 0)
        grid_layout.addWidget(self.cq_row_widget, row, 1)
        self.cq_label.setVisible(False)
        self.cq_row_widget.setVisible(False)

        row += 1
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(300, 50000)
        self.bitrate_spin.setValue(5000)
        configure_control(self.bitrate_spin)
        self.bitrate_label = add_label("Video Bitrate (kbps):")
        self.bitrate_row_widget = QWidget()
        bitrate_layout = QHBoxLayout(self.bitrate_row_widget)
        bitrate_layout.setContentsMargins(0, 0, 0, 0)
        bitrate_layout.addWidget(self.bitrate_spin)
        grid_layout.addWidget(self.bitrate_label, row, 0)
        grid_layout.addWidget(self.bitrate_row_widget, row, 1)
        self.bitrate_label.setVisible(False)
        self.bitrate_row_widget.setVisible(False)

        row += 1
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(5, 50000)
        self.size_spin.setDecimals(1)
        self.size_spin.setValue(50.0)
        configure_control(self.size_spin)
        self.size_label = add_label("Target Size (MB):")
        self.size_row_widget = QWidget()
        size_layout = QHBoxLayout(self.size_row_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.addWidget(self.size_spin)
        grid_layout.addWidget(self.size_label, row, 0)
        grid_layout.addWidget(self.size_row_widget, row, 1)
        self.size_label.setVisible(False)
        self.size_row_widget.setVisible(False)

        row += 1
        self.video_codec_combo = QComboBox()
        configure_control(self.video_codec_combo)
        self.video_codec_combo.currentTextChanged.connect(self.on_video_codec_changed)
        grid_layout.addWidget(add_label("Video Codec:"), row, 0)
        grid_layout.addWidget(self.video_codec_combo, row, 1)

        row += 1
        self.video_preset_combo = QComboBox()
        self.video_preset_combo.addItems([
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow"
        ])
        configure_control(self.video_preset_combo)
        self.video_preset_label = add_label("Encoder Preset:")
        grid_layout.addWidget(self.video_preset_label, row, 0)
        grid_layout.addWidget(self.video_preset_combo, row, 1)

        row += 1
        self.video_profile_combo = QComboBox()
        self.video_profile_combo.addItems(["", "baseline", "main", "high", "high10"])
        configure_control(self.video_profile_combo)
        self.video_profile_label = add_label("Profile:")
        grid_layout.addWidget(self.video_profile_label, row, 0)
        grid_layout.addWidget(self.video_profile_combo, row, 1)

        row += 1
        self.video_tune_combo = QComboBox()
        self.video_tune_combo.addItems(["", "film", "animation", "grain", "fastdecode", "zerolatency"])
        configure_control(self.video_tune_combo)
        self.video_tune_label = add_label("Tune:")
        grid_layout.addWidget(self.video_tune_label, row, 0)
        grid_layout.addWidget(self.video_tune_combo, row, 1)

        row += 1
        self.bframes_spin = QSpinBox()
        self.bframes_spin.setRange(0, 16)
        self.bframes_spin.setValue(2)
        configure_control(self.bframes_spin)
        self.bframes_label = add_label("B-Frames:")
        grid_layout.addWidget(self.bframes_label, row, 0)
        grid_layout.addWidget(self.bframes_spin, row, 1)

        row += 1
        self.gop_mode_combo = QComboBox()
        configure_control(self.gop_mode_combo)
        gop_options = [
            ("Half frame rate", "half_fps"),
            ("Same frame rate", "same_fps"),
            ("Double frame rate", "double_fps"),
            ("Custom (frames)", "custom"),
        ]
        for text, value in gop_options:
            self.gop_mode_combo.addItem(text, value)
        self.gop_mode_combo.currentIndexChanged.connect(self.on_gop_mode_changed)
        self.gop_mode_label = add_label("GOP Strategy:")
        grid_layout.addWidget(self.gop_mode_label, row, 0)
        grid_layout.addWidget(self.gop_mode_combo, row, 1)

        row += 1
        self.gop_spin = QSpinBox()
        self.gop_spin.setRange(1, 600)
        self.gop_spin.setValue(60)
        configure_control(self.gop_spin)
        self.gop_label = add_label("Keyframe Interval:")
        grid_layout.addWidget(self.gop_label, row, 0)
        grid_layout.addWidget(self.gop_spin, row, 1)

        row += 1
        self.audio_codec_combo = QComboBox()
        configure_control(self.audio_codec_combo)
        grid_layout.addWidget(add_label("Audio Codec:"), row, 0)
        grid_layout.addWidget(self.audio_codec_combo, row, 1)

        row += 1
        self.hw_accel_check = QCheckBox()
        self.hw_accel_check.setChecked(True)
        configure_control(self.hw_accel_check)
        self.hw_accel_check.setToolTip("Enable GPU acceleration when supported by the system.")
        grid_layout.addWidget(add_label("Hardware Acceleration:"), row, 0)
        grid_layout.addWidget(self.hw_accel_check, row, 1, alignment=Qt.AlignmentFlag.AlignLeft)

        row += 1
        output_container = QWidget()
        output_layout = QHBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(10)
        self.output_path_edit = QLineEdit(self.config_manager.config.output_directory)
        configure_control(self.output_path_edit)
        output_layout.addWidget(self.output_path_edit)
        browse_btn = QPushButton("Browse")
        configure_control(browse_btn)
        browse_btn.clicked.connect(self.browse_output_directory)
        output_layout.addWidget(browse_btn)
        grid_layout.addWidget(add_label("Output Directory:"), row, 0)
        grid_layout.addWidget(output_container, row, 1)
        
        # Connect signals after all dependent widgets are initialized
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)

        # Ensure mode-dependent controls start in the correct state
        self.on_format_changed(self.format_combo.currentText())

        return section
        
    def create_queue_section(self) -> QWidget:
        section = GlassFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header_layout = QHBoxLayout()
        label = QLabel("📋 Conversion Queue")
        label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f5ad5b;")
        header_layout.addWidget(label)
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_queue)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet("""
            QListWidget {
                background: rgba(66, 71, 64, 0.3);
                border: 1px solid rgba(142, 162, 98, 0.3);
                border-radius: 8px;
                color: #dfcca9;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(142, 162, 98, 0.2);
            }
            QListWidget::item:selected {
                background: rgba(245, 173, 91, 0.3);
            }
        """)
        layout.addWidget(self.queue_list)
        
        return section
        
    def create_control_section(self) -> QWidget:
        section = GlassFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid rgba(142, 162, 98, 0.5);
                border-radius: 8px;
                text-align: center;
                background: rgba(66, 71, 64, 0.3);
                color: #dfcca9;
                height: 30px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8ea262, stop:1 #f5ad5b);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        btn_layout = QHBoxLayout()
        
        self.start_btn = AnimatedButton("▶️ Start Conversion")
        self.start_btn.clicked.connect(self.start_conversion)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = AnimatedButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_conversion)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        
        return section
        
    def create_footer(self) -> QWidget:
        footer = GlassFrame()
        footer.setFixedHeight(40)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 5, 20, 5)
        
        author_label = QLabel("Built by Chun")
        author_label.setStyleSheet("color: #8ea262; font-size: 11px;")
        layout.addWidget(author_label)
        
        layout.addStretch()
        
        github_label = QLabel('<a href="https://github.com/Chungus1310" style="color: #f5ad5b; text-decoration: none;">GitHub: Chungus1310</a>')
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)
        
        return footer
        
    def apply_styles(self):
        self.setStyleSheet(StyleSheet.get_main_stylesheet())
        
    def initialize_hardware(self):
        QTimer.singleShot(100, self._detect_hardware)
        
    def _detect_hardware(self):
        success = self.conversion_engine.initialize_hardware()
        
        if success:
            hw_info = self.conversion_engine.get_hardware_info()
            gpu = hw_info.get("gpu", "None")
            accel = hw_info.get("acceleration", "none")
            
            if accel != "none":
                self.hw_status_label.setText(f"✅ GPU: {gpu} ({accel.upper()})")
                self.hw_status_label.setStyleSheet("color: #8ea262; font-size: 11px;")
            else:
                self.hw_status_label.setText(f"⚠️ CPU Only - {gpu}")
                self.hw_status_label.setStyleSheet("color: #f5ad5b; font-size: 11px;")
        else:
            self.hw_status_label.setText("❌ Hardware detection failed")
            self.hw_status_label.setStyleSheet("color: #939393; font-size: 11px;")
            
        self.update_codec_options()
        
    def update_codec_options(self):
        current_format = self.format_combo.currentText()
        
        video_codecs = self.format_compat.get_compatible_video_codecs(current_format)
        audio_codecs = self.format_compat.get_compatible_audio_codecs(current_format)
        
        self.video_codec_combo.clear()
        if video_codecs:
            self.video_codec_combo.addItems(video_codecs)
            self.video_codec_combo.setCurrentIndex(0)
        self.video_codec_combo.setEnabled(bool(video_codecs))
        self.on_video_codec_changed(self.video_codec_combo.currentText() if video_codecs else "")
            
        self.audio_codec_combo.clear()
        if audio_codecs:
            self.audio_codec_combo.addItems(audio_codecs)
        self.audio_codec_combo.setEnabled(bool(audio_codecs))
            
    def on_format_changed(self, format_name: str):
        self.update_codec_options()
        # If audio-only format chosen, disable video controls
        fmt = self.format_compat.get_format_info(format_name)
        is_audio = bool(fmt and fmt.type == "audio")
        self.mode_combo.setEnabled(not is_audio)
        self.crf_spin.setEnabled(not is_audio)
        self.bitrate_spin.setEnabled(not is_audio)
        self.size_spin.setEnabled(not is_audio)
        self.video_codec_combo.setEnabled(not is_audio)
        self.video_preset_combo.setEnabled(not is_audio)
        self.video_profile_combo.setEnabled(not is_audio)
        self.video_tune_combo.setEnabled(not is_audio)
        self.bframes_spin.setEnabled(not is_audio)
        self.gop_mode_combo.setEnabled(not is_audio)
        self.gop_spin.setEnabled(not is_audio and self.gop_mode_combo.currentData() == "custom")
        self.cq_spin.setEnabled(not is_audio)
        self.video_preset_label.setEnabled(not is_audio)
        self.video_profile_label.setEnabled(not is_audio)
        self.video_tune_label.setEnabled(not is_audio)
        self.bframes_label.setEnabled(not is_audio)
        self.gop_mode_label.setEnabled(not is_audio)
        self.gop_label.setEnabled(not is_audio)
        self.cq_label.setEnabled(not is_audio)
        self.on_gop_mode_changed()
        self.on_mode_changed(self.mode_combo.currentText())
        
    def _normalize_video_codec(self, codec: str) -> str:
        mapping = {
            "libx264": "h264",
            "libx265": "h265",
            "libvpx-vp9": "vp9",
            "libaom-av1": "av1",
            "libxvid": "mpeg4",
        }
        codec_lower = (codec or "h264").lower()
        if codec_lower in mapping:
            return mapping[codec_lower]
        if codec_lower.startswith("lib"):
            trimmed = codec_lower[3:]
            if trimmed.startswith("x"):
                trimmed = trimmed[1:]
            return trimmed
        return codec_lower

    def _normalize_audio_codec(self, codec: str) -> str:
        mapping = {
            "libmp3lame": "mp3",
            "libopus": "opus",
            "libvorbis": "vorbis",
        }
        codec_lower = (codec or "aac").lower()
        return mapping.get(codec_lower, codec_lower)

    def _set_combo_items(self, combo: QComboBox, items: List[str], default_value: str = "") -> None:
        current_text = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        idx = combo.findText(current_text, Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        elif items:
            fallback = default_value if default_value and combo.findText(default_value, Qt.MatchFlag.MatchFixedString) >= 0 else items[0]
            fallback_idx = combo.findText(fallback, Qt.MatchFlag.MatchFixedString)
            combo.setCurrentIndex(fallback_idx if fallback_idx >= 0 else 0)
        combo.blockSignals(False)

    def on_video_codec_changed(self, codec: str):
        codec_lower = (codec or "").lower()

        crf_ranges = {
            "h264": (16, 24, 22),
            "h265": (24, 30, 27),
            "vp9": (28, 36, 30),
            "vp8": (28, 36, 32)
        }
        min_crf, max_crf, default_crf = crf_ranges.get(codec_lower, (0, 51, max(self.crf_spin.value(), 23)))
        self.crf_spin.setRange(min_crf, max_crf)
        if not (min_crf <= self.crf_spin.value() <= max_crf):
            self.crf_spin.setValue(default_crf)

        preset_options = {
            "vp9": ["realtime", "good", "best"],
            "vp8": ["realtime", "good", "best"],
            "ffv1": [""],
            "prores": [""]
        }
        default_presets = [
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow"
        ]
        preset_default = "medium" if codec_lower in {"h264", "h265"} else "good" if codec_lower in {"vp9", "vp8"} else ""
        self._set_combo_items(self.video_preset_combo, preset_options.get(codec_lower, default_presets), preset_default)
        self.video_preset_combo.setEnabled(codec_lower not in {"ffv1", "prores"})
        self.video_preset_label.setEnabled(codec_lower not in {"ffv1", "prores"})

        profile_options = {
            "h264": ["", "baseline", "main", "high", "high10"],
            "h265": ["", "main", "main10"]
        }
        if codec_lower in {"ffv1", "prores", "vp9", "vp8"}:
            profile_options.setdefault(codec_lower, [""])
        self._set_combo_items(self.video_profile_combo, profile_options.get(codec_lower, [""]))
        enable_profiles = codec_lower in {"h264", "h265"}
        self.video_profile_combo.setEnabled(enable_profiles)
        self.video_profile_label.setEnabled(enable_profiles)

        tune_options = {
            "h264": ["", "film", "animation", "grain", "fastdecode", "zerolatency"],
            "h265": ["", "grain", "psnr", "ssim", "fastdecode", "zerolatency"]
        }
        self._set_combo_items(self.video_tune_combo, tune_options.get(codec_lower, [""]))
        enable_tune = codec_lower in {"h264", "h265"}
        self.video_tune_combo.setEnabled(enable_tune)
        self.video_tune_label.setEnabled(enable_tune)

        supports_bframes = codec_lower not in {"vp9", "vp8", "ffv1", "prores"}
        self.bframes_spin.setEnabled(supports_bframes)
        self.bframes_label.setEnabled(supports_bframes)
        if not supports_bframes:
            self.bframes_spin.setValue(0)

        long_gop = codec_lower not in {"ffv1", "prores"}
        self.gop_mode_combo.setEnabled(long_gop)
        self.gop_mode_label.setEnabled(long_gop)
        if not long_gop:
            custom_index = self.gop_mode_combo.findData("custom")
            if custom_index >= 0:
                self.gop_mode_combo.setCurrentIndex(custom_index)
            self.gop_spin.setValue(1 if codec_lower in {"ffv1", "prores"} else 12)
        self.on_gop_mode_changed()

        if codec_lower in {"ffv1", "prores"} and self.mode_combo.currentText() != "Lossless":
            self.mode_combo.setCurrentText("Lossless")

    def _extract_preset_overrides(self, preset: Dict[str, Any]) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        passthrough_keys = {
            "video_codec",
            "video_encoder",
            "video_preset",
            "video_profile",
            "video_level",
            "video_tune",
            "encoding_mode",
            "crf",
            "cq",
            "video_bitrate",
            "target_size_mb",
            "pixel_format",
            "b_frames",
            "gop_mode",
            "gop_size",
            "gop_seconds",
            "movflags",
            "color_primaries",
            "color_trc",
            "colorspace",
            "maxrate",
            "bufsize",
            "audio_codec",
            "audio_encoder",
            "audio_bitrate",
            "audio_sample_rate",
            "audio_channels",
            "video_filters",
            "framerate",
            "scale_width",
            "scale_height",
            "use_hardware_acceleration",
            "force_cfr",
            "extra_video_options",
            "extra_audio_options"
        }

        for key in passthrough_keys:
            if key in preset and preset[key] is not None:
                value = preset[key]
                if isinstance(value, (list, dict)):
                    overrides[key] = copy.deepcopy(value)
                else:
                    overrides[key] = value

        return overrides

    def on_gop_mode_changed(self):
        current_mode = self.gop_mode_combo.currentData()
        is_custom = current_mode == "custom"
        self.gop_spin.setEnabled(self.gop_mode_combo.isEnabled() and is_custom)
        self.gop_label.setEnabled(self.gop_mode_combo.isEnabled())

    def load_preset(self, preset_id: str):
        preset = self.config_manager.get_preset(preset_id)
        if not preset:
            return
        
        self.current_preset_id = preset_id
        self.preset_overrides = self._extract_preset_overrides(preset)
        advanced_sync_keys = {"scale_width", "scale_height", "framerate", "pixel_format"}
        if any(key in preset for key in advanced_sync_keys):
            for key in advanced_sync_keys:
                if key in self.advanced_values:
                    self.advanced_values.pop(key, None)
            for key in advanced_sync_keys:
                if key in preset and preset[key] is not None:
                    self.advanced_values[key] = preset[key]
        container = preset.get("container")
        if container:
            idx = self.format_combo.findText(container, Qt.MatchFlag.MatchFixedString)
            if idx >= 0:
                self.format_combo.setCurrentIndex(idx)

        encoding_mode = (preset.get("encoding_mode") or "crf").lower()
        mode_map = {
            "crf": "CRF",
            "cq": "CQ",
            "bitrate": "Bitrate",
            "target_size": "Target Size",
            "lossless": "Lossless"
        }
        self.mode_combo.setCurrentText(mode_map.get(encoding_mode, "CRF"))

        if encoding_mode == "crf":
            self.crf_spin.setValue(preset.get("crf", self.crf_spin.value()))
        elif encoding_mode == "cq":
            self.cq_spin.setValue(preset.get("cq", self.cq_spin.value()))
        elif encoding_mode == "bitrate":
            bitrate_value = preset.get("video_bitrate")
            if isinstance(bitrate_value, str):
                lowered = bitrate_value.lower()
                try:
                    if lowered.endswith("k"):
                        self.bitrate_spin.setValue(int(float(lowered[:-1])))
                    elif lowered.endswith("m"):
                        self.bitrate_spin.setValue(int(float(lowered[:-1]) * 1000))
                except ValueError:
                    pass
        elif encoding_mode == "target_size":
            self.size_spin.setValue(float(preset.get("target_size_mb", self.size_spin.value())))

        normalized_video_codec = self._normalize_video_codec(preset.get("video_codec", "h264"))
        idx = self.video_codec_combo.findText(normalized_video_codec, Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self.video_codec_combo.setCurrentIndex(idx)
        elif self.video_codec_combo.count() > 0:
            self.video_codec_combo.setCurrentIndex(0)

        video_preset = preset.get("video_preset")
        if video_preset:
            vp_idx = self.video_preset_combo.findText(video_preset, Qt.MatchFlag.MatchFixedString)
            if vp_idx < 0:
                self.video_preset_combo.addItem(video_preset)
                vp_idx = self.video_preset_combo.count() - 1
            self.video_preset_combo.setCurrentIndex(vp_idx)

        profile_val = preset.get("video_profile")
        if profile_val is not None:
            profile_str = str(profile_val)
            prof_idx = self.video_profile_combo.findText(profile_str, Qt.MatchFlag.MatchFixedString)
            if prof_idx < 0:
                self.video_profile_combo.addItem(profile_str)
                prof_idx = self.video_profile_combo.count() - 1
            self.video_profile_combo.setCurrentIndex(prof_idx)

        tune_val = preset.get("video_tune")
        if tune_val:
            tune_idx = self.video_tune_combo.findText(tune_val, Qt.MatchFlag.MatchFixedString)
            if tune_idx < 0:
                self.video_tune_combo.addItem(tune_val)
                tune_idx = self.video_tune_combo.count() - 1
            self.video_tune_combo.setCurrentIndex(tune_idx)

        if "b_frames" in preset and preset["b_frames"] is not None:
            self.bframes_spin.setValue(int(preset["b_frames"]))

        gop_mode = preset.get("gop_mode")
        if gop_mode:
            gop_idx = self.gop_mode_combo.findData(gop_mode)
            if gop_idx >= 0:
                self.gop_mode_combo.setCurrentIndex(gop_idx)
        if "gop_size" in preset and preset.get("gop_size") is not None:
            self.gop_spin.setValue(int(preset["gop_size"]))
        self.on_gop_mode_changed()

        if "use_hardware_acceleration" in preset:
            self.hw_accel_check.setChecked(bool(preset["use_hardware_acceleration"]))

        normalized_audio_codec = self._normalize_audio_codec(preset.get("audio_codec", "aac"))
        idx = self.audio_codec_combo.findText(normalized_audio_codec, Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self.audio_codec_combo.setCurrentIndex(idx)
        elif self.audio_codec_combo.count() > 0:
            self.audio_codec_combo.setCurrentIndex(0)

        if self.config_manager.config:
            self.config_manager.config.last_preset = preset_id
            self.config_manager.save_config()

        logger.info(f"Loaded preset: {preset['name']}")

    def on_mode_changed(self, mode_text: str):
        mode = mode_text.lower()
        controls_enabled = self.mode_combo.isEnabled()
        # Toggle rows visibility
        is_crf = mode == "crf"
        is_cq = mode == "cq"
        is_bitrate = mode == "bitrate"
        is_target_size = mode == "target size"
        is_lossless = mode == "lossless"

        self.crf_label.setVisible(is_crf)
        self.crf_row_widget.setVisible(is_crf)
        self.crf_spin.setEnabled(is_crf and controls_enabled)

        self.cq_label.setVisible(is_cq)
        self.cq_row_widget.setVisible(is_cq)
        self.cq_spin.setEnabled(is_cq and controls_enabled)

        self.bitrate_label.setVisible(is_bitrate)
        self.bitrate_row_widget.setVisible(is_bitrate)
        self.bitrate_spin.setEnabled(is_bitrate and controls_enabled)

        self.size_label.setVisible(is_target_size)
        self.size_row_widget.setVisible(is_target_size)
        self.size_spin.setEnabled(is_target_size and controls_enabled)

        if is_lossless:
            # ensure hidden quality controls for clarity
            self.crf_label.setVisible(False)
            self.crf_row_widget.setVisible(False)
            self.cq_label.setVisible(False)
            self.cq_row_widget.setVisible(False)
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files",
            "",
            "Media Files (*.mp4 *.mkv *.avi *.mov *.flv *.webm *.mp3 *.wav *.flac *.ogg *.aac);;All Files (*.*)"
        )
        
        if files:
            for file in files:
                self.conversion_queue.append(file)
                item = QListWidgetItem(Path(file).name)
                item.setData(Qt.ItemDataRole.UserRole, file)
                self.queue_list.addItem(item)
                
            logger.info(f"Added {len(files)} files to queue")
            
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if folder:
            extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', 
                         '.mp3', '.wav', '.flac', '.ogg', '.aac']
            
            folder_path = Path(folder)
            files = []
            for ext in extensions:
                files.extend(folder_path.rglob(f"*{ext}"))
                
            for file in files:
                file_str = str(file)
                self.conversion_queue.append(file_str)
                item = QListWidgetItem(file.name)
                item.setData(Qt.ItemDataRole.UserRole, file_str)
                self.queue_list.addItem(item)
                
            logger.info(f"Added {len(files)} files from folder")
            
    def clear_queue(self):
        self.conversion_queue.clear()
        self.queue_list.clear()
        
    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_path_edit.setText(directory)
            self.config_manager.config.output_directory = directory
            self.config_manager.save_config()
            
    def start_conversion(self):
        if not self.conversion_queue:
            QMessageBox.warning(self, "No Files", "Please add files to the queue first.")
            return
            
        output_dir = self.output_path_edit.text()
        if not output_dir or not Path(output_dir).exists():
            QMessageBox.warning(self, "Invalid Output", "Please select a valid output directory.")
            return
            
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.fill_conversion_slots()
        
    def process_next_in_queue(self):
        if not self.conversion_queue:
            if not self.active_conversions:
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.progress_bar.setValue(0)
                QMessageBox.information(self, "Complete", "All conversions completed!")
            return
        input_file = self.conversion_queue.pop(0)
        self.queue_list.takeItem(0)
        
        output_format = self.format_combo.currentText()
        output_file = Path(self.output_path_edit.text()) / f"{Path(input_file).stem}.{output_format}"
        
        job_config = {
            "input_file": input_file,
            "output_file": str(output_file),
            "video_codec": self.video_codec_combo.currentText(),
            "audio_codec": self.audio_codec_combo.currentText(),
            "crf": self.crf_spin.value(),
            "encoding_mode": self.mode_combo.currentText().lower().replace(" ", "_"),
            "video_bitrate": f"{self.bitrate_spin.value()}k",
            "target_size_mb": float(self.size_spin.value()),
            "video_preset": "medium",
            "use_hardware_acceleration": self.hw_accel_check.isChecked(),
            "threads": 0
        }
        if self.preset_overrides:
            job_config.update(self.preset_overrides)
        # Merge advanced settings into job config
        if self.advanced_values:
            job_config.update(self.advanced_values)
        # Determine conversion type based on selected format
        fmt_info = self.format_compat.get_format_info(output_format)
        if fmt_info and fmt_info.type == "audio":
            job_config["conversion_type"] = "video_to_audio"
        
        worker = self.conversion_engine.create_conversion_job(job_config)
        if not worker:
            QMessageBox.critical(self, "Error", "Failed to create conversion job")
            return
            
        thread = QThread()
        worker.moveToThread(thread)
        
        worker.progress.connect(
            self.on_conversion_progress,
            Qt.ConnectionType.QueuedConnection
        )
        worker.finished.connect(
            self.on_conversion_finished,
            Qt.ConnectionType.QueuedConnection
        )
        worker.error.connect(
            self.on_conversion_error,
            Qt.ConnectionType.QueuedConnection
        )
        
        thread.started.connect(worker.run)
        
        self.active_conversions[input_file] = (thread, worker)
        thread.start()
        
    def fill_conversion_slots(self):
        max_parallel = max(1, int(self.config_manager.config.max_parallel_conversions))
        while self.conversion_queue and len(self.active_conversions) < max_parallel:
            self.process_next_in_queue()
        
    def on_conversion_progress(self, progress: float, message: str):
        # Track average progress across active conversions
        # Sender is a ConversionWorker
        worker = self.sender()
        for key, (_t, w) in self.active_conversions.items():
            if w is worker:
                self.progress_values[key] = progress
                break
        if self.progress_values:
            avg = sum(self.progress_values.values()) / max(1, len(self.progress_values))
            self.progress_bar.setValue(int(avg))
        
    def on_conversion_finished(self, success: bool, message: str):
        worker = self.sender()
        if not isinstance(worker, ConversionWorker):
            worker = None

        thread: QThread | None = None

        if worker is not None:
            for key, (thr, wrk) in list(self.active_conversions.items()):
                if wrk is worker:
                    thread = thr
                    del self.active_conversions[key]
                    self.progress_values.pop(key, None)
                    break

        fallback_worker: ConversionWorker | None = None
        if thread is None and self.active_conversions:
            # Fallback: clean up the most recent entry to avoid orphaned threads
            key, (thr, fallback_worker) = self.active_conversions.popitem()
            thread = thr
            self.progress_values.pop(key, None)

        if thread is not None:
            if thread is not QThread.currentThread():
                thread.quit()
                thread.wait()
            else:
                thread.quit()

        cleanup_worker = worker if isinstance(worker, ConversionWorker) else fallback_worker
        if isinstance(cleanup_worker, ConversionWorker):
            cleanup_worker.deleteLater()
        if thread is not None:
            thread.deleteLater()

        if success:
            logger.info(f"Conversion completed: {message}")
            self.fill_conversion_slots()
        else:
            failure_msg = message or "Conversion failed"
            if failure_msg == "Conversion cancelled":
                logger.info("Conversion cancelled by user")
                return
            logger.error(f"Conversion failed: {failure_msg}")
            display_msg = failure_msg
            if len(display_msg) > 500:
                display_msg = display_msg[:500] + "..."
            QMessageBox.warning(self, "Conversion Failed", f"Failed:\n{display_msg}")
            
    def on_conversion_error(self, error: str):
        logger.error(f"Conversion error: {error}")
        
    def stop_conversion(self):
        for input_file, (thread, worker) in list(self.active_conversions.items()):
            worker.stop()
            if thread is not QThread.currentThread():
                thread.quit()
                thread.wait()
            else:
                thread.quit()
            worker.deleteLater()
            thread.deleteLater()
            
        self.active_conversions.clear()
        self.progress_values.clear()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def show_advanced_settings(self):
        dlg = AdvancedSettingsDialog(self, self.advanced_values)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self.advanced_values = dlg.get_values()
            logger.info("Advanced settings updated")
        
    def closeEvent(self, event):
        self.stop_conversion()
        self.config_manager.cleanup_temp_files()
        event.accept()
