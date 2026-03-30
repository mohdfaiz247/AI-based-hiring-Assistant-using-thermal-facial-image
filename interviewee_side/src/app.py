"""
AI Hiring Assistant - Main Application Controller
Manages page navigation, session lifecycle, and data flow.

Data flow (Supabase-backed):
  1. Registration → create_session() in Supabase → get UUID
  2. Face Alignment → capture image → upload_image() to Supabase
  3. Interview Recording → local temp video → upload_video() to Supabase
  4. Results page → shows Session ID UUID for interviewer reference
"""

import sys
import os
import cv2
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt

from .styles import GLOBAL_STYLESHEET
from .camera_handler import CameraHandler
from .pages.landing_page import LandingPage
from .pages.registration_page import RegistrationPage
from .pages.face_alignment_page import FaceAlignmentPage
from .pages.interview_page import InterviewPage
from .pages.results_page import ResultsPage

# Add the ISP root to sys.path so we can import the shared module
_ISP_ROOT = Path(__file__).resolve().parents[2]
if str(_ISP_ROOT) not in sys.path:
    sys.path.insert(0, str(_ISP_ROOT))

from shared.db_manager import ProjectDatabaseManager


class AIHiringAssistant(QMainWindow):
    """
    Main application window controller.
    Manages navigation between pages and coordinates data flow.
    All persistent data is stored exclusively via ProjectDatabaseManager (Supabase).
    """

    # Page indices
    PAGE_LANDING = 0
    PAGE_REGISTRATION = 1
    PAGE_FACE_ALIGNMENT = 2
    PAGE_INTERVIEW = 3
    PAGE_RESULTS = 4

    def __init__(self):
        super().__init__()

        # Initialize Supabase manager
        try:
            self.db_manager = ProjectDatabaseManager()
        except EnvironmentError as e:
            # Show error early before UI is built
            app = QApplication.instance()
            QMessageBox.critical(None, "Configuration Error", str(e))
            sys.exit(1)

        self.camera_handler = CameraHandler()

        # In-memory session data
        self.session_id: Optional[str] = None          # Supabase UUID
        self.registration_data: Dict[str, Any] = {}

        # Temp file reference for the interview video (cleaned on next session)
        self._interview_video_path: Optional[Path] = None

        # Set up UI
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("AI Hiring Assistant")
        self.setMinimumSize(1024, 768)

        self.setStyleSheet(GLOBAL_STYLESHEET)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.landing_page = LandingPage()
        self.registration_page = RegistrationPage()
        self.face_alignment_page = FaceAlignmentPage(self.camera_handler)
        self.interview_page = InterviewPage(self.camera_handler)
        self.results_page = ResultsPage()

        self.stack.addWidget(self.landing_page)       # Index 0
        self.stack.addWidget(self.registration_page)  # Index 1
        self.stack.addWidget(self.face_alignment_page) # Index 2
        self.stack.addWidget(self.interview_page)     # Index 3
        self.stack.addWidget(self.results_page)       # Index 4

        self.stack.setCurrentIndex(self.PAGE_LANDING)

    def setup_connections(self):
        """Connect page signals to navigation handlers."""
        self.landing_page.start_clicked.connect(self._go_to_registration)

        self.registration_page.registration_complete.connect(self._on_registration_complete)
        self.registration_page.back_clicked.connect(self._go_to_landing)

        self.face_alignment_page.proceed_clicked.connect(self._go_to_interview)
        self.face_alignment_page.back_clicked.connect(self._go_to_registration)

        self.interview_page.interview_complete.connect(self._on_interview_complete)
        self.interview_page.back_clicked.connect(self._go_to_face_alignment)

        self.results_page.restart_clicked.connect(self._restart_session)

    # ------------------------------------------------------------------ #
    #  Navigation handlers                                                 #
    # ------------------------------------------------------------------ #

    def _go_to_landing(self):
        self.stack.setCurrentIndex(self.PAGE_LANDING)

    def _go_to_registration(self):
        self.stack.setCurrentIndex(self.PAGE_REGISTRATION)

    def _on_registration_complete(self, data: dict):
        """Handle registration completion — create Supabase session row."""
        self.registration_data = data

        try:
            self.session_id = self.db_manager.create_session(data)
        except RuntimeError as e:
            QMessageBox.critical(self, "Error", f"Failed to create session in Supabase:\n{e}")
            return

        self._go_to_face_alignment()

    def _go_to_face_alignment(self):
        self.stack.setCurrentIndex(self.PAGE_FACE_ALIGNMENT)
        self.face_alignment_page.start()

    def _go_to_interview(self):
        """Capture aligned face image, upload to Supabase, start interview recording."""
        self.face_alignment_page.stop()

        import time
        frame = None
        for _ in range(10):
            frame = self.camera_handler.get_frame()
            if frame is not None:
                break
            time.sleep(0.05)

        # Upload aligned face image to Supabase Storage
        if frame is not None and self.session_id:
            try:
                _, jpeg_bytes = cv2.imencode(".jpg", frame)
                self.db_manager.upload_image(self.session_id, jpeg_bytes.tobytes())
            except Exception as e:
                print(f"[Warning] Could not upload profile image: {e}")

        # Prepare a temp file for the interview video recording
        tmp_video = tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp4", prefix=f"isp_interview_{self.session_id}_"
        )
        tmp_video.close()
        self._interview_video_path = Path(tmp_video.name)

        self.stack.setCurrentIndex(self.PAGE_INTERVIEW)

        # Start recording to temp path
        self.camera_handler.start_recording(self._interview_video_path)
        self.interview_page.start()

    def _on_interview_complete(self):
        """Stop recording, upload video to Supabase, navigate to results."""
        # Stop camera recording — get path to recorded file
        saved_path = self.camera_handler.stop_recording()
        video_path = saved_path or self._interview_video_path

        # Upload video to Supabase Storage
        if video_path and video_path.exists() and self.session_id:
            try:
                self.db_manager.upload_video(self.session_id, video_path)
            except Exception as e:
                QMessageBox.warning(
                    self, "Upload Warning",
                    f"Interview video could not be uploaded:\n{e}\n\n"
                    "The session was still created. You can retry via the interviewer tool."
                )
        elif not self.session_id:
            print("[Warning] No active session_id, skipping video upload.")

        # Clean up the temp file after upload
        if video_path and video_path.exists():
            try:
                video_path.unlink()
            except Exception:
                pass
        self._interview_video_path = None

        self._go_to_results()

    def _go_to_results(self):
        """Navigate to results page, passing registration data and session UUID."""
        self.results_page.set_data(
            registration=self.registration_data,
            session_id=self.session_id or "N/A",
        )
        self.stack.setCurrentIndex(self.PAGE_RESULTS)

    def _restart_session(self):
        """Reset everything for a new session."""
        self.registration_data = {}
        self.session_id = None
        self.db_manager.reset()

        self.registration_page.reset()
        self.camera_handler.stop()

        self._go_to_landing()

    def closeEvent(self, event):
        """Handle window close — stop camera."""
        self.camera_handler.stop()
        event.accept()


def run_app():
    """Run the AI Hiring Assistant application."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = AIHiringAssistant()
    window.show()

    sys.exit(app.exec())
