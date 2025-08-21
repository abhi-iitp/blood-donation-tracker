# Blood Donation Tracker System

A simple Flask + SQLite app to track donors, donations, and blood stock with low-stock alerts, charts, CSV export, and a PDF report.

## ✨ Features
- Donor data collection (name, blood group, last donation)
- Track stock units per blood group
- Log donations (increments stock + updates donor's last donation)
- Log usage/issue (decrements stock)
- Low-stock alert thresholds per blood group
- Dashboard with Chart.js bar chart by blood type
- Export donor list as CSV
- Download availability chart as PNG
- Generate PDF blood bank status report

## 🧰 Tech Stack
- Python 3.10+
- Flask, Flask_SQLAlchemy
- SQLite (file-based)
- Chart.js (CDN)
- ReportLab (for PDF report)

## 📦 Project Structure
```
blood-donation-tracker/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ templates/
│  ├─ base.html
│  ├─ dashboard.html
│  ├─ donors.html
│  ├─ donate.html
│  ├─ use.html
│  └─ report.html
└─ static/
   ├─ css/styles.css
   └─ img/
```

## 🚀 How to Run Locally
```bash
# 1) Create & activate a virtual environment (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Initialize the database with sample data
python app.py --initdb

# 4) Run the server
python app.py
# App will start on http://127.0.0.1:5000/
```

> Tip: Change `DEBUG=True` in `app.py` if you don't want auto-reload.

## 🧪 Sample Data Included
- Donors:
  - Rahul (A+) — last donation: 2025-06-25
  - Sneha (O-) — last donation: 2025-07-01
- One sample donation for Rahul on 2025-07-01 (1 unit), stock updated accordingly.

## 🧾 PDF Report
Visit **/report/pdf** to download a generated PDF with stock summary and low-stock alerts.

## 📤 Export
- **Donor CSV:** `/export/donors.csv`
- **Chart PNG:** Use the "Download Chart" button on the dashboard to save the availability chart.

## 🐙 Push to GitHub (Quick Guide)
```bash
# From the project root
git init
git add .
git commit -m "Blood Donation Tracker: initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/blood-donation-tracker.git
git push -u origin main
```

## 📝 Notes
- Thresholds default to 5 per group (editable in DB seed or via script).
- You can add more donors and donations from the UI.
- For a full PDF with logos/branding, tweak the ReportLab code in `app.py`.

## 📄 License
MIT
