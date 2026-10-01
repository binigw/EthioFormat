# ETHIOFORMAT RULEBOOK & ARCHITECTURAL SPECIFICATION
**File:** `ETHIOFORMAT_RULES.md`  
**Project:** EthioFormat — Automated Ethiopian Thesis Formatting SaaS  
**Version:** 1.0.0 (Production Blueprint)  
**Status:** Permanent Definitive Rulebook  

---

## 1. Executive Overview & Core Principle

**EthioFormat** is an automated SaaS platform engineered to format Ethiopian academic thesis and dissertation documents (`.docx`) strictly following university guidelines and institutional publishing standards.

### Core Principle
> **"Zero User Error & Strict Free Preview Paywall"**  
> Formatting an academic document must be seamless, robust, and completely protected against user configuration error. Formatting rules must never be typed manually. Output files are protected behind a high-fidelity 3-page preview paywall verified by Chapa payments before releasing full documents.

---

## 2. Tech Stack & Architecture

- **Frontend:** Next.js (React), TypeScript, Tailwind CSS, shadcn/ui component library, Lucide React icons.
- **Backend:** Python FastAPI, `python-docx` for document manipulation, `PyMuPDF` (fitz) / `pdf2image` for page rendering & dynamic page count calculation.
- **Document Conversion Engine:** Headless document rendering pipeline for high-fidelity DOCX-to-PDF rendering and page image extraction.
- **Storage:** Supabase Storage (secured buckets with 24-hour temporary retention policy and signed temporary URLs).
- **Payment Gateway:** Chapa API (Ethiopian Payment Gateway supporting Telebirr, CBEBirr, Cards, and local mobile money).

---

## 3. Strict System Constraints (The 5 Golden Rules)

Every component, route, script, and feature created in this project must strictly comply with the following 5 Golden Rules:

### Rule 1: Zero Fake Code / Zero Mocks
- **No dummy endpoints, mocked responses, or simulated logic.**
- Every backend endpoint (`/api/preview`, `/api/initiate-payment`, `/api/verify-payment`, formatting worker) must be 100% functional and execute real processing.
- The formatting engine must parse actual `.docx` files, transform styles, re-calculate layout, generate real preview images, and upload verified artifacts to storage.

### Rule 2: Zero User Input Errors (Dropdown Only UI)
- Users **MUST NOT** type formatting parameters (e.g., margins in inches, font names, line spacing values) manually.
- All configuration is strictly handled via structured **Dropdown Menus ONLY**.
- Primary Mode: University Presets Dropdown (22 Ethiopian Universities + Custom Setup fallback).
- Secondary Mode (Custom Setup): Secondary Dropdown controls with locked, pre-validated options.

### Rule 3: Dynamic Page Calculation & Pricing Engine
- The backend engine (`python-docx` + `PyMuPDF`) must dynamically calculate the total formatted page count of the entire document before returning the preview payload.
- Pricing must be calculated dynamically based on total formatted pages:
  - **Base Fee:** For documents up to 20 pages (e.g., 50 ETB base fee).
  - **Incremental Fee:** Configurable per-page increment for pages exceeding 20 pages (e.g., +1.50 ETB / additional page).
- The exact computed page count and ETB pricing must be included in the preview response payload and displayed dynamically on the frontend.

### Rule 4: Secure 3-Page Free Preview Paywall
- The `/api/preview` endpoint MUST return **ONLY the first 3 pages** (Cover Page, Approval/Signature Page, Table of Contents) as high-resolution base64 images or a 3-page PDF stream.
- **SECURITY INVARIANT:** The full formatted `.docx` file or full PDF must **NEVER** be sent, exposed, or leaked to the client browser prior to verified payment.
- The frontend modal displays Pages 1 to 3 in a document viewer, followed by a blurred paywall overlay indicating the remaining locked pages and payment CTA.

### Rule 5: Chapa Payment Verification & Supabase Temporary Storage
- When a user initiates checkout, Chapa payment is generated with a unique transaction reference (`tx_ref`).
- Access to the full `.docx` is granted **ONLY** after verified payment validation through Chapa API (`/api/verify-payment` or verified Webhook).
- Full formatted files are stored securely in Supabase Storage with expiring signed download URLs (24-hour TTL) generated upon successful verification.

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

### 4.2 Mode B: Custom Setup (Secondary Dropdowns Only)
If the user selects `Custom Setup (የተለየ ህግ ለመምረጥ)`, the UI dynamically reveals strict secondary dropdowns with no free text input:

| Parameter | Allowed Dropdown Options | Default |
| :--- | :--- | :--- |
| **Font Family** | `[ "Times New Roman", "Arial" ]` | `Times New Roman` |
| **Font Size** | `[ "12 pt", "11 pt" ]` | `12 pt` |
| **Line Spacing** | `[ "1.5 Lines", "2.0 Lines", "1.0 Line" ]` | `1.5 Lines` |
| **Margins** | `[ "Ethiopian Standard (Left 1.5\", Others 1.0\")", "Equal Margins (1.0\" All Sides)" ]` | `Ethiopian Standard` |
| **Table of Contents** | `[ "Auto-Generate TOC", "Keep Existing" ]` | `Auto-Generate TOC` |

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
       |  4. Store full formatted file in secure staging area (Session Cache / Supabase Private)
       |
       v  5. Return { session_id, preview_pages: [p1, p2, p3], total_pages, calculated_price }
[ Frontend Preview Modal ]
       |
       |  6. Renders Pages 1-3 + Blurred Paywall Overlay for remaining (N-3) pages
       |  7. User clicks "Pay [Price] ETB via Chapa / Telebirr"
       v
[ Chapa Payment Gateway ]
       |
       |  8. Payment completed -> Webhook/Callback with tx_ref
       v
[ FastAPI Backend (/api/verify-payment) ]
       |
       |  9. Verifies tx_ref with Chapa API
       |  10. Moves document to Supabase Storage Bucket & generates 24h Signed URL
       v
[ Frontend Auto-Download ]
       |
       | 11. Initiates browser download of complete formatted .docx
```

---

## 6. Detailed API Contracts

### 6.1 `POST /api/preview`
- **Content-Type:** `multipart/form-data`
- **Request Fields:**
  - `file`: Binary `.docx` file
  - `preset_id`: string (e.g. `addis_ababa_university` or `custom`)
  - `custom_rules`: JSON string (optional, required if `preset_id == 'custom'`)
    ```json
    {
      "font_family": "Times New Roman",
      "font_size": 12,
      "line_spacing": 1.5,
      "margin_preset": "ethiopian_standard",
      "toc_mode": "auto_generate"
    }
    ```
- **Response Payload (JSON):**
  ```json
  {
    "status": "success",
    "session_id": "sess_9f83a2c418e",
    "total_pages": 84,
    "preview_pages": [
      "data:image/png;base64,iVBORw0KGgoAAAANSU...",
      "data:image/png;base64,iVBORw0KGgoAAAANSU...",
      "data:image/png;base64,iVBORw0KGgoAAAANSU..."
    ],
    "pricing": {
      "base_fee": 50.0,
      "incremental_fee": 96.0,
      "total_fee": 146.0,
      "currency": "ETB"
    },
    "metadata": {
      "filename": "thesis_final_draft.docx",
      "formatted_at": "2026-09-30T10:50:00Z",
      "university": "Addis Ababa University (አዲስ አበባ ዩኒቨርሲቲ)"
    }
  }
  ```

### 6.2 `POST /api/initiate-payment`
- **Content-Type:** `application/json`
- **Request Payload:**
  ```json
  {
    "session_id": "sess_9f83a2c418e",
    "email": "student@aau.edu.et",
    "first_name": "Abebe",
    "last_name": "Bikila",
    "phone_number": "0911223344"
  }
  ```
- **Response Payload:**
  ```json
  {
    "status": "success",
    "checkout_url": "https://checkout.chapa.co/checkout/payment/...",
    "tx_ref": "ETHIO-FORMAT-sess_9f83a2c418e-1727693400"
  }
  ```

### 6.3 `POST /api/verify-payment`
- **Content-Type:** `application/json`
- **Request Payload:**
  ```json
  {
    "tx_ref": "ETHIO-FORMAT-sess_9f83a2c418e-1727693400",
    "session_id": "sess_9f83a2c418e"
  }
  ```
- **Response Payload:**
  ```json
  {
    "status": "paid",
    "verified": true,
    "download_url": "https://[supabase-project].supabase.co/storage/v1/object/sign/formatted-theses/...",
    "expires_in_hours": 24,
    "file_name": "Formatted_thesis_final_draft.docx"
  }
  ```

---

## 7. Dynamic Pricing Engine Rules

The pricing algorithm enforces fair student pricing based on verified page length:
- **Base Tier:** Up to 20 pages = **50.00 ETB** flat.
- **Extended Tier:** Every page above 20 pages adds **1.50 ETB / page** (rounded to nearest integer).
- **Calculation Formula:**
  $$\text{Total Fee (ETB)} = \begin{cases} 50, & \text{if } P \le 20 \\ 50 + ((P - 20) \times 1.50), & \text{if } P > 20 \end{cases}$$
  *(where $P$ is the total formatted page count computed by PyMuPDF)*.

---

## 8. Frontend Paywall UI/UX Guidelines

1. **Upload & Configuration Card:**
   - Drag-and-drop `.docx` file uploader with file validation.
   - Primary University Preset Dropdown with all 23 options clearly labeled in English and Amharic.
   - Conditional rendering for Mode B Custom Dropdowns.
   - "Format Thesis & Preview Free" CTA button with live processing progress state.

2. **Preview Modal Window:**
   - Modal header showing document title, detected total pages, and assigned formatting standard.
   - High-resolution Page Viewer rendering Page 1 (Cover), Page 2 (Approval), Page 3 (TOC).
   - Zoom and page navigation controls for the 3 preview pages.
   - **Paywall Hook Container:**
     - Frosted blur preview visual stack representing pages 4 through $N$.
     - Prominent floating paywall banner:
       > *"To unlock and download the complete formatted document (Total: {total_pages} Pages), pay {total_fee} ETB via Chapa / Telebirr"*.
     - Action button: `[ Pay {total_fee} ETB via Chapa / Telebirr ]`.

3. **Payment & Receipt View:**
   - Seamless checkout redirect or embedded modal.
   - Instant transaction verification polling.
   - Download Card with countdown timer for 24-hour expiration link.

---

## 9. Security & Anti-Leak Policy

1. **File Sandboxing:** Formatted documents in the preview stage are stored in a non-public temporary directory or protected memory cache indexed by cryptographic session IDs.
2. **Preview Image Isolation:** PyMuPDF extracts only indices `[0, 1, 2]`. No higher page indices are ever converted or transmitted during preview.
3. **Download URL Protection:** Direct download URLs are strictly generated using Supabase Storage time-restricted Signed URLs only after Chapa HTTP 200 verification with matching `tx_ref` and `amount`.
4. **No Plaintext Parameter Injection:** Dropdown selections are validated against an Enum schema in FastAPI Pydantic models; any unknown parameters result in immediate 422 Unprocessable Entity.

---

## 10. Developer & Agent Compliance Directive

For every upcoming phase, component, backend route, and utility:
- You **MUST** strictly adhere to `ETHIOFORMAT_RULES.md`.
- Never substitute functional code with mock timeouts or placeholder dictionaries.
- Always implement complete, robust, error-handled production logic.
