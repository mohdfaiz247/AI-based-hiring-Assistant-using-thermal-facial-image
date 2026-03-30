import os
import cv2
import time
import sys
import numpy as np
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QFrame, QGridLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QColor
from ui.theme import Theme

# Core logic imports
from core.camera_manager import CameraManager
from core.landmark_detector import LandmarkDetector
from core.alignment_logic import AlignmentLogic
from core.thermal_processor import ThermalProcessor
from core.data_logger import DataLogger
from core.gan_validator import GANValidator

# Supabase manager
_ISP_ROOT = Path(__file__).resolve().parents[3]
if str(_ISP_ROOT) not in sys.path:
    sys.path.insert(0, str(_ISP_ROOT))
from shared.db_manager import ProjectDatabaseManager

class AlignmentPage(QWidget):
    def __init__(self, main_window, db_manager: ProjectDatabaseManager):
        super().__init__()
        self.main_window = main_window
        self.db_manager = db_manager

        # --- CORE LOGIC INSTANCES ---
        self.detector = LandmarkDetector()
        self.aligner = AlignmentLogic()
        self.processor = ThermalProcessor()
        self.logger = DataLogger()
        self.validator = GANValidator()

        # --- STATE ---
        self.video_writer = None
        self.capture_mode = "IMAGE"
        self.recording = False
        self.paused = False
        self.face_ready = False
        self.aligned_frames = 0
        self.required_stable_frames = 18
        self.frame_counter = 0

        # Temp file references (cleaned up after upload)
        self._temp_video_path = None   # Path to downloaded video temp file
        self._session_id = None        # Active Supabase session UUID

        # --- CAMERA & TIMER ---
        self.video_source = None
        self.is_video_file = True
        self.camera = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # ---------- UI LAYOUT & STYLE ----------
        self.setStyleSheet(Theme.global_style())

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # LEFT: DUAL VIDEO DISPLAY
        self.video_container = QVBoxLayout()
        self.video_container.setSpacing(10)
        
        # RGB Feed Frame
        self.rgb_frame_container = QFrame()
        self.rgb_frame_container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.COLOR_BORDER};
                border: 1px solid {Theme.COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        rgb_layout = QVBoxLayout(self.rgb_frame_container)
        rgb_layout.setContentsMargins(1,1,1,1)

        self.camera_label = QLabel("Initializing Video Feed...")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background: #000; color: #94a3b8; border-radius: 6px;")
        self.camera_label.setFixedSize(640, 360) 
        
        rgb_layout.addWidget(self.camera_label)
        
        # Validation Feed Frame
        self.val_frame_container = QFrame()
        self.val_frame_container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.COLOR_BG};
                border: 1px solid {Theme.COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        val_layout = QVBoxLayout(self.val_frame_container)
        val_layout.setContentsMargins(1,1,1,1)

        self.validation_label = QLabel("GAN Validation Stream (Waiting)")
        self.validation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.validation_label.setStyleSheet(f"background: {Theme.COLOR_BG}; color: {Theme.COLOR_TEXT_SEC}; font-size: 11px; border-radius: 6px;")
        self.validation_label.setFixedSize(640, 200)

        val_layout.addWidget(self.validation_label)
        
        self.video_container.addWidget(self.rgb_frame_container)
        self.video_container.addWidget(self.val_frame_container)

        # RIGHT: CONTROL PANEL
        panel = QVBoxLayout()
        panel.setSpacing(20)
        
        # -- Session Info Card --
        self.session_card = QLabel()
        self.session_card.setWordWrap(True)
        self.session_card.setStyleSheet(Theme.card_style() + "padding: 15px; font-size: 13px;")
        
        # Add shadow to session card
        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(10)
        card_shadow.setColor(QColor(0, 0, 0, 10))
        card_shadow.setOffset(0, 2)
        self.session_card.setGraphicsEffect(card_shadow)
        
        # -- Instruction / Status Display --
        self.instruction_display = QFrame()
        self.instruction_display.setStyleSheet(Theme.card_style())
        
        inst_layout = QVBoxLayout(self.instruction_display)
        
        self.status_label = QLabel("Status: Idle")
        self.status_label.setStyleSheet(f"color: {Theme.COLOR_TEXT_SEC}; font-weight: 600; font-size: 12px; margin-bottom: 5px;")
        
        self.instruction_card = QLabel("Align face with guides")
        self.instruction_card.setWordWrap(True)
        self.instruction_card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_card.setStyleSheet(f"color: {Theme.COLOR_TEXT_MAIN}; font-size: 16px; font-weight: 700;")
        
        inst_layout.addWidget(self.status_label)
        inst_layout.addWidget(self.instruction_card)

        # -- Controls --
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        self.start_btn = QPushButton("Start Recording")
        self.start_btn.setFixedHeight(45)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet(Theme.button_primary())
        
        self.pause_btn = QPushButton("Pause Stream")
        self.pause_btn.setFixedHeight(45)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Using a custom style for "Warning" button as it's not in standard Theme yet, or reuse secondary
        self.pause_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 215, 0, 0.1);
                color: {Theme.COLOR_WARNING};
                font-size: 14px;
                font-weight: bold;
                border: 1px solid rgba(255, 215, 0, 0.3);
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 215, 0, 0.2);
                border-color: {Theme.COLOR_WARNING};
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
                border: none;
            }}
        """)
        
        self.stop_btn = QPushButton("Stop & Save")
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet(Theme.button_danger())
        
        self.reset_btn = QPushButton("Back to Selection")
        self.reset_btn.setFixedHeight(45)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet(Theme.button_secondary())

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        self.start_btn.clicked.connect(self.start_recording)
        self.pause_btn.clicked.connect(self.pause_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.reset_btn.clicked.connect(self.go_back)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.reset_btn)

        panel.addWidget(self.session_card)
        panel.addWidget(self.instruction_display)
        panel.addLayout(btn_layout)
        panel.addStretch()

        main_layout.addLayout(self.video_container, 3)
        main_layout.addLayout(panel, 1)

    def set_session(self, user_data: dict, session_id: str):
        """
        Prepare the alignment page for processing a session.

        Downloads the interview video from Supabase Storage to a local temp file,
        then loads it into CameraManager.

        Args:
            user_data:  Session dict from Supabase (name, email, etc.).
            session_id: The Supabase UUID for the session.
        """
        self.user_data = user_data
        self._session_id = session_id
        self.capture_mode = "VIDEO_PROCESSING"

        self.session_card.setText(
            f"<b style='color:{Theme.COLOR_TEXT_MAIN}; font-size:14px;'>Applicant Info</b><br><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Name:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{user_data.get('name', 'Unknown')}</span><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Session ID:</span> "
            f"<span style='color:{Theme.COLOR_PRIMARY}; font-size:10px; font-family:monospace;'>{session_id}</span><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Email:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{user_data.get('email', 'Unknown')}</span><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Mode:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{self.capture_mode}</span>"
        )

        # Release previous camera if any
        if self.camera:
            self.camera.release()

        # Clean up any previous temp video
        self._cleanup_temp_video()

        # Download video from Supabase to a temp file
        try:
            self.status_label.setText("Status: Downloading video…")
            self._temp_video_path = self.db_manager.download_video(session_id)
            self.video_source = str(self._temp_video_path)
            print(f"[AlignmentPage] Video ready at: {self.video_source}")
        except RuntimeError as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Download Error", str(e))
            return

        self.camera = CameraManager(self.video_source)
        self.reset_state()
        self.timer.start(30)

    def _cleanup_temp_video(self):
        """Delete the temp video file if it exists."""
        if self._temp_video_path and self._temp_video_path.exists():
            try:
                self._temp_video_path.unlink()
                print(f"[AlignmentPage] Cleaned up temp video: {self._temp_video_path}")
            except Exception as e:
                print(f"[AlignmentPage] Could not delete temp video: {e}")
        self._temp_video_path = None

    def reset_state(self):
        self.recording = False
        self.paused = False
        self.face_ready = False
        self.aligned_frames = 0
        self.frame_counter = 0
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Idle")
        self.status_label.setStyleSheet(f"color: {Theme.COLOR_TEXT_SEC}; font-weight: 600; font-size: 12px; margin-bottom: 5px;")
        self.instruction_card.setText("Align face with guides")
        self.instruction_card.setStyleSheet(f"color: {Theme.COLOR_TEXT_MAIN}; font-size: 16px; font-weight: 700;")
        self.rgb_frame_container.setStyleSheet(f"background-color: {Theme.COLOR_BORDER}; border: 1px solid {Theme.COLOR_BORDER}; border-radius: 8px;")
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

    def update_frame(self):
        if not self.camera:
            return
            
        ret, frame = self.camera.read() 
        if not ret:
            if self.is_video_file:
                print("Video file finished.")
                self.stop_recording()
                self.timer.stop()
            return
            
        thermal_frame = frame.copy() 

        landmarks = self.detector.get_landmarks(frame)

        if landmarks is not None:
            thermal_landmarks = self.aligner.map_points(landmarks)

            fake_thermal = self.validator.generate_synthetic_thermal(frame)
            validation_frame = self.validator.validate_alignment(fake_thermal, thermal_landmarks)
            self.display_frame(validation_frame, self.validation_label)

            for (x, y) in landmarks:
                cv2.circle(frame, (x, y), 2, (255, 212, 0), -1) # Cyan Dots (BGR for #00d4ff)

            nose_x, nose_y = landmarks[30]
            cx, cy = frame.shape[1]//2, frame.shape[0]//2

            if abs(nose_x-cx) < 80 and abs(nose_y-cy) < 100:
                self.aligned_frames += 1
                self.instruction_card.setText("Hold Position...")
                self.instruction_card.setStyleSheet(f"color: {Theme.COLOR_WARNING}; font-size: 16px; font-weight: 700;")
                self.rgb_frame_container.setStyleSheet(f"background-color: {Theme.COLOR_WARNING_BG}; border: 2px solid {Theme.COLOR_WARNING}; border-radius: 8px;")
            else:
                self.aligned_frames = 0
                self.instruction_card.setText("Center Face")
                self.instruction_card.setStyleSheet(f"color: {Theme.COLOR_DANGER}; font-size: 16px; font-weight: 700;")
                self.rgb_frame_container.setStyleSheet(f"background-color: {Theme.COLOR_DANGER_BG}; border: 2px solid {Theme.COLOR_DANGER}; border-radius: 8px;")

            # For video files, relax the stable frame requirement to ensure processing starts
            current_required_frames = 1 if self.is_video_file else self.required_stable_frames

            if self.aligned_frames >= current_required_frames or self.is_video_file:
                self.face_ready = True
                self.instruction_card.setText("Alignment Confirmed" if not self.is_video_file else "Processing Video...")
                self.instruction_card.setStyleSheet(f"color: {Theme.COLOR_SUCCESS}; font-size: 16px; font-weight: 700;")
                self.rgb_frame_container.setStyleSheet(f"background-color: {Theme.COLOR_SUCCESS_BG}; border: 2px solid {Theme.COLOR_SUCCESS}; border-radius: 8px;")
                self.status_label.setText("Status: Ready")
                self.status_label.setStyleSheet(f"color: {Theme.COLOR_SUCCESS}; font-weight: 600; font-size: 12px; margin-bottom: 5px;")
                
                if self.capture_mode == "VIDEO" and not self.recording:
                    self.start_btn.setEnabled(True)

            if self.recording and not self.paused:
                self.frame_counter += 1
                stim_data = self.processor.extract_stimulus_data(thermal_frame, thermal_landmarks)
                self.logger.log_frame(self.frame_counter, thermal_landmarks, stim_data)
                if self.video_writer: self.video_writer.write(frame)

        else:
            self.aligned_frames = 0
            self.instruction_card.setText("Searching for Subject...")
            self.instruction_card.setStyleSheet(f"color: {Theme.COLOR_TEXT_SEC}; font-size: 16px; font-weight: 700;")
            self.rgb_frame_container.setStyleSheet(f"background-color: {Theme.COLOR_BORDER}; border: 1px solid {Theme.COLOR_BORDER}; border-radius: 8px;")

        self.display_frame(frame, self.camera_label)

        if self.is_video_file and not self.recording and self.face_ready:
             self.start_recording()

    def display_frame(self, frame, label):
        if frame is None: return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch*w, QImage.Format.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(img).scaled(
            label.width(), 
            label.height(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        ))

    def start_recording(self):
        if not self.face_ready: return
        os.makedirs("data/videos", exist_ok=True)
        user_id = self.user_data.get('id', 'unknown_id')
        filename = f"data/videos/{user_id}_{int(time.time())}.avi"
        self.video_writer = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*"XVID"), 20.0, (640, 480))
        self.recording = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        self.status_label.setText("Status: Recording")
        self.status_label.setStyleSheet(f"color: {Theme.COLOR_DANGER}; font-weight: 600; font-size: 12px; margin-bottom: 5px;")

    def pause_recording(self):
        if self.recording:
            self.paused = not self.paused
            self.pause_btn.setText("Resume" if self.paused else "Pause Stream")

    def stop_recording(self):
        self.recording = False
        if self.video_writer:
            self.video_writer.release()

        self.status_label.setText("Status: Data Saved")
        self.status_label.setStyleSheet(
            f"color: {Theme.COLOR_SUCCESS}; font-weight: 600; font-size: 12px; margin-bottom: 5px;"
        )

        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)

        csv_local_path = self.logger.file_path

        # Upload the DataLogger CSV to Supabase if we have an active session
        if self._session_id:
            try:
                self.status_label.setText("Status: Uploading CSV…")
                from pathlib import Path as _Path
                self.db_manager.upload_csv(self._session_id, _Path(csv_local_path))
                print(f"[AlignmentPage] CSV uploaded for session {self._session_id}")
            except Exception as e:
                print(f"[AlignmentPage] CSV upload warning: {e}")

        # Transition to ML Result Page
        # Pass session_id (UUID) — ml_result_page will fetch OCEAN scores and image from Supabase
        if self._session_id:
            session_id = self._session_id
            QTimer.singleShot(
                1000,
                lambda: self.main_window.go_to_ml_result_page(
                    self.user_data, session_id, csv_path=csv_local_path
                )
            )
        else:
            print("[AlignmentPage] Error: No session_id set — cannot transition.")

        # Schedule temp video cleanup after transition
        QTimer.singleShot(6000, self._cleanup_temp_video)

    def go_back(self):
        self.stop_recording()
        self.timer.stop()
        if self.camera:
            self.camera.release()
        self.main_window.go_to_session_selection_page()