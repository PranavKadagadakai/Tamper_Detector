# 🛡️ Tamper Detector - ID Image Forensics System

This web-based application allows users to upload ID documents and detect potential tampering using various forensic techniques including EXIF analysis, ELA, noise, and text consistency.

## 🧩 Features

- 🔐 User authentication via JWT
- 🖼️ Upload and analyze JPEG/PNG images
- 📜 Full detection report including:
  - Metadata
  - Error Level Analysis
  - Noise & edge inconsistencies
  - Copy-move forgery
- 📊 View detection history (for logged-in users)

## 🖥️ Tech Stack

- **Frontend:** React + Vite + Bootstrap 5
- **Backend:** Django REST Framework + JWT
- **Forensics:** OpenCV, EXIFRead, Tesseract, PIL, scikit-image

## 🚀 Setup

### Backend

```bash
cd Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

### Environment Variables

Create .env in Frontend/

```ini
VITE_BACKEND_URL=http://localhost:8000
```

### 🏁 Deployment Notes

Backend: Host on Render/EC2/Elastic Beanstalk

Frontend: Vercel or Netlify

CORS: Ensure allowed origins set in settings.py

### 🧠 Credits

## Developed by Pranav Kadagadakai | CSE | 2025
