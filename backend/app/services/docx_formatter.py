import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

DATA_FILE = Path(__file__).parent.parent / "data" / "university_presets.json"

# Ethiopian Academic Standard major headings keywords
CHAPTER_TITLE_KEYWORDS = [
    "CHAPTER 1", "CHAPTER ONE", "CHAPTER I", "CHAPTER 2", "CHAPTER TWO", "CHAPTER II",
    "CHAPTER 3", "CHAPTER THREE", "CHAPTER III", "CHAPTER 4", "CHAPTER FOUR", "CHAPTER IV",
    "CHAPTER 5", "CHAPTER FIVE", "CHAPTER V", "CHAPTER 6", "CHAPTER SIX", "CHAPTER VI",
    "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES", "LIST OF APPENDICES",
    "LIST OF ABBREVIATIONS", "LIST OF ACRONYMS", "ABSTRACT", "DECLARATION", "APPROVAL SHEET",
    "CERTIFICATION", "DEDICATION", "ACKNOWLEDGEMENT", "ACKNOWLEDGEMENTS", "REFERENCES",
    "BIBLIOGRAPHY", "APPENDIX", "APPENDICES"
]

class DocxFormatterService:
    """
    High-precision Ethiopian University Academic Thesis Formatting Engine for .docx.
    Enforces institutional formatting standards:
    - Margins: 1.5" Left/Binding margin, 1.0" Top, Right, Bottom.
    - Typography: Times New Roman (or Arial for specific presets), pure black #000000.
    - Heading 1: 14pt Bold, 1.5 lines, 12pt before, 6pt after, 0 indent.
    - Heading 2: 12pt Bold, 1.5 lines, 10pt before, 4pt after, 0 indent.
    - Heading 3: 12pt Bold Italic, 1.5 lines, 8pt before, 4pt after, 0 indent.
    - Body Paragraphs: 12pt, 1.5 lines, 0pt before, 6pt after, 0.5" first-line indent, Justified.
    - Cover & Preliminary Title: Centered, 1.5 lines, 0 indent.
    - Tables & Figures: 10-11pt, clean borders, captions.
    - OpenXML Dynamic Page Numbering in footer.
    """

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

    def _set_run_typography(
        self,
        run: Any,
        font_name: str,
        font_size_pt: float,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        color_rgb: tuple = (0, 0, 0)
    ):
        """
        Deep OpenXML & python-docx typography enforcer.
        Sets w:rFonts (w:ascii, w:hAnsi, w:cs, w:eastAsia), removes conflicting theme fonts,
        and removes accidental text highlights / background colors from pasted content.
        """
        rPr = run._r.get_or_add_rPr()

        # 1. Enforce rFonts at XML level
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.append(rFonts)

        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rFonts.set(qn('w:cs'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)

        # Clear theme font overrides
        for attr in ['asciiTheme', 'hAnsiTheme', 'cstheme', 'eastAsiaTheme']:
            attr_qn = qn(f'w:{attr}')
            if attr_qn in rFonts.attrib:
                del rFonts.attrib[attr_qn]

        # 2. Clear highlighting / shading
        hl = rPr.find(qn('w:highlight'))
        if hl is not None:
            rPr.remove(hl)
        shd = rPr.find(qn('w:shd'))
        if shd is not None:
            rPr.remove(shd)

        # 3. Apply standard python-docx properties
        run.font.name = font_name
        run.font.size = Pt(font_size_pt)
        if bold is not None:
            run.font.bold = bold
        if italic is not None:
            run.font.italic = italic
        run.font.color.rgb = RGBColor(*color_rgb)

    def _add_page_number_to_footer(self, footer: Any, font_name: str = "Times New Roman", font_size_pt: int = 10):
        """
        Inserts dynamic Word OpenXML page number field (<w:fldSimple w:instr="PAGE"/>)
        centered in the footer.
        """
        try:
            footer.is_linked_to_previous = False
            if len(footer.paragraphs) > 0:
                p = footer.paragraphs[0]
                p.text = ""
            else:
                p = footer.add_paragraph()

            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0

            run = p.add_run()
            self._set_run_typography(run, font_name=font_name, font_size_pt=font_size_pt)

            fldSimple = OxmlElement('w:fldSimple')
            fldSimple.set(qn('w:instr'), 'PAGE')
            run._r.append(fldSimple)
        except Exception:
            pass

    def format_document(
        self,
        input_docx_path: str,
        output_docx_path: str,
        preset_id: str,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Loads the docx document and applies full Ethiopian thesis formatting.
        """
        doc = Document(input_docx_path)
        config = self.get_preset_config(preset_id, custom_rules)

        font_family = config["font_family"]
        font_size_body = float(config["font_size_body"])
        font_size_h1 = float(config["font_size_h1"])
        font_size_h2 = float(config["font_size_h2"])
        font_size_h3 = float(config["font_size_h3"])
        line_spacing = float(config["line_spacing"])
        indent_inches = float(config.get("first_line_indent_inches", 0.5))
        margins = config["margins"]

        # 1. Apply Margins to all sections (1.5" Left, 1.0" Top, Right, Bottom)
        for section in doc.sections:
            section.top_margin = Inches(margins.get("top_inches", 1.0))
            section.bottom_margin = Inches(margins.get("bottom_inches", 1.0))
            section.left_margin = Inches(margins.get("left_inches", 1.5))
            section.right_margin = Inches(margins.get("right_inches", 1.0))
            section.page_width = Inches(8.5)
            section.page_height = Inches(11.0)
            section.footer_distance = Inches(0.5)
            section.header_distance = Inches(0.5)

            # Insert dynamic OpenXML page numbers in footer
            self._add_page_number_to_footer(section.footer, font_name=font_family, font_size_pt=10)

        # 2. Update Default Styles in Document
        styles_map = {
            'Normal': (font_size_body, False, False),
            'Heading 1': (font_size_h1, True, False),
            'Heading 2': (font_size_h2, True, False),
            'Heading 3': (font_size_h3, True, True),
            'Title': (font_size_h1, True, False),
            'Subtitle': (font_size_body, True, False),
            'Header': (10, False, False),
            'Footer': (10, False, False),
        }

        for style_name, (sz, is_b, is_it) in styles_map.items():
            if style_name in doc.styles:
                try:
                    st = doc.styles[style_name]
                    st.font.name = font_family
                    st.font.size = Pt(sz)
                    st.font.bold = is_b
                    st.font.italic = is_it
                    st.font.color.rgb = RGBColor(0, 0, 0)
                except Exception:
                    pass

        # 3. Process & Format All Paragraphs
        seen_first_heading = False
        paragraph_count = len(doc.paragraphs)

        for idx, p in enumerate(doc.paragraphs):
            text_stripped = p.text.strip()
            if not text_stripped:
                # Limit empty paragraph spacing
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                continue

            text_upper = text_stripped.upper()
            style_name = p.style.name.lower() if p.style else ""

            # Check if this paragraph is on the cover page (before first chapter or TOC)
            is_cover_page = False
            if not seen_first_heading and idx < 20:
                if any(kw in text_upper for kw in ["CHAPTER 1", "CHAPTER ONE", "TABLE OF CONTENTS", "ABSTRACT", "DECLARATION"]):
                    seen_first_heading = True
                else:
                    is_cover_page = True

            # Heading Detection Regexes
            is_h1 = (
                ("heading 1" in style_name) or
                any(text_upper == kw or text_upper.startswith(kw + ":") or text_upper.startswith(kw + " ") for kw in CHAPTER_TITLE_KEYWORDS) or
                (bool(re.match(r'^(?:CHAPTER\s+[0-9IVX]+|[0-9]+\.\s+[A-Z\s]{3,80})$', text_stripped, re.IGNORECASE)) and len(text_stripped) < 90)
            )

            is_h2 = not is_h1 and (
                ("heading 2" in style_name) or
                (bool(re.match(r'^[0-9]+\.[0-9]+\s+[A-Za-z]', text_stripped)) and len(text_stripped) < 110)
            )

            is_h3 = not is_h1 and not is_h2 and (
                ("heading 3" in style_name) or
                (bool(re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\s+[A-Za-z]', text_stripped)) and len(text_stripped) < 110)
            )

            is_caption = bool(re.match(r'^(?:Table|Figure|Fig\.|Appendix)\s+[0-9IVX]+(?:\.[0-9]+)?\s*[:\-]', text_stripped, re.IGNORECASE))

            if is_h1:
                seen_first_heading = True
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_before = Pt(14)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.first_line_indent = Inches(0)
                p.paragraph_format.left_indent = Inches(0)
                p.paragraph_format.right_indent = Inches(0)
                
                # Center chapter titles, left-align standard headings
                if any(kw in text_upper for kw in ["CHAPTER", "TABLE OF CONTENTS", "LIST OF", "ABSTRACT", "DECLARATION", "APPROVAL", "DEDICATION", "ACKNOWLEDGEMENT"]):
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                for run in p.runs:
                    self._set_run_typography(run, font_name=font_family, font_size_pt=font_size_h1, bold=True, italic=False)

            elif is_h2:
                seen_first_heading = True
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_before = Pt(10)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.first_line_indent = Inches(0)
                p.paragraph_format.left_indent = Inches(0)
                p.paragraph_format.right_indent = Inches(0)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                for run in p.runs:
                    self._set_run_typography(run, font_name=font_family, font_size_pt=font_size_h2, bold=True, italic=False)

            elif is_h3:
                seen_first_heading = True
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.first_line_indent = Inches(0)
                p.paragraph_format.left_indent = Inches(0)
                p.paragraph_format.right_indent = Inches(0)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                for run in p.runs:
                    self._set_run_typography(run, font_name=font_family, font_size_pt=font_size_h3, bold=True, italic=True)

            elif is_caption:
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.first_line_indent = Inches(0)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                for run in p.runs:
                    self._set_run_typography(run, font_name=font_family, font_size_pt=font_size_body - 1, bold=True)

            elif is_cover_page or p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                # Cover page elements
                p.paragraph_format.line_spacing = 1.5
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.first_line_indent = Inches(0)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                is_title_line = len(text_stripped) > 20 and text_stripped.isupper()
                is_bold_cover = is_title_line or any(kw in text_upper for kw in ["UNIVERSITY", "COLLEGE", "DEPARTMENT", "FACULTY", "THESIS", "BY"])
                font_sz = font_size_h1 if is_title_line else font_size_body

                for run in p.runs:
                    self._set_run_typography(run, font_name=font_family, font_size_pt=font_sz, bold=is_bold_cover)

            else:
                # Standard Body Paragraph
                p.paragraph_format.line_spacing = line_spacing
                p.paragraph_format.space_before = Pt(config.get("paragraph_space_before", 0))
                p.paragraph_format.space_after = Pt(config.get("paragraph_space_after", 6))

                # If paragraph was explicitly right-aligned or centered, keep alignment; otherwise JUSTIFY
                if p.alignment not in (WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT):
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    # Apply 0.5" first-line indent on multi-sentence or narrative body paragraphs
                    if len(text_stripped) > 60 and not text_stripped.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.")):
                        p.paragraph_format.first_line_indent = Inches(indent_inches)
                    else:
                        p.paragraph_format.first_line_indent = Inches(0)

                for run in p.runs:
                    self._set_run_typography(run, font_name=font_family, font_size_pt=font_size_body)

        # 4. Format Tables (Academic 3-line / clean grid table styling)
        for table in doc.tables:
            table.autofit = False
            for r_idx, row in enumerate(table.rows):
                for cell in row.cells:
                    for cp in cell.paragraphs:
                        cp.paragraph_format.line_spacing = 1.15
                        cp.paragraph_format.space_before = Pt(2)
                        cp.paragraph_format.space_after = Pt(2)
                        cp.paragraph_format.first_line_indent = Inches(0)
                        
                        is_header_row = (r_idx == 0)
                        for crun in cp.runs:
                            self._set_run_typography(
                                crun,
                                font_name=font_family,
                                font_size_pt=font_size_body - 1,  # 11pt in tables
                                bold=is_header_row
                            )

        # Save formatted document
        doc.save(output_docx_path)
        return {
            "status": "success",
            "output_path": output_docx_path,
            "config_applied": config
        }

docx_formatter = DocxFormatterService()
