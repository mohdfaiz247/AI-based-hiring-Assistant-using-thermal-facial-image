"""
AI Hiring Assistant - Registration Page
Sleek glassmorphism card with refined input fields.
Aesthetic: Neo-Corporate Futurism
"""

import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QFrame,
    QSpacerItem, QSizePolicy, QSpinBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient


class GlassCard(QFrame):
    """Glassmorphism styled card container."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassCard")
        self._setup_style()
    
    def _setup_style(self):
        self.setStyleSheet("""
            QFrame#glassCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(35, 35, 50, 0.85), 
                                            stop:1 rgba(25, 25, 38, 0.9));
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-radius: 24px;
            }
        """)
        
        # Cyan glow shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 212, 255, 40))
        self.setGraphicsEffect(shadow)


class StyledInput(QLineEdit):
    """Custom styled input with focus glow."""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(52)
        self._apply_style()
    
    def _apply_style(self):
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 15, 25, 0.7);
                color: #f8f9fa;
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-radius: 12px;
                padding: 0 18px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
                background: rgba(15, 15, 25, 0.9);
            }
            QLineEdit:hover {
                border: 1px solid rgba(0, 212, 255, 0.5);
            }
            QLineEdit[error="true"] {
                border: 1px solid #ff4757;
                background: rgba(255, 71, 87, 0.1);
            }
        """)


class RegistrationPage(QWidget):
    """
    Registration form with glassmorphism card styling.
    Premium input fields with validation and visual feedback.
    """
    
    registration_complete = pyqtSignal(dict)
    back_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the registration page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(0)
        
        # Top spacer
        main_layout.addStretch(1)
        
        # Header section - TRANSPARENT
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Step indicator
        step_label = QLabel("STEP 1 OF 5")
        step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_label.setStyleSheet("""
            color: #00d4ff;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 2px;
            background: transparent;
        """)
        header_layout.addWidget(step_label)
        
        # Main heading
        heading = QLabel("Create Your Profile")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        heading.setStyleSheet("color: #f8f9fa; letter-spacing: -1px; background: transparent;")
        header_layout.addWidget(heading)
        
        # Subtitle
        subtitle = QLabel("Tell us about yourself to personalize your experience")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #6c757d; font-size: 15px; background: transparent;")
        header_layout.addWidget(subtitle)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(40)
        
        # Glass card container
        card = GlassCard()
        card.setFixedWidth(520)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 35, 40, 35)
        card_layout.setSpacing(0)
        
        # Name field
        self.name_input = self._create_field(card_layout, "Full Name", "Enter your full name", is_first=True)
        
        # Email field
        self.email_input = self._create_field(card_layout, "Email Address", "you@example.com")
        
        # Phone field
        self.phone_input = self._create_field(card_layout, "Phone Number", "+1 (555) 000-0000")
        
        # Job Profile field
        job_profile_layout = QVBoxLayout()
        job_profile_layout.setContentsMargins(0, 16, 0, 0)
        job_profile_layout.setSpacing(6)
        
        job_profile_label = QLabel("Job Profile")
        job_profile_label.setFixedHeight(20)
        job_profile_label.setStyleSheet("color: #adb5bd; font-size: 13px; font-weight: 500; background: transparent; padding: 0; margin: 0;")
        job_profile_layout.addWidget(job_profile_label)
        
        self.job_profile_input = QComboBox()
        self.job_profile_input.addItems(["Select Job Profile", "Software Engineer", "Data Scientist", "Product Manager", "UI/UX Designer", "Marketing", "Other"])
        self.job_profile_input.setFixedHeight(52)
        self.job_profile_input.setStyleSheet("""
            QComboBox {
                background: rgba(15, 15, 25, 0.7);
                color: #f8f9fa;
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-radius: 12px;
                padding: 0 18px;
                font-size: 15px;
            }
            QComboBox:focus {
                border: 2px solid #00d4ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #00d4ff;
            }
            QComboBox QAbstractItemView {
                background: #1a1a24;
                color: #f8f9fa;
                selection-background-color: rgba(0, 212, 255, 0.2);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                padding: 5px;
            }
        """)
        job_profile_layout.addWidget(self.job_profile_input)
        card_layout.addLayout(job_profile_layout)
        
        # Age and Gender row
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 16, 0, 0)
        row_layout.setSpacing(20)
        
        # Age
        age_layout = QVBoxLayout()
        age_layout.setContentsMargins(0, 0, 0, 0)
        age_layout.setSpacing(6)
        
        age_label = QLabel("Age")
        age_label.setFixedHeight(20)
        age_label.setStyleSheet("color: #adb5bd; font-size: 13px; font-weight: 500; background: transparent; padding: 0; margin: 0;")
        age_layout.addWidget(age_label)
        
        self.age_input = QSpinBox()
        self.age_input.setRange(18, 80)
        self.age_input.setValue(25)
        self.age_input.setFixedHeight(52)
        self.age_input.setStyleSheet("""
            QSpinBox {
                background: rgba(15, 15, 25, 0.7);
                color: #f8f9fa;
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-radius: 12px;
                padding: 0 18px;
                font-size: 15px;
            }
            QSpinBox:focus {
                border: 2px solid #00d4ff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 24px;
                border: none;
                background: transparent;
            }
        """)
        age_layout.addWidget(self.age_input)
        row_layout.addLayout(age_layout)
        
        # Gender
        gender_layout = QVBoxLayout()
        gender_layout.setContentsMargins(0, 0, 0, 0)
        gender_layout.setSpacing(6)
        
        gender_label = QLabel("Gender")
        gender_label.setFixedHeight(20)
        gender_label.setStyleSheet("color: #adb5bd; font-size: 13px; font-weight: 500; background: transparent; padding: 0; margin: 0;")
        gender_layout.addWidget(gender_label)
        
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Select Gender", "Male", "Female", "Non-binary", "Prefer not to say"])
        self.gender_input.setFixedHeight(52)
        self.gender_input.setStyleSheet("""
            QComboBox {
                background: rgba(15, 15, 25, 0.7);
                color: #f8f9fa;
                border: 1px solid rgba(0, 212, 255, 0.25);
                border-radius: 12px;
                padding: 0 18px;
                font-size: 15px;
            }
            QComboBox:focus {
                border: 2px solid #00d4ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #00d4ff;
            }
            QComboBox QAbstractItemView {
                background: #1a1a24;
                color: #f8f9fa;
                selection-background-color: rgba(0, 212, 255, 0.2);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                padding: 5px;
            }
        """)
        gender_layout.addWidget(self.gender_input)
        
        self.gender_error = QLabel("")
        self.gender_error.setStyleSheet("color: #ff4757; font-size: 12px; background: transparent;")
        self.gender_error.hide()
        gender_layout.addWidget(self.gender_error)
        
        row_layout.addLayout(gender_layout)
        card_layout.addLayout(row_layout)
        
        # Center the card
        card_wrapper = QHBoxLayout()
        card_wrapper.addStretch()
        card_wrapper.addWidget(card)
        card_wrapper.addStretch()
        main_layout.addLayout(card_wrapper)
        
        main_layout.addSpacing(40)
        
        # Buttons - transparent container
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.setFixedSize(140, 52)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.setStyleSheet("""
            QPushButton {
                background: rgba(30, 30, 45, 0.6);
                color: #adb5bd;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 26px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                border-color: #00d4ff;
                color: #00d4ff;
                background: rgba(0, 212, 255, 0.1);
            }
        """)
        self.back_button.clicked.connect(self._on_back_clicked)
        
        # Next button
        self.next_button = QPushButton("Continue →")
        self.next_button.setFixedSize(180, 52)
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.setFont(QFont("Segoe UI", 15, QFont.Weight.DemiBold))
        self.next_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #00d4ff, stop:1 #a855f7);
                color: #0a0a0f;
                border: none;
                border-radius: 26px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #00e5ff, stop:0.5 #00d4ff, stop:1 #a855f7);
            }
        """)
        
        # Add glow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 212, 255, 100))
        self.next_button.setGraphicsEffect(shadow)
        self.next_button.clicked.connect(self._on_next_clicked)
        
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.next_button)
        main_layout.addLayout(button_layout)
        
        main_layout.addStretch(2)
    
    def _create_field(self, parent_layout, label_text, placeholder, is_first=False):
        """Create a styled input field with label."""
        layout = QVBoxLayout()
        top_margin = 0 if is_first else 16
        layout.setContentsMargins(0, top_margin, 0, 0)
        layout.setSpacing(6)
        
        # Label
        label = QLabel(label_text)
        label.setFixedHeight(20)
        label.setStyleSheet("color: #adb5bd; font-size: 13px; font-weight: 500; background: transparent; padding: 0; margin: 0;")
        layout.addWidget(label)
        
        # Input
        input_field = StyledInput(placeholder)
        layout.addWidget(input_field)
        
        # Error label
        error_label = QLabel("")
        error_label.setStyleSheet("color: #ff4757; font-size: 12px; background: transparent;")
        error_label.hide()
        layout.addWidget(error_label)
        
        input_field.error_label = error_label
        parent_layout.addLayout(layout)
        
        return input_field
    
    def _validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _show_error(self, input_field, message):
        input_field.setProperty("error", True)
        input_field.style().unpolish(input_field)
        input_field.style().polish(input_field)
        if hasattr(input_field, 'error_label'):
            input_field.error_label.setText(message)
            input_field.error_label.show()
    
    def _clear_error(self, input_field):
        input_field.setProperty("error", False)
        input_field.style().unpolish(input_field)
        input_field.style().polish(input_field)
        if hasattr(input_field, 'error_label'):
            input_field.error_label.hide()
    
    def _on_next_clicked(self):
        """Handle next button with validation."""
        is_valid = True
        
        # Validate name
        name = self.name_input.text().strip()
        if not name:
            self._show_error(self.name_input, "Name is required")
            is_valid = False
        else:
            self._clear_error(self.name_input)
        
        # Validate email
        email = self.email_input.text().strip()
        if not email:
            self._show_error(self.email_input, "Email is required")
            is_valid = False
        elif not self._validate_email(email):
            self._show_error(self.email_input, "Please enter a valid email")
            is_valid = False
        else:
            self._clear_error(self.email_input)
        
        # Validate phone
        phone = self.phone_input.text().strip()
        if not phone:
            self._show_error(self.phone_input, "Phone is required")
            is_valid = False
        else:
            self._clear_error(self.phone_input)
        
        # Validate gender
        if self.gender_input.currentIndex() == 0:
            self.gender_error.setText("Please select a gender")
            self.gender_error.show()
            is_valid = False
        else:
            self.gender_error.hide()
        
        if not is_valid:
            return
            
        job_profile_val = self.job_profile_input.currentText()
        if self.job_profile_input.currentIndex() == 0:
            job_profile_val = ""
        
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "age": self.age_input.value(),
            "gender": self.gender_input.currentText(),
            "job_profile": job_profile_val
        }
        
        self.registration_complete.emit(data)
    
    def _on_back_clicked(self):
        self.back_clicked.emit()
    
    def reset(self):
        """Reset all form fields."""
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.age_input.setValue(25)
        self.gender_input.setCurrentIndex(0)
        self.job_profile_input.setCurrentIndex(0)
        
        self._clear_error(self.name_input)
        self._clear_error(self.email_input)
        self._clear_error(self.phone_input)
        self.gender_error.hide()
    
    def paintEvent(self, event):
        """Paint gradient background."""
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0a0a0f"))
        gradient.setColorAt(0.5, QColor("#12121a"))
        gradient.setColorAt(1.0, QColor("#0f0f18"))
        painter.fillRect(self.rect(), gradient)
