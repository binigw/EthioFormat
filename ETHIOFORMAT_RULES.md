# ETHIOFORMAT RULEBOOK & ARCHITECTURAL SPECIFICATION
**File:** `ETHIOFORMAT_RULES.md`  
**Project:** EthioFormat — Automated Ethiopian Thesis Formatting SaaS  
**Version:** 2.0.0 (CBE Direct Transfer & Gmail IMAP Automation Architecture)  
**Status:** Permanent Definitive Rulebook  

---

## 1. Executive Overview & Core Principle

**EthioFormat** is an automated SaaS platform engineered to format Ethiopian academic thesis and dissertation documents (`.docx`) strictly following university guidelines and institutional publishing standards.

### Core Principle
> **"Zero User Error, Strict Free Preview Paywall & Automated CBE Direct Bank Verification"**  
> Formatting an academic document must be seamless, robust, and completely protected against user configuration error. Formatting rules must never be typed manually. Output files are protected behind a high-fidelity 3-page preview paywall verified by an automated **CBE Direct Transfer + FastAPI IMAP Gmail receipt verification engine** before releasing full documents.

---

## 2. Tech Stack & Architecture

- **Frontend:** Next.js (React), TypeScript, Tailwind CSS, shadcn/ui component library, Lucide React icons.
- **Backend:** Python FastAPI, `python-docx` for document manipulation, `PyMuPDF` (fitz) / `pdf2image` for page rendering & dynamic page count calculation, `reportlab` for layout engine.
- **Email Receipt Verification Engine:** Python `imaplib` + `email` background worker polling Gmail (`imap.gmail.com:993`) for official Commercial Bank of Ethiopia (CBE) transfer confirmation emails, paired with high-precision Regex parsing.
- **Storage & Database:** Supabase PostgreSQL (`transactions` table) and Supabase Storage (secured buckets with 24-hour temporary retention policy and expiring signed temporary URLs).
- **Payment Method:** Commercial Bank of Ethiopia (CBE) Direct Account Transfer / CBE Birr / Mobile Banking.

---

## 3. Strict System Constraints (The 5 Golden Rules)

Every component, route, script, and feature created in this project must strictly comply with the following 5 Golden Rules:

### Rule 1: Zero Fake Code / Zero Mocks
- **No dummy endpoints, mocked responses, or simulated logic.**
- Every backend endpoint (`/api/preview`, `/api/initiate-cbe-payment`, `/api/payment/submit-cbe-txn`, `/api/payment/status/{session_id}`, IMAP worker) must be 100% functional and execute real processing.
- The formatting engine must parse actual `.docx` files, transform styles, re-calculate layout, generate real preview images, and upload verified artifacts to storage.

### Rule 2: Zero User Input Errors (Dropdown Only UI)
- Users **MUST NOT** type formatting parameters (e.g., margins in inches, font names, line spacing values) manually.
- All configuration is strictly handled via structured **Dropdown Menus ONLY**.
- Primary Mode: University Presets Dropdown (22 Ethiopian Universities + Custom Setup fallback).
- Secondary Mode (Custom Setup): Secondary Dropdown controls with locked, pre-validated options.

### Rule 3: Dynamic Page Calculation & Pricing Engine
- The backend engine (`python-docx` + `PyMuPDF`) must dynamically calculate the total formatted page count of the entire document before returning the preview payload.
- Pricing must be calculated dynamically based on total formatted pages:
  - **Base Fee:** For documents up to 20 pages = **50.00 ETB** flat.
  - **Incremental Fee:** For pages exceeding 20 pages = **+1.50 ETB / additional page**.
  - **Formula:** Total Fee (ETB) = 50 if P <= 20 else 50 + ((P - 20) * 1.50)
- The exact computed page count and ETB pricing must be included in the preview response payload and displayed dynamically on the frontend.

### Rule 4: Secure 3-Page Free Preview Paywall
- The `/api/preview` endpoint MUST return **ONLY the first 3 pages** (Cover Page, Approval/Signature Page, Table of Contents) as high-resolution base64 images or a 3-page PDF stream.
- **SECURITY INVARIANT:** The full formatted `.docx` file or full PDF must **NEVER** be sent, exposed, or leaked to the client browser prior to verified payment.
- The frontend modal displays Pages 1 to 3 in a document viewer, followed by a blurred paywall overlay indicating the remaining locked pages and payment CTA.

### Rule 5: Automated CBE Direct Transfer & Gmail IMAP Verification
- When a user initiates checkout, the system provides official CBE Account Details and the exact dynamically calculated amount.
- The user transfers via CBE Mobile Banking / CBE Birr and submits their CBE Transaction Reference ID (FT/TXN number) on the frontend.
- A FastAPI background worker running `imaplib` connects to Gmail, scans incoming CBE credit alerts, extracts the `Txn ID` and `Amount` using Regex, and verifies that `amount_paid >= amount_expected`.
- Upon verification, the `transactions` record in Supabase is updated to `'approved'`, the document is uploaded to Supabase Storage, and a secure **24-hour signed download URL** is generated and delivered to the user.

---

## 4. University Presets & Formatting Specifications

### 4.1 Mode A: University Presets (Primary & Default)
Selecting any Ethiopian University preset automatically enforces the **Standard Ethiopian Thesis Formatting Profile**:
- **Font Family:** Times New Roman
- **Font Size:** 12 pt for body text; 14 pt Bold for Chapter Headings (Heading 1); 12 pt Bold for Subheadings (Heading 2 & 3)
- **Line Spacing:** 1.5 Lines
- **Paragraph Spacing:** 0 pt before, 6 pt after (or 0 pt before / 0 pt after with 0.5" first-line indent)
- **Margins:** 
  - Left / Binding Margin: **1.5 inches (3.81 cm)**
  - Top Margin: **1.0 inch (2.54 cm)**
  - Right Margin: **1.0 inch (2.54 cm)**
  - Bottom Margin: **1.0 inch (2.54 cm)**
- **Alignment:** Justified body text
- **Page Numbering:** Roman numerals (`i, ii, iii...`) for preliminary pages (Approval, Abstract, TOC, Lists); Arabic numerals (`1, 2, 3...`) starting from Chapter 1.
- **TOC:** Automated generation and heading level synchronization.

#### Supported University Presets (Exact 23 Options)
1. `Addis Ababa University (አዲስ አበባ ዩኒቨርሲቲ)`
2. `Jimma University (ጅማ ዩኒቨርሲቲ)`
3. `Hawassa University (ሐዋሳ ዩኒቨርሲቲ)`
4. `Bahir Dar University (ባሕር ዳር ዩኒቨርሲቲ)`
5. `University of Gondar (ጎንደር ዩኒቨርሲቲ)`
6. `Arba Minch University (አርባ ምንጭ ዩኒቨርሲቲ)`
7. `Haramaya University (ሀረማያ ዩኒቨርሲቲ)`
8. `Adama Science and Technology University - ASTU (አዳማ ሳይንስና ቴክኖሎጂ)`
9. `Addis Ababa Science and Technology University - AASTU (አዲስ አበባ ሳይንስና ቴክኖሎጂ)`
10. `Mekelle University (መቀሌ ዩኒቨርሲቲ)`
11. `Dilla University (ዲላ ዩኒቨርሲቲ)`
12. `Debre Markos University (ደብረ ማርቆስ ዩኒቨርሲቲ)`
13. `Debre Birhan University (ደብረ ብርሃን ዩኒቨርሲቲ)`
14. `Wollo University (ወሎ ዩኒቨርሲቲ)`
15. `Dire Dawa University (ድሬዳዋ ዩኒቨርሲቲ)`
16. `Jigjiga University (ጅግጅጋ ዩኒቨርሲቲ)`
17. `Wollega University (ወለጋ ዩኒቨርሲቲ)`
18. `Ambo University (አምቦ ዩኒቨርሲቲ)`
19. `Mettu University (መቱ ዩኒቨርሲቲ)`
20. `Gambella University (ጋምቤላ ዩኒቨርሲቲ)`
21. `St. Mary's University (ቅድስት ማርያም ዩኒቨርሲቲ)`
22. `Unity University (ዩኒቲ ዩኒቨርሲቲ)`
23. `Custom Setup (የተለየ ህግ ለመምረጥ)` -> *Unlocks Mode B*

---

## 5. End-to-End System Architecture

```
[ User Browser (Next.js) ]
       |
       |  1. Upload .docx + Dropdown Selections (JSON)
       v
[ FastAPI Backend (/api/preview) ]
       |
       |  2. python-docx: Full document restructuring & style normalization
       |  3. PyMuPDF / Conversion Engine: Calculate total pages & render Pages 1-3
       |  4. Store full formatted file in secure staging area (Session Cache)
       |
       v  5. Return { session_id, preview_pages: [p1, p2, p3], total_pages, calculated_price }
[ Frontend Preview Modal ]
       |
       |  6. Renders Pages 1-3 + Blurred Paywall Overlay for remaining (N-3) pages
       |  7. User clicks "Pay [Price] ETB via CBE Birr / Bank Transfer"
       |  8. User transfers money via CBE Mobile Banking / CBE Birr to Account 1000123456789
       |  9. User submits their CBE Transaction ID (e.g. FT260987ABCD) -> /api/payment/submit-cbe-txn
       v
[ FastAPI IMAP Background Worker / Webhook Receiver ]
       |
       | 10. imaplib polls Gmail for CBE receipt email -> extracts Txn ID and Amount via Regex
       | 11. Matches Txn ID with pending record in Supabase transactions table
       | 12. Validates amount_paid >= amount_expected
       | 13. Marks session as 'approved', uploads document to Supabase Storage Bucket & generates 24h Signed URL
       v
[ Frontend Live Polling / Realtime ]
       |
       | 14. Frontend detects 'approved' status and unlocks "Download Formatted Thesis (.docx)"
```

---

## 6. Detailed API Contracts

### 6.1 `POST /api/preview`
- **Content-Type:** `multipart/form-data`
- **Request Fields:** `file` (.docx), `preset_id`, `custom_rules` (optional).
- **Response Payload:** Returns `session_id`, `total_pages`, `preview_pages` (pages 1-3), `pricing` (base + incremental), `metadata`.

### 6.2 `POST /api/initiate-cbe-payment`
- **Content-Type:** `application/json`
- **Request Payload:** `{ "session_id": "sess_..." }`
- **Response Payload:** Returns `session_id`, `amount_expected`, `cbe_account_number`, `cbe_account_name`, `instructions`.

### 6.3 `POST /api/payment/submit-cbe-txn`
- **Content-Type:** `application/json`
- **Request Payload:** `{ "session_id": "sess_...", "transaction_ref": "FT2609871234", "payer_name": "Abebe Bikila" }`

### 6.4 `GET /api/payment/status/{session_id}`
- **Response Payload:** Returns `status` ('pending' | 'approved' | 'failed'), `verified`, `download_url`, `file_name`.

---

## 7. Security & Anti-Leak Policy

1. **File Sandboxing:** Formatted documents in the preview stage are stored in an isolated temporary staging directory indexed by cryptographic session IDs.
2. **Preview Image Isolation:** PyMuPDF extracts only indices `[0, 1, 2]`. No higher page indices are ever converted or transmitted during preview.
3. **Download URL Protection:** Direct download URLs are strictly generated using Supabase Storage time-restricted Signed URLs (24-hour TTL) only after successful CBE transaction validation matching the expected amount.
4. **No Plaintext Parameter Injection:** Dropdown selections are validated against an Enum schema in FastAPI Pydantic models.
