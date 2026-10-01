import os
import subprocess
import base64
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any
import pymupdf
from app.services.pricing_engine import PricingEngine
from app.models.formatting import PricingDetailModel

class DocumentConverterService:
    def __init__(self):
        self.libreoffice_bin = self._find_libreoffice()

    def _find_libreoffice(self) -> str:
        candidates = ["libreoffice", "soffice", "/usr/bin/libreoffice", "/usr/bin/soffice"]
        for cand in candidates:
            if shutil.which(cand):
                return cand
        return "libreoffice"

    def convert_docx_to_pdf(self, docx_path: str, output_dir: str) -> str:
        """
        Converts a .docx document to .pdf using headless LibreOffice.
        Returns the path to the generated .pdf file.
        """
        docx_path_obj = Path(docx_path)
        output_dir_obj = Path(output_dir)
        output_dir_obj.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.libreoffice_bin,
            "--headless",
            "--invisible",
            "--nodefault",
            "--nofirststartwizard",
            "--nolockcheck",
            "--nologo",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir_obj.resolve()),
            str(docx_path_obj.resolve())
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed (code {result.returncode}): {result.stderr}")

        expected_pdf_name = f"{docx_path_obj.stem}.pdf"
        pdf_path = output_dir_obj / expected_pdf_name
        
        if not pdf_path.exists():
            # Check if any pdf was generated in the output directory
            pdf_files = list(output_dir_obj.glob("*.pdf"))
            if pdf_files:
                pdf_path = pdf_files[0]
            else:
                raise FileNotFoundError(f"Converted PDF not found at {pdf_path}")

        return str(pdf_path.resolve())

    def generate_previews_and_page_count(self, pdf_path: str, max_preview_pages: int = 3) -> Tuple[int, List[str]]:
        """
        Inspects the PDF using PyMuPDF:
        1. Dynamically calculates total page count.
        2. Renders ONLY the first `max_preview_pages` (Pages 1, 2, 3) as high-res base64 PNG images.
        3. Strictly DOES NOT expose or extract pages beyond index (max_preview_pages - 1).
        """
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        
        if total_pages == 0:
            doc.close()
            raise ValueError("The generated document has 0 pages.")

        preview_images_base64: List[str] = []
        pages_to_render = min(max_preview_pages, total_pages)

        # 2x scale matrix for 144-150 DPI crisp rendering
        matrix = pymupdf.Matrix(2.0, 2.0)

        for page_idx in range(pages_to_render):
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            png_bytes = pix.tobytes(output="png")
            b64_str = base64.b64encode(png_bytes).decode("utf-8")
            data_url = f"data:image/png;base64,{b64_str}"
            preview_images_base64.append(data_url)

        doc.close()
        return total_pages, preview_images_base64

    def process_document_pipeline(self, formatted_docx_path: str, work_dir: str) -> Dict[str, Any]:
        """
        Full pipeline:
        1. DOCX -> PDF conversion
        2. Page count & 3-page base64 preview rendering
        3. Dynamic pricing calculation
        """
        pdf_path = self.convert_docx_to_pdf(formatted_docx_path, work_dir)
        total_pages, preview_pages = self.generate_previews_and_page_count(pdf_path, max_preview_pages=3)
        pricing = PricingEngine.calculate_pricing(total_pages)

        return {
            "total_pages": total_pages,
            "preview_pages": preview_pages,
            "pricing": pricing,
            "pdf_path": pdf_path
        }

converter_service = DocumentConverterService()
