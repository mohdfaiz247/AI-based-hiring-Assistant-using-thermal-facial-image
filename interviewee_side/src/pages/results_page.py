"""
AI Hiring Assistant - Results Page
Stunning results dashboard with score visualizations.
Aesthetic: Neo-Corporate Futurism
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QTextBrowser,
    QGraphicsDropShadowEffect, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient


class SuccessBadge(QWidget):
    """Large success checkmark with glow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Outer glow rings
        for i in range(4):
            painter.setBrush(QColor(0, 255, 163, 20 - i * 5))
            painter.setPen(Qt.PenStyle.NoPen)
            size = 120 - i * 10
            offset = i * 5
            painter.drawEllipse(offset, offset, size, size)
        
        # Inner circle
        painter.setBrush(QColor(0, 255, 163))
        painter.drawEllipse(30, 30, 60, 60)
        
        # Checkmark
        from PyQt6.QtGui import QPen
        pen = QPen(QColor("#0a0a0f"))
        pen.setWidth(5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw checkmark path
        painter.drawLine(45, 60, 55, 72)
        painter.drawLine(55, 72, 78, 48)





class InfoCard(QFrame):
    """User information card."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_base()
    
    def _setup_base(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(30, 30, 42, 0.8), 
                                            stop:1 rgba(20, 20, 30, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 20px;
            }
        """)


class ResultsPage(QWidget):
    """
    Stunning results dashboard with OCEAN score visualizations.
    Summary cards and data explorer.
    """
    
    restart_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent; width: 8px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 4px;
            }
        """)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(60, 40, 60, 40)
        content_layout.setSpacing(40)
        
        # Success header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(20)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        badge = SuccessBadge()
        header_layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        
        heading = QLabel("Assessment Complete!")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setFont(QFont("Segoe UI", 42, QFont.Weight.Bold))
        heading.setStyleSheet("color: #f8f9fa; letter-spacing: -1px;")
        header_layout.addWidget(heading)
        
        subtitle = QLabel("Your data has been saved to the cloud ✓")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #6c757d; font-size: 16px;")
        header_layout.addWidget(subtitle)
        
        content_layout.addWidget(header)
        

        
        # Info cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)
        
        # Personal info card
        self.info_card = InfoCard("Profile")
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(25, 25, 25, 25)
        info_layout.setSpacing(16)
        
        info_title = QLabel("👤 Personal Info")
        info_title.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        info_title.setStyleSheet("color: #f8f9fa;")
        info_layout.addWidget(info_title)
        
        self.info_content = QLabel("")
        self.info_content.setStyleSheet("color: #adb5bd; font-size: 14px; line-height: 1.8;")
        info_layout.addWidget(self.info_content)
        info_layout.addStretch()
        
        cards_row.addWidget(self.info_card)
        cards_row.addStretch()
        
        content_layout.addLayout(cards_row)
        
        # Action buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)
        
        self.restart_button = QPushButton("✨ Start New Session")
        self.restart_button.setFixedSize(240, 56)
        self.restart_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restart_button.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        self.restart_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #00d4ff, stop:1 #a855f7);
                color: #0a0a0f;
                border: none;
                border-radius: 28px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #00e5ff, stop:1 #a855f7);
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 212, 255, 100))
        self.restart_button.setGraphicsEffect(shadow)
        self.restart_button.clicked.connect(self._on_restart)
        
        button_layout.addWidget(self.restart_button)
        
        content_layout.addWidget(button_container)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def set_data(self, registration: dict, session_id: str):
        """Populate the results page with registration data and session UUID."""
        # Personal info
        info_text = f"""
<b>Name:</b> {registration.get('name', 'N/A')}<br>
<b>Email:</b> {registration.get('email', 'N/A')}<br>
<b>Phone:</b> {registration.get('phone', 'N/A')}<br>
<b>Age:</b> {registration.get('age', 'N/A')}<br>
<b>Gender:</b> {registration.get('gender', 'N/A')}
        """
        self.info_content.setText(info_text)

        # Show session ID card for the interviewer
        if not hasattr(self, '_session_id_label'):
            from PyQt6.QtWidgets import QLabel as _QLabel
            self._session_id_label = _QLabel()
            self._session_id_label.setWordWrap(True)
            self._session_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._session_id_label.setStyleSheet("""
                color: #00d4ff;
                font-size: 12px;
                font-family: monospace;
                background: rgba(0, 212, 255, 0.05);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 8px;
                padding: 10px;
            """)
            # Insert below info_card in the layout
            parent_layout = self.info_card.parent().layout() if self.info_card.parent() else None
            if parent_layout:
                parent_layout.insertWidget(parent_layout.indexOf(self.info_card) + 1,
                                           self._session_id_label)

        self._session_id_label.setText(
            f"📋 <b>Session ID</b> (share with interviewer):<br>{session_id}"
        )
    
    def _on_restart(self):
        self.restart_clicked.emit()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0a0a0f"))
        gradient.setColorAt(0.5, QColor("#0f0f18"))
        gradient.setColorAt(1.0, QColor("#12121a"))
        painter.fillRect(self.rect(), gradient)
