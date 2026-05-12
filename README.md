# AI-Based Hiring Assistant (Thermal Facial Imaging)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green?style=for-the-badge&logo=qt)
![Supabase](https://img.shields.io/badge/Supabase-Database-1CA28B?style=for-the-badge&logo=supabase)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-white?style=for-the-badge&logo=opencv)
![PyTorch](https://img.shields.io/badge/PyTorch-Machine%20Learning-EE4C2C?style=for-the-badge&logo=pytorch)

A cutting-edge desktop application system built with PyQt6 that modernizes the recruitment process. This tool uses **Computer Vision**, **Machine Learning**, and **Thermal Facial Analysis** to evaluate candidates remotely and assist interviewers in making data-driven decisions.

## Key Features

- **Dual-Application Architecture**: Separate, secure interfaces for both Candidates (`interviewee_side`) and Recruiters (`interviewer_side`).
- **Real-Time Face Alignment & Tracking**: Uses MediaPipe and OpenCV to ensure candidates are properly positioned.
- **Thermal Imaging & ML Analysis**: Extracts thermal features and runs predictive models (Scikit-Learn/PyTorch) to estimate **OCEAN** personality scores.
- **Cloud Database Integration**: Seamless synchronization using **Supabase** (PostgreSQL) and Supabase Object Storage for video/image assets.
- **Automated PDF Reports**: Generates comprehensive, exportable evaluation reports for interviewers.
- **Stunning Glassmorphism UI**: A premium, modern, and highly responsive user interface.

## Project Architecture

```text
├── interviewee_side/   # Candidate application (Registration, Camera, Recording)
├── interviewer_side/   # Recruiter application (Session review, ML Analysis, PDF Generation)
├── shared/             # Shared logic (Supabase database manager)
├── schema.sql          # Supabase Database schema blueprint
├── requirements.txt    # Python dependencies
└── .env.template       # Environment variables template
```

## Getting Started

### 1. Prerequisites
- Python 3.9 or higher
- A [Supabase](https://supabase.com/) account (Free tier works perfectly)

### 2. Database Setup (Supabase)
1. Create a new Supabase project.
2. Go to the **SQL Editor** in your Supabase dashboard and run the code provided in `schema.sql`.
3. Go to **Storage** and create a **private** bucket named exactly `interview-assets`.

### 3. Installation
Clone the repository and install the required dependencies:

```bash
git clone https://github.com/mohdfaiz247/AI-based-hiring-Assistant-using-thermal-facial-image.git
cd AI-based-hiring-Assistant-using-thermal-facial-image
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory based on the `.env.template` file. Add your Supabase keys:

```env
SUPABASE_URL=https://your-project-url.supabase.co
SUPABASE_KEY=your_anon_or_service_role_key
```

### 5. Running the Application

**To run the Candidate Application:**
```bash
cd interviewee_side
python main.py
```

**To run the Recruiter Application:**
```bash
cd interviewer_side/AIHiringAssistant
python main.py
```

## 🛠️ Technology Stack
- **Frontend/GUI:** PyQt6
- **Backend/DB:** Supabase (PostgreSQL + Object Storage)
- **Computer Vision:** OpenCV, MediaPipe
- **Machine Learning:** PyTorch, Scikit-Learn, Joblib
- **Data Handling:** NumPy, Pillow
