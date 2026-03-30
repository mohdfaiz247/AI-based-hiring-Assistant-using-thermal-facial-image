"""
AI Hiring Assistant - Main Application Controller
Manages page navigation, session lifecycle, and data flow.
"""

import sys
import cv2
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt

from .styles import GLOBAL_STYLESHEET
from .data_manager import DataManager
from .camera_handler import CameraHandler
from .pages.landing_page import LandingPage
from .pages.registration_page import RegistrationPage
from .pages.face_alignment_page import FaceAlignmentPage
from .pages.interview_page import InterviewPage
from .pages.results_page import ResultsPage


class AIHiringAssistant(QMainWindow):
    """
    Main application window controller.
    Manages navigation between pages and coordinates data flow.
    """
    
    # Page indices
    PAGE_LANDING = 0
    PAGE_REGISTRATION = 1
    PAGE_FACE_ALIGNMENT = 2
    PAGE_INTERVIEW = 3
    PAGE_RESULTS = 4
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.data_manager = DataManager()
        self.camera_handler = CameraHandler()
        
        # Session data storage
        self.registration_data: Dict[str, Any] = {}
        
        # Set up UI
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("AI Hiring Assistant")
        self.setMinimumSize(1024, 768)
        
        # Apply global stylesheet
        self.setStyleSheet(GLOBAL_STYLESHEET)
        
        # Central stacked widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Create pages
        self.landing_page = LandingPage()
        self.registration_page = RegistrationPage()
        self.face_alignment_page = FaceAlignmentPage(self.camera_handler)
        self.interview_page = InterviewPage(self.camera_handler, self.data_manager)
        self.results_page = ResultsPage()
        
        # Add pages to stack
        self.stack.addWidget(self.landing_page)      # Index 0
        self.stack.addWidget(self.registration_page)  # Index 1
        self.stack.addWidget(self.face_alignment_page) # Index 2
        self.stack.addWidget(self.interview_page)     # Index 3
        self.stack.addWidget(self.results_page)       # Index 4
        
        # Start on landing page
        self.stack.setCurrentIndex(self.PAGE_LANDING)
    
    def setup_connections(self):
        """Connect page signals to navigation handlers."""
        # Landing page
        self.landing_page.start_clicked.connect(self._go_to_registration)
        
        # Registration page
        self.registration_page.registration_complete.connect(self._on_registration_complete)
        self.registration_page.back_clicked.connect(self._go_to_landing)
        
        # Face alignment page
        self.face_alignment_page.proceed_clicked.connect(self._go_to_interview)
        self.face_alignment_page.back_clicked.connect(self._go_to_registration)
        
        # Interview page
        self.interview_page.interview_complete.connect(self._on_interview_complete)
        self.interview_page.back_clicked.connect(self._go_to_face_alignment)
        
        # Results page
        self.results_page.restart_clicked.connect(self._restart_session)
    
    # Navigation handlers
    
    def _go_to_landing(self):
        """Navigate to landing page."""
        self.stack.setCurrentIndex(self.PAGE_LANDING)
    
    def _go_to_registration(self):
        """Navigate to registration page."""
        self.stack.setCurrentIndex(self.PAGE_REGISTRATION)
    
    def _on_registration_complete(self, data: dict):
        """Handle registration completion."""
        self.registration_data = data
        
        # Create new session
        try:
            session_id = self.data_manager.create_session()
            self.data_manager.save_registration(data)
        except RuntimeError as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create session: {e}"
            )
            return
        
        # Navigate to face alignment
        self._go_to_face_alignment()
    
    def _go_to_face_alignment(self):
        """Navigate to face alignment page."""
        self.stack.setCurrentIndex(self.PAGE_FACE_ALIGNMENT)
        self.face_alignment_page.start()
    
    def _go_to_interview(self):
        """Navigate to interview page."""
        self.face_alignment_page.stop() # Ensure alignment page stops its loop
        
        import time
        frame = None
        for _ in range(10):
            frame = self.camera_handler.get_frame()
            if frame is not None:
                break
            time.sleep(0.05)
            
        session_folder = self.data_manager.get_session_folder()
        if frame is not None and session_folder:
            image_path = session_folder / "aligned_face.jpg"
            cv2.imwrite(str(image_path), frame)
            
        self.stack.setCurrentIndex(self.PAGE_INTERVIEW)
    
        # Start recording in background
        video_save_path = self.data_manager.get_interview_path(question_id=1)
        self.camera_handler.start_recording(video_save_path)
    
        self.interview_page.start()
    
    def _on_interview_complete(self):
        """Handle interview completion."""
        # Save basic session summary without questionnaire scores
        try:
            self.data_manager.save_summary(self.registration_data, {})
        except RuntimeError as e:
            QMessageBox.warning(
                self,
                "Warning",
                f"Failed to save data: {e}"
            )
            
        # Navigate directly to results
        self._go_to_results()
    
    def _go_to_results(self):
        """Navigate to results page."""
        # Get interview recordings
        recordings = self.data_manager.get_interview_recordings()
        
        # Get session folder
        session_folder = str(self.data_manager.get_session_folder() or "Unknown")
        
        # Set data on results page
        self.results_page.set_data(
            registration=self.registration_data,
            session_folder=session_folder
        )
        
        self.stack.setCurrentIndex(self.PAGE_RESULTS)
    
    def _restart_session(self):
        """Restart the application for a new session."""
        # Clear in-memory data
        self.registration_data = {}
        
        # Reset data manager
        self.data_manager.reset()
        
        # Reset pages
        self.registration_page.reset()
        
        # Stop camera if running
        self.camera_handler.stop()
        
        # Go back to landing
        self._go_to_landing()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop camera
        self.camera_handler.stop()
        
        # Accept close
        event.accept()


def run_app():
    """Run the AI Hiring Assistant application."""
    # Enable HighDPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for consistent look
    
    # Create and show main window
    window = AIHiringAssistant()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())
