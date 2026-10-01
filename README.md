# EthioFormat (ኢትዮ-ፎርማት) 🎓🇪🇹

> **Automated Academic Thesis & Dissertation Formatting SaaS for Ethiopian Universities**

EthioFormat is a full-stack automated document formatting platform engineered to format Ethiopian academic thesis and dissertation documents (`.docx`) strictly following university guidelines and institutional publishing standards.

---

## 🌟 Key Features

- **22 Ethiopian University Presets:** One-click automated formatting adhering to guidelines for AAU, Jimma University, Hawassa University, Bahir Dar University, Gondar University, Haramaya, ASTU, AASTU, Mekelle, and 13+ others.
- **Mode B Custom Setup:** Dropdown-only fine-grained customization (Font Family, Font Size, Line Spacing, Ethiopian standard binding margins, and Auto-TOC).
- **Dynamic Page Calculation Engine:** `python-docx` + `PyMuPDF` rendering pipeline dynamically calculates page count and fair student pricing (50 ETB base up to 20 pages + 1.50 ETB / extra page).
- **Secure 3-Page Free Preview Paywall:** High-resolution rendering for Page 1 (Cover Page), Page 2 (Approval Sheet), and Page 3 (Table of Contents) with frosted blur paywall overlay.
- **Chapa Payment & Supabase Storage Integration:** Direct Telebirr, CBEBirr, and Card payment verification with 24-hour signed download access.

---

## 🛠️ Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Radix UI (shadcn/ui), Lucide Icons, Canvas Confetti.
- **Backend:** Python FastAPI, `python-docx`, `PyMuPDF`, `pdf2image`, Headless LibreOffice.
- **Storage:** Supabase Storage (`ethioformat-documents` bucket).
- **Payment Gateway:** Chapa API (Telebirr, CBEBirr, Cards).

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Node.js 18+ & npm
- Python 3.10+
- LibreOffice (for headless DOCX to PDF conversion)

### 2. Environment Variables (.env)
Create a `.env` file in the root directory:
```ini
# Chapa API Keys
CHAPA_SECRET_KEY=your_chapa_secret_key
CHAPA_PUBLIC_KEY=your_chapa_public_key
CHAPA_API_URL=https://api.chapa.co/v1

# Supabase Storage Integration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_secret_key
SUPABASE_BUCKET_NAME=ethioformat-documents

# Pricing Parameters (ETB)
BASE_PAGE_THRESHOLD=20
BASE_FEE_ETB=50.0
INCREMENTAL_PER_PAGE_FEE_ETB=1.50
```

### 3. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

---

## 📜 License
MIT License. Built for Ethiopian researchers and students.
