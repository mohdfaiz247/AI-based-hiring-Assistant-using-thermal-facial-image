import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox

from ui.home_page import HomePage
from ui.session_selection_page import SessionSelectionPage
from ui.alignment_page import AlignmentPage
from ui.ml_result_page import MlResultPage

# Add ISP root to path so shared module is importable
_ISP_ROOT = Path(__file__).resolve().parents[2]
if str(_ISP_ROOT) not in sys.path:
    sys.path.insert(0, str(_ISP_ROOT))

from shared.db_manager import ProjectDatabaseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-Based Hiring Assistant (Video Processing Mode)")
        self.setGeometry(100, 100, 1400, 800)

        # Single shared Supabase manager instance
        try:
            self.db_manager = ProjectDatabaseManager()
        except EnvironmentError as e:
            QMessageBox.critical(None, "Configuration Error", str(e))
            sys.exit(1)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pass db_manager to pages that need it
        self.home_page = HomePage(self)
        self.session_selection_page = SessionSelectionPage(self)
        self.alignment_page = AlignmentPage(self, self.db_manager)
        self.ml_result_page = MlResultPage(self, self.db_manager)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.session_selection_page)
        self.stack.addWidget(self.alignment_page)
        self.stack.addWidget(self.ml_result_page)

        self.stack.setCurrentWidget(self.home_page)

    def go_to_session_selection_page(self):
        self.session_selection_page.load_sessions()  # Refresh from Supabase
        self.stack.setCurrentWidget(self.session_selection_page)

    def go_to_alignment_page(self, user_data: dict, session_id: str):
        """
        Navigate to the alignment/processing page.

        Args:
            user_data:  Session dict from Supabase.
            session_id: Supabase UUID — used to download the interview video.
        """
        self.alignment_page.set_session(user_data, session_id)
        self.stack.setCurrentWidget(self.alignment_page)

    def go_to_ml_result_page(self, user_data: dict, session_id: str, csv_path: str = None):
        """
        Navigate to the ML result page.

        Args:
            user_data:  Session dict from Supabase.
            session_id: Supabase UUID — used to read/write ocean_score and report_pdf_url.
            csv_path:   Local path to the DataLogger CSV (generated during alignment processing).
        """
        self.ml_result_page.process_session(user_data, session_id, csv_path=csv_path)
        self.stack.setCurrentWidget(self.ml_result_page)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
