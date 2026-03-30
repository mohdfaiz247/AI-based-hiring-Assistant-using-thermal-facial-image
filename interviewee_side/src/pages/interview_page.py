"""
AI Hiring Assistant - Interview Recording Page
Video-based interview experience with reaction recording.
Aesthetic: Neo-Corporate Futurism
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from ..camera_handler import CameraHandler


class PulsingDot(QWidget):
    """Animated recording indicator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.opacity = 255
        self.direction = -1
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
    
    def start(self):
        self.timer.start(40)
        self.show()
    
    def stop(self):
        self.timer.stop()
        self.hide()
    
    def _animate(self):
        self.opacity += self.direction * 12
        if self.opacity <= 100:
            self.direction = 1
        elif self.opacity >= 255:
            self.direction = -1
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Outer glow
        painter.setBrush(QColor(255, 71, 87, self.opacity // 3))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 16, 16)
        
        # Inner dot
        painter.setBrush(QColor(255, 71, 87, self.opacity))
        painter.drawEllipse(4, 4, 8, 8)


class VideoPlayerFrame(QFrame):
    """Styled frame for video playback."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()
    
    def _setup_style(self):
        self.setStyleSheet("""
            QFrame {
                background: #000000;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)


class InterviewPage(QWidget):
    """
    Video interview interface.
    Plays a video from 'Data' folder and records user reaction via the camera.
    Recording is started externally by app.py before calling start().
    """

    interview_complete = pyqtSignal()
    back_clicked = pyqtSignal()

    def __init__(self, camera_handler: CameraHandler, parent=None):
        super().__init__(parent)
        self.camera_handler = camera_handler

        self.is_recording = False
        self.video_path = None

        self.setup_ui()
        self._setup_media_player()
    
    def setup_ui(self):
        """Set up the interview page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(0)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step_label = QLabel("STEP 3 OF 5")
        step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_label.setStyleSheet("""
            color: #00d4ff;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 2px;
            background: transparent;
        """)
        header_layout.addWidget(step_label)

        heading = QLabel("video Interview")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        heading.setStyleSheet("color: #f8f9fa; letter-spacing: -1px; background: transparent;")
        header_layout.addWidget(heading)

        self.status_label = QLabel("Please watch the video below")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #6c757d; font-size: 15px; background: transparent;")
        header_layout.addWidget(self.status_label)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(30)

        # Video Player Area
        player_container = QHBoxLayout()
        player_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.video_frame = VideoPlayerFrame()
        video_layout = QVBoxLayout(self.video_frame)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        video_layout.addWidget(self.video_widget)

        player_container.addWidget(self.video_frame)
        main_layout.addLayout(player_container)

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.setSpacing(20)

        # Play button (initially active)
        self.play_button = QPushButton("▶ Play Video")
        self.play_button.setFixedSize(130, 40)
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.setStyleSheet("""
            QPushButton {
                background: rgba(0, 212, 255, 0.15);
                color: #00d4ff;
                border: 1px solid #00d4ff;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.25);
            }
        """)
        self.play_button.clicked.connect(self._toggle_playback)
        controls_layout.addWidget(self.play_button)

        # Shift controls downward
        main_layout.addSpacing(20)
        main_layout.addLayout(controls_layout)
        main_layout.addSpacing(10)

        # Recording indicator and finish button
        bottom_bar = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setSpacing(30)
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Recording status
        rec_layout = QHBoxLayout()
        rec_layout.setSpacing(10)

        self.recording_dot = PulsingDot()
        self.recording_dot.hide()

        self.rec_label = QLabel("RECORDING REACTION")
        self.rec_label.setStyleSheet("color: #ff4757; font-size: 12px; font-weight: bold; letter-spacing: 1px; background: transparent;")
        self.rec_label.hide()

        rec_layout.addWidget(self.recording_dot)
        rec_layout.addWidget(self.rec_label)
        bottom_layout.addLayout(rec_layout)

        # Finish button (hidden initially)
        self.finish_button = QPushButton("Finish Interview →")
        self.finish_button.setFixedSize(170, 42)
        self.finish_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.finish_button.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        self.finish_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #00d4ff, stop:1 #a855f7);
                color: #0a0a0f;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #00e5ff, stop:1 #a855f7);
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 212, 255, 100))
        self.finish_button.setGraphicsEffect(shadow)
        self.finish_button.clicked.connect(self._on_finish)
        self.finish_button.hide()

        bottom_layout.addWidget(self.finish_button)
        main_layout.addWidget(bottom_bar)

        main_layout.addSpacing(20)

    def _update_video_size(self):
        """Keep video area proportionally sized to prevent overlaps."""
        if not hasattr(self, 'video_frame') or not self.video_frame:
            return

        # Reserve space for header, controls, and margins (~350px total)
        available_height = max(180, self.height() - 360)
        available_width = max(320, self.width() - 120)

        # Target 16:9 aspect ratio
        target_height = available_height
        target_width = int(target_height * 16 / 9)

        if target_width > available_width:
            target_width = available_width
            target_height = int(target_width * 9 / 16)

        # Respect maximum limits
        container_width = min(target_width, 1100)
        container_height = min(target_height, 620)

        self.video_frame.setFixedSize(container_width, container_height)
        self.video_widget.setFixedSize(container_width, container_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_video_size()

    def _setup_media_player(self):
        """Initialize media player."""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
    
    def start(self):
        """Initialize and prepare video."""
        # Look for video in Data folder
        # TO (More robust):
        data_dir = Path(__file__).resolve().parents[2] / "Data"
        # Try finding any mp4 file
        video_files = list(data_dir.glob("*.mp4"))
        
        if not video_files:
            QMessageBox.warning(self, "Error", "No video file found in 'Data' folder.\nPlease add an MP4 file.")
            self.status_label.setText("Error: Video file not found")
            self.play_button.setEnabled(False)
            return

        self.video_path = video_files[0]
        self.media_player.setSource(QUrl.fromLocalFile(str(self.video_path.absolute())))
        self.status_label.setText(f"Loaded: {self.video_path.name}")
        self.play_button.setEnabled(True)
    
    def _toggle_playback(self):
        """Toggle play/pause."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶ Resume Video")
            self._pause_recording()
        else:
            self.media_player.play()
            self.play_button.setText("⏸ Pause Video")
            self._start_recording()
            
            # Show finish button once playback starts
            self.finish_button.show()
    
    def _start_recording(self):
        """Indicate visually that recording is active (actual recording already started by app.py)."""
        if self.is_recording:
            return
        self.is_recording = True
        self.recording_dot.start()
        self.rec_label.show()
    
    def _pause_recording(self):
        """Ideally pause recording, but for now we keep recording to simplify."""
        # For simplicity in this version, we can keep recording or stop and append.
        # User requirement implies continuous reaction. 
        # We will keep recording running even if paused, to capture reactions during pause.
        # Or if strictly "record reaction", maybe reaction to pause is relevant?
        # Let's keep it running.
        pass

    def _stop_recording(self):
        """Stop recording."""
        if self.is_recording:
            self.camera_handler.stop_recording()
            self.is_recording = False
            self.recording_dot.stop()
            self.rec_label.hide()
            self.recording_dot.hide()
    
    def _on_media_status_changed(self, status):
        """Handle media status changes."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_button.setText("↺ Replay Video")
            self.status_label.setText("Video ended. You can finish or replay.")
    
    def _on_finish(self):
        """Handle finish button."""
        self.media_player.stop()
        self._stop_recording()
        self.camera_handler.stop()
        self.interview_complete.emit()
    
    def stop(self):
        """Stop everything when leaving page."""
        self.media_player.stop()
        self._stop_recording()
    
    def paintEvent(self, event):
        """Paint gradient background."""
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0a0a0f"))
        gradient.setColorAt(0.5, QColor("#12121a"))
        gradient.setColorAt(1.0, QColor("#0f0f18"))
        painter.fillRect(self.rect(), gradient)
