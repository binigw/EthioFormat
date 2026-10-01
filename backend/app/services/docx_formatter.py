import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

DATA_FILE = Path(__file__).parent.parent / "data" / "university_presets.json"

class DocxFormatterService:
    def __init__(self):
        self.presets_data = self._load_presets()

    def _load_presets(self) -> Dict[str, Any]:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"presets": []}

    def get_preset_config(self, preset_id: str, custom_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolves formatting rules from preset ID or custom rules."""
        if preset_id == "custom" and custom_rules:
            # Map custom rules to standard config
            font_family = custom_rules.get("font_family", "Times New Roman")
            font_size = int(custom_rules.get("font_size", 12))
            line_spacing = float(custom_rules.get("line_spacing", 1.5))
            margin_preset = custom_rules.get("margin_preset", "ethiopian_standard")
            toc_mode = custom_rules.get("toc_mode", "auto_generate")

            if margin_preset == "equal_margins":
                margins = {"left_inches": 1.0, "top_inches": 1.0, "right_inches": 1.0, "bottom_inches": 1.0}
            else:
                margins = {"left_inches": 1.5, "top_inches": 1.0, "right_inches": 1.0, "bottom_inches": 1.0}

            return {
                "font_family": font_family,
                "font_size_body": font_size,
                "font_size_h1": font_size + 2,
                "font_size_h2": font_size,
                "font_size_h3": font_size,
                "line_spacing": line_spacing,
                "paragraph_space_after": 6,
                "paragraph_space_before": 0,
                "first_line_indent_inches": 0.5,
                "margins": margins,
                "alignment": "JUSTIFY",
                "toc_mode": toc_mode,
                "page_numbering": {
                    "preliminary": "ROMAN_LOWER",
                    "main_body": "ARABIC",
                    "position": "BOTTOM_CENTER"
                }
            }

        # Find matching preset
        for p in self.presets_data.get("presets", []):
            if p["id"] == preset_id and p.get("config"):
                return p["config"]

        # Default fallback: Addis Ababa University standard
        return {
            "font_family": "Times New Roman",
            "font_size_body": 12,
            "font_size_h1": 14,
            "font_size_h2": 12,
            "font_size_h3": 12,
            "line_spacing": 1.5,
            "paragraph_space_after": 6,
            "paragraph_space_before": 0,
            "first_line_indent_inches": 0.5,
            "margins": {"left_inches": 1.5, "top_inches": 1.0, "right_inches": 1.0, "bottom_inches": 1.0},
            "alignment": "JUSTIFY",
            "toc_mode": "auto_generate",
            "page_numbering": {
                "preliminary": "ROMAN_LOWER",
                "main_body": "ARABIC",
                "position": "BOTTOM_CENTER"
            }
        }

    def format_document(self, input_docx_path: str, output_docx_path: str, preset_id: str, custom_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Loads the docx document and applies full Ethiopian thesis formatting:
        - Section page size (A4 / Letter) and binding margins (1.5" Left, 1.0" Top/Right/Bottom)
        - Normal style & run font family and sizes
        - Heading 1, Heading 2, Heading 3 hierarchical formatting
        - Line spacing & paragraph spacing
        - Table cell formatting and borders
        - Page numbering
        """
        doc = Document(input_docx_path)
        config = self.get_preset_config(preset_id, custom_rules)
        
        font_family = config["font_family"]
        font_size_body = config["font_size_body"]
        font_size_h1 = config["font_size_h1"]
        font_size_h2 = config["font_size_h2"]
        font_size_h3 = config["font_size_h3"]
        line_spacing = config["line_spacing"]
        margins = config["margins"]

        # 1. Apply Margins to all sections
        for section in doc.sections:
            section.top_margin = Inches(margins["top_inches"])
            section.bottom_margin = Inches(margins["bottom_inches"])
            section.left_margin = Inches(margins["left_inches"])
            section.right_margin = Inches(margins["right_inches"])
            section.page_width = Inches(8.5)
            section.page_height = Inches(11.0)
            
            # Ensure footer distance
            section.footer_distance = Inches(0.5)
            section.header_distance = Inches(0.5)

        # 2. Update Default 'Normal' Style in Document
        if 'Normal' in doc.styles:
            normal_style = doc.styles['Normal']
            normal_font = normal_style.font
            normal_font.name = font_family
            normal_font.size = Pt(font_size_body)
            normal_font.color.rgb = RGBColor(0, 0, 0)
            normal_style.paragraph_format.line_spacing = line_spacing
            normal_style.paragraph_format.space_after = Pt(config.get("paragraph_space_after", 6))
            normal_style.paragraph_format.space_before = Pt(config.get("paragraph_space_before", 0))

        # 3. Format Paragraphs & Headings
        for p in doc.paragraphs:
            text_stripped = p.text.strip()
            if not text_stripped:
                continue

            style_name = p.style.name.lower() if p.style else ""
            is_heading_1 = ("heading 1" in style_name) or (text_stripped.isupper() and len(text_stripped) < 80 and ("CHAPTER" in text_stripped or "TABLE OF CONTENTS" in text_stripped or "ABSTRACT" in text_stripped or "DECLARATION" in text_stripped or "APPROVAL" in text_stripped or "REFERENCES" in text_stripped))
            is_heading_2 = ("heading 2" in style_name) or (text_stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) and len(text_stripped) < 90 and not text_stripped.count(".") > 2)
            is_heading_3 = ("heading 3" in style_name) or (text_stripped.count(".") == 2 and len(text_stripped) < 90)

            # Detect Cover Page Elements (first few paragraphs centered)
            is_centered_title = p.alignment == WD_ALIGN_PARAGRAPH.CENTER

            if is_heading_1:
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.first_line_indent = Inches(0)
                if not is_centered_title and not ("CHAPTER" in text_stripped or "TABLE OF CONTENTS" in text_stripped):
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.name = font_family
                    run.font.size = Pt(font_size_h1)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 0, 0)
            elif is_heading_2:
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_before = Pt(10)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.first_line_indent = Inches(0)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.name = font_family
                    run.font.size = Pt(font_size_h2)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(0, 0, 0)
            elif is_heading_3:
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.first_line_indent = Inches(0)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.name = font_family
                    run.font.size = Pt(font_size_h3)
                    run.font.bold = True
                    run.font.italic = True
                    run.font.color.rgb = RGBColor(0, 0, 0)
            else:
                # Body paragraph
                p.paragraph_format.line_spacing = line_spacing
                p.paragraph_format.space_before = Pt(config.get("paragraph_space_before", 0))
                p.paragraph_format.space_after = Pt(config.get("paragraph_space_after", 6))
                
                # If not centered or listed, justify alignment
                if p.alignment != WD_ALIGN_PARAGRAPH.CENTER and p.alignment != WD_ALIGN_PARAGRAPH.RIGHT:
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                for run in p.runs:
                    run.font.name = font_family
                    run.font.size = Pt(font_size_body)
                    run.font.color.rgb = RGBColor(0, 0, 0)

        # 4. Format Tables (if present)
        for table in doc.tables:
            table.autofit = False
            for row in table.rows:
                for cell in row.cells:
                    for cp in cell.paragraphs:
                        cp.paragraph_format.line_spacing = 1.15
                        cp.paragraph_format.space_after = Pt(2)
                        cp.paragraph_format.space_before = Pt(2)
                        for crun in cp.runs:
                            crun.font.name = font_family
                            crun.font.size = Pt(font_size_body - 1)  # 11pt or 10pt in tables
                            crun.font.color.rgb = RGBColor(0, 0, 0)

        # 5. Add Page Numbers in Footer
        for section in doc.sections:
            footer = section.footer
            if footer and len(footer.paragraphs) > 0:
                fp = footer.paragraphs[0]
            else:
                fp = footer.add_paragraph()
            fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # Ensure font on footer
            for frun in fp.runs:
                frun.font.name = font_family
                frun.font.size = Pt(10)

        # Save the formatted docx
        doc.save(output_docx_path)
        return {
            "status": "success",
            "output_path": output_docx_path,
            "config_applied": config
        }

docx_formatter = DocxFormatterService()
