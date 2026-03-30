"""
Session Selection Page — Supabase-backed
Loads all sessions from Supabase instead of scanning a local directory.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QSplitter, QFrame, QGraphicsDropShadowEffect,
    QDialog, QTextBrowser, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ui.theme import Theme
from core.career_model import CareerPersonalityModel

# Add ISP root to path so shared module is importable
_ISP_ROOT = Path(__file__).resolve().parents[3]
if str(_ISP_ROOT) not in sys.path:
    sys.path.insert(0, str(_ISP_ROOT))

from shared.db_manager import ProjectDatabaseManager


class SessionSelectionPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selected_session_id = None     # Supabase UUID (the handshake key)
        self.selected_user_data = None

        try:
            self.db_manager = ProjectDatabaseManager()
        except EnvironmentError as e:
            QMessageBox.critical(self, "Configuration Error", str(e))
            self.db_manager = None

        # Apply Global Theme
        self.setStyleSheet(Theme.global_style() + """
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Session Selection")
        title.setStyleSheet(f"""
            font-size: 26px;
            font-weight: 700;
            color: {Theme.COLOR_TEXT_MAIN};
            margin-bottom: 20px;
        """)
        layout.addWidget(title)

        # Main Content (Splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Theme.COLOR_BORDER};
            }}
        """)

        # Left: Session List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 20, 0)
        left_layout.setSpacing(10)

        list_label = QLabel("Available Sessions")
        list_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {Theme.COLOR_TEXT_SEC};")

        self.session_list = QListWidget()
        self.session_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.session_list.itemClicked.connect(self.on_session_selected)

        left_layout.addWidget(list_label)
        left_layout.addWidget(self.session_list)

        # Right: Details & Action
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 0, 0, 0)
        right_layout.setSpacing(15)

        details_header = QLabel("Session Details")
        details_header.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {Theme.COLOR_TEXT_SEC};")

        # Details Pane (Card Style)
        self.details_frame = QFrame()
        self.details_frame.setStyleSheet(f"""
            QFrame {{
                {Theme.card_style()}
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 212, 255, 40))
        shadow.setOffset(0, 5)
        self.details_frame.setGraphicsEffect(shadow)

        details_layout = QVBoxLayout(self.details_frame)
        details_layout.setContentsMargins(20, 20, 20, 20)

        self.details_label = QLabel("Select a session to view details.")
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.details_label.setStyleSheet(f"""
            font-size: 14px;
            color: {Theme.COLOR_TEXT_MAIN};
            border: none;
            background: transparent;
        """)

        details_layout.addWidget(self.details_label)
        details_layout.addStretch()

        # Action Buttons
        self.report_btn = QPushButton("SHOW REPORT")
        self.report_btn.setEnabled(False)
        self.report_btn.setFixedHeight(50)
        self.report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.report_btn.setStyleSheet(Theme.button_secondary())
        self.report_btn.clicked.connect(self.show_report_dialog)

        self.process_btn = QPushButton("Start Processing")
        self.process_btn.setEnabled(False)
        self.process_btn.setFixedHeight(50)
        self.process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_btn.setStyleSheet(Theme.button_primary())
        self.process_btn.clicked.connect(self.process_session)

        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.setFixedHeight(50)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(Theme.button_secondary())
        self.refresh_btn.clicked.connect(self.load_sessions)

        right_layout.addWidget(details_header)
        right_layout.addWidget(self.details_frame, 2)
        right_layout.addSpacing(10)
        right_layout.addWidget(self.report_btn)
        right_layout.addWidget(self.refresh_btn)
        right_layout.addWidget(self.process_btn)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        self.load_sessions()

    def load_sessions(self):
        """Fetch all sessions from Supabase and populate the list."""
        self.session_list.clear()
        self.process_btn.setEnabled(False)
        self.report_btn.setEnabled(False)
        self.details_label.setText("Select a session to view details.")

        if not self.db_manager:
            self.details_label.setText("Database not available (check .env configuration).")
            return

        sessions = self.db_manager.list_sessions()
        if not sessions:
            self.details_label.setText("No sessions found in Supabase.")
            return

        for session in sessions:
            name = session.get("name") or "Unknown"
            created_at = (session.get("created_at") or "")[:10]  # Date only
            display_name = f"{name}  ({created_at})"

            item = QListWidgetItem(display_name)
            # Store the full session dict as item data
            item.setData(Qt.ItemDataRole.UserRole, session)
            self.session_list.addItem(item)

    def on_session_selected(self, item):
        session = item.data(Qt.ItemDataRole.UserRole)
        self.selected_session_id = session.get("id")
        self.selected_user_data = session

        name = session.get("name") or "N/A"
        email = session.get("email") or "N/A"
        mobile = session.get("mobile") or "N/A"
        age = session.get("age") or "N/A"
        job = session.get("job_profile") or "N/A"
        created = (session.get("created_at") or "")[:19].replace("T", " ")

        has_video = bool(session.get("interview_video"))
        is_processed = bool(session.get("ocean_score"))
        has_report = bool(session.get("report_pdf_url"))

        details = (
            f"<b style='font-size:15px; color:{Theme.COLOR_TEXT_MAIN};'>{name}</b>"
            f"<hr style='border: 1px solid {Theme.COLOR_BORDER};'><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Email:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{email}</span><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Mobile:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{mobile}</span><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Age:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{age}</span><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Job Profile:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{job}</span><br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Created:</span> "
            f"<span style='color:{Theme.COLOR_TEXT_MAIN}; font-weight:600;'>{created}</span><br>"
            f"<br>"
            f"<span style='color:{Theme.COLOR_TEXT_SEC};'>Session ID:</span> "
            f"<span style='font-family:monospace; color:{Theme.COLOR_PRIMARY}; font-size:11px;'>"
            f"{self.selected_session_id}</span><br>"
        )

        if has_video:
            status_color = Theme.COLOR_SUCCESS if not is_processed else Theme.COLOR_SUCCESS
            status_text = "✓ Processing Complete" if is_processed else "✓ Video ready for processing"
            details += f"<br><span style='color:{status_color}; font-weight:bold;'>{status_text}</span>"
        else:
            details += f"<br><span style='color:{Theme.COLOR_DANGER}; font-weight:bold;'>⚠ No video uploaded yet</span>"

        self.details_label.setText(details)

        # Enable buttons based on state
        if has_video and not is_processed:
            self.process_btn.setVisible(True)
            self.process_btn.setEnabled(True)
        else:
            self.process_btn.setVisible(False)
            self.process_btn.setEnabled(False)

        if is_processed or has_report:
            self.report_btn.setVisible(True)
            self.report_btn.setEnabled(True)
        else:
            self.report_btn.setVisible(False)
            self.report_btn.setEnabled(False)

    def process_session(self):
        """Start processing the selected session — pass session_id (UUID) to alignment page."""
        if self.selected_user_data and self.selected_session_id:
            self.main_window.go_to_alignment_page(
                self.selected_user_data,
                self.selected_session_id,
            )

    def show_report_dialog(self):
        """Open the report PDF URL from Supabase in the default browser."""
        if not self.selected_user_data:
            return

        report_url = self.selected_user_data.get("report_pdf_url")
        if report_url:
            import webbrowser
            try:
                webbrowser.open(report_url)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open report URL:\n{e}")
        else:
            QMessageBox.information(
                self, "Not Found",
                "PDF Report not found for this session. It may not be fully processed yet."
            )
