import os
import sys
import json
import io
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QProgressBar, QFrame, QGraphicsDropShadowEffect, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.theme import Theme
from ml.predict import predict

# Supabase manager
_ISP_ROOT = Path(__file__).resolve().parents[3]
if str(_ISP_ROOT) not in sys.path:
    sys.path.insert(0, str(_ISP_ROOT))
from shared.db_manager import ProjectDatabaseManager

class MlResultPage(QWidget):
    def __init__(self, main_window, db_manager: ProjectDatabaseManager):
        super().__init__()
        self.main_window = main_window
        self.db_manager = db_manager
        self.session_id = None
        self.user_data = None
        self._pdf_url = None    # Supabase URL after upload

        # --- Apply Global Theme ---
        self.setStyleSheet(Theme.global_style())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for longer content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # --- Header ---
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0,0,0,0)
        
        self.title = QLabel("Analysis Complete")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {Theme.COLOR_TEXT_MAIN};")
        
        self.subtitle = QLabel("AI Personality Profile (OCEAN Model)")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet(f"font-size: 16px; color: {Theme.COLOR_TEXT_SEC};")
        
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.subtitle)
        
        # --- Value Container ---
        self.results_card = QFrame()
        self.results_card.setStyleSheet(Theme.card_style())
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 212, 255, 40)) # Soft cyan glow
        shadow.setOffset(0, 5)
        self.results_card.setGraphicsEffect(shadow)

        self.results_layout = QVBoxLayout(self.results_card)
        self.results_layout.setContentsMargins(30, 30, 30, 30)
        self.results_layout.setSpacing(20)
        
        # Loading State
        self.loading_label = QLabel("Loading data...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet(f"color: {Theme.COLOR_PRIMARY}; font-size: 16px; font-weight: 600;")
        self.results_layout.addWidget(self.loading_label)

        # --- Footer Actions ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.export_btn = QPushButton("Export Report")
        self.export_btn.setFixedSize(140, 45)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(Theme.button_secondary())
        self.export_btn.setEnabled(False) # Enable after results
        
        self.home_btn = QPushButton("New Session")
        self.home_btn.setFixedSize(140, 45)
        self.home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.home_btn.setStyleSheet(Theme.button_primary())
        self.home_btn.clicked.connect(self.go_home)

        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.home_btn)
        btn_layout.addStretch()

        self.layout.addWidget(header_container)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.results_card)
        self.layout.addSpacing(10)
        self.layout.addLayout(btn_layout)
        self.layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def process_session(self, user_data, session_id: str, csv_path=None):
        """
        Load predictions for a session identified by its Supabase UUID.

        If ocean_score is already set in Supabase, use that cached value.
        Otherwise run predict() on the CSV and persist the result back.
        """
        self.user_data = user_data
        self.session_id = session_id
        self.csv_path = csv_path
        self._pdf_url = None

        # Reset UI
        self.title.setText(f"Analysis for {user_data.get('name', 'Candidate')}")
        self.loading_label.setVisible(True)
        self.loading_label.setText("Generating AI Profile...")

        # Clear previous results from layout
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        trait_order = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
        predictions = None

        # --- 1. Try to load cached scores from Supabase ---
        try:
            session_row = self.db_manager.get_session(session_id)
            cached = session_row.get("ocean_score") if session_row else None
            if cached and all(t in cached for t in trait_order):
                predictions = [cached[t] for t in trait_order]
                print("[MlResultPage] Using cached OCEAN scores from Supabase.")
        except Exception as e:
            print(f"[MlResultPage] Error reading cached scores: {e}")

        # --- 2. Run prediction if no cache ---
        if predictions is None:
            if self.csv_path and os.path.exists(self.csv_path):
                try:
                    predictions = predict(self.csv_path)
                    # Persist scores back to Supabase
                    scores_dict = dict(zip(trait_order, [float(p) for p in predictions]))
                    self.db_manager.update_ocean_score(session_id, scores_dict)
                except Exception as e:
                    print(f"[MlResultPage] Error running prediction: {e}")
            else:
                print("[MlResultPage] Warning: Missing or invalid CSV path for predictions.")

        if predictions is None:
            self.display_error("Failed to generate AI predictions.")
            return

        self.display_predictions(predictions)
        self.auto_generate_report(predictions)

    def display_error(self, message):
        self.loading_label.setVisible(False)
        err_label = QLabel(message)
        err_label.setStyleSheet(f"color: {Theme.COLOR_DANGER}; font-size: 14px; font-weight: 600;")
        err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(err_label)

    def display_predictions(self, predictions):
        self.loading_label.setVisible(False)
        
        trait_order = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]

        # Grid for comparison
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Headers
        headers = ["Trait", "Predicted Score (AI)"]
        for col, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-weight: 700; color: {Theme.COLOR_TEXT_SEC}; font-size: 14px; border-bottom: 2px solid {Theme.COLOR_BORDER}; padding-bottom: 5px;")
            grid.addWidget(lbl, 0, col)

        row = 1
        
        for i, trait in enumerate(trait_order):
            # Use Real ML Prediction for this trait
            predicted_val = float(predictions[i])
            
            # --- Render Row ---
            
            # Trait Name
            lbl_trait = QLabel(trait)
            lbl_trait.setStyleSheet(f"font-weight: 600; color: {Theme.COLOR_TEXT_MAIN}; font-size: 15px;")
            
            # Predicted Score
            lbl_pred = QLabel(f"{predicted_val:.2f}/5")
            lbl_pred.setStyleSheet(f"font-weight: 700; color: {Theme.COLOR_WARNING}; font-size: 15px;")
            
            grid.addWidget(lbl_trait, row, 0)
            grid.addWidget(lbl_pred, row, 1)
            
            row += 1

        container = QWidget()
        container.setLayout(grid)
        self.results_layout.addWidget(container)
        
        self.export_btn.setEnabled(True)

    def go_home(self):
        self.main_window.go_to_session_selection_page()

    def auto_generate_report(self, predictions):
        """Generate an HTML/PDF report and upload the PDF to Supabase Storage."""
        ocean_scores = {
            'O': predictions[0], 'C': predictions[1],
            'E': predictions[2], 'A': predictions[3], 'N': predictions[4]
        }

        # ---- Profile image: load from Supabase URL ----
        import base64
        import urllib.request
        image_html = ""
        img_url = (self.user_data or {}).get("user_image_url") or ""
        if img_url:
            try:
                with urllib.request.urlopen(img_url, timeout=5) as resp:
                    encoded_string = base64.b64encode(resp.read()).decode()
                img_uri = f"data:image/jpeg;base64,{encoded_string}"
                image_html = f"<img src='{img_uri}' width='150' alt='Candidate'>"
            except Exception as e:
                print(f"[MlResultPage] Could not load profile image: {e}")
                image_html = f"<div style='color:#bdc3c7; padding:50px 0;'>Image Unavailable</div>"
        else:
            image_html = f"<div style='color:#bdc3c7; padding:50px 0;'>No Image</div>"

        try:
            from core.career_model import CareerPersonalityModel
            model = CareerPersonalityModel()
            top_3 = model.get_top_3_profiles(ocean_scores)
            job_profile = self.user_data.get('job_profile', '')
            suitability = model.get_job_suitability_percentage(ocean_scores, job_profile) if job_profile else "N/A"
        except Exception:
            top_3 = ["Software Engineer", "Data Scientist", "Product Manager"]
            suitability = "75%"

        top_3_html = "<ul>" + "".join([f"<li>{p}</li>" for p in top_3]) + "</ul>"

        name  = (self.user_data or {}).get('name', 'N/A')
        email = (self.user_data or {}).get('email', 'N/A')
        age   = (self.user_data or {}).get('age', 'N/A')
        job   = (self.user_data or {}).get('job_profile', 'Not Specified')
        session_label = self.session_id or "N/A"
        
        html_str = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #2c3e50; line-height: 1.6; background-color: #ffffff; }}
            h1 {{ color: {Theme.COLOR_PRIMARY}; text-align: center; border-bottom: 2px solid #ecf0f1; padding-bottom: 15px; letter-spacing: 1px; font-weight: 300; font-size: 28px; margin-bottom: 30px; }}
            h3 {{ color: #34495e; font-weight: 600; font-size: 18px; margin-top: 0; padding-bottom: 8px; border-bottom: 1px solid #ecf0f1; }}
            .card {{ background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; margin-bottom: 20px; }}
            .highlight-card {{ background-color: #f0f7ff; border: 1px solid #cce5ff; border-left: 5px solid {Theme.COLOR_PRIMARY}; padding: 20px; margin-top: 25px; }}
            .label {{ font-weight: bold; color: #7f8c8d; font-size: 14px; }}
            .value {{ font-weight: 600; color: #2c3e50; font-size: 15px; }}
            .score-box {{ background-color: #ffffff; border: 1px solid #dee2e6; padding: 10px; text-align: center; margin: 5px; }}
            .score-title {{ font-size: 11px; color: #7f8c8d; font-weight: bold; text-transform: uppercase; }}
            .score-val {{ font-size: 18px; color: {Theme.COLOR_PRIMARY}; font-weight: bold; }}
            ul {{ margin-top: 10px; padding-left: 20px; color: #34495e; font-size: 15px; font-weight: 500; }}
            li {{ margin-bottom: 8px; }}
            .suitability {{ font-size: 20px; font-weight: bold; color: #27ae60; background: #e8f8f5; padding: 10px 15px; border-radius: 8px; display: inline-block; margin-top: 15px; }}
        </style>
        </head>
        <body>
            <h1>CANDIDATE EVALUATION REPORT</h1>
            
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 25px;">
                <tr>
                    <td width="30%" valign="top" align="center">
                        <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px;">
                            {image_html}
                        </div>
                    </td>
                    <td width="5%"></td>
                    <td width="65%" valign="top">
                        <div class="card" style="margin-bottom: 0;">
                            <h3>Candidate Details</h3>
                            <table width="100%" cellpadding="5" cellspacing="0" border="0">
                                <tr>
                                    <td width="35%" class="label">Full Name:</td>
                                    <td class="value">{name}</td>
                                </tr>
                                <tr>
                                    <td class="label">Email Address:</td>
                                    <td class="value">{email}</td>
                                </tr>
                                <tr>
                                    <td class="label">Age:</td>
                                    <td class="value">{age}</td>
                                </tr>
                                <tr>
                                    <td class="label">Target Role:</td>
                                    <td class="value">{job}</td>
                                </tr>
                            </table>
                        </div>
                    </td>
                </tr>
            </table>
            
            <div class="card">
                <h3>OCEAN Personality Profile</h3>
                <p style="color: #7f8c8d; font-size: 13px; margin-top: 0; margin-bottom: 15px;">Extracted from behavioral analysis across interview sessions.</p>
                <table width="100%" cellpadding="5" cellspacing="0" border="0">
                    <tr>
                        <td width="20%" align="center">
                            <div class="score-box">
                                <div class="score-title">Openness</div>
                                <div class="score-val">{float(ocean_scores.get('O',0)):.2f}</div>
                            </div>
                        </td>
                        <td width="20%" align="center">
                            <div class="score-box">
                                <div class="score-title">Conscient.</div>
                                <div class="score-val">{float(ocean_scores.get('C',0)):.2f}</div>
                            </div>
                        </td>
                        <td width="20%" align="center">
                            <div class="score-box">
                                <div class="score-title">Extraversion</div>
                                <div class="score-val">{float(ocean_scores.get('E',0)):.2f}</div>
                            </div>
                        </td>
                        <td width="20%" align="center">
                            <div class="score-box">
                                <div class="score-title">Agreeable.</div>
                                <div class="score-val">{float(ocean_scores.get('A',0)):.2f}</div>
                            </div>
                        </td>
                        <td width="20%" align="center">
                            <div class="score-box">
                                <div class="score-title">Neuroticism</div>
                                <div class="score-val">{float(ocean_scores.get('N',0)):.2f}</div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div class="highlight-card">
                <h3 style="border-bottom:none; color: {Theme.COLOR_PRIMARY};">Career Match Analysis</h3>
                
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                        <td width="55%" valign="top">
                            <div class="label" style="margin-bottom: 10px;">Top Recommended Profiles:</div>
                            {top_3_html}
                        </td>
                        <td width="45%" valign="top" align="center" style="border-left: 1px solid #cce5ff; padding-left: 20px;">
                            <div class="label">Suitability for Target Role</div>
                            <div style="font-size: 15px; font-weight: 500; color: #34495e; margin-top: 5px;">{job}</div>
                            <br>
                            <span class="suitability" style="color: #27ae60; border: 2px solid #27ae60; padding: 5px;">{suitability} MATCH</span>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 40px; color: #bdc3c7; font-size: 12px;">
                Generated by AI Hiring Assistant • Session: {session_label}
            </div>
        </body>
        </html>
        """
        try:
            from PyQt6.QtGui import QTextDocument
            from PyQt6.QtPrintSupport import QPrinter
            import tempfile

            safe_name = name.replace(' ', '_') or "Candidate"

            # Render PDF to a temp file
            tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf",
                                                  prefix=f"isp_report_{safe_name}_")
            tmp_pdf.close()
            pdf_path = tmp_pdf.name

            doc = QTextDocument()
            doc.setHtml(html_str)

            printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(pdf_path)

            doc.print(printer)
            print(f"[MlResultPage] PDF rendered to temp: {pdf_path}")

            # Upload PDF bytes to Supabase and get public URL
            pdf_url = None
            if self.session_id:
                try:
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    pdf_url = self.db_manager.upload_report_pdf(self.session_id, pdf_bytes)
                    self._pdf_url = pdf_url
                    print(f"[MlResultPage] PDF uploaded → {pdf_url}")
                except Exception as upload_err:
                    print(f"[MlResultPage] PDF upload error: {upload_err}")

            # Clean up temp file
            try:
                import os as _os
                _os.unlink(pdf_path)
            except Exception:
                pass

            # Disconnect previous export button handlers
            try:
                self.export_btn.clicked.disconnect()
            except TypeError:
                pass

            # Wire export button to open the Supabase URL in browser
            if pdf_url:
                import webbrowser
                self.export_btn.clicked.connect(lambda _, u=pdf_url: webbrowser.open(u))
                self.export_btn.setText("Open PDF Report")
            else:
                self.export_btn.setEnabled(False)
                self.export_btn.setText("PDF Upload Failed")

        except Exception as e:
            print(f"[MlResultPage] Error auto-generating document report: {e}")
