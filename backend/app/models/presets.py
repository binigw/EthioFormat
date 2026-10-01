from typing import Optional, List
from pydantic import BaseModel, Field

class MarginsModel(BaseModel):
    left_inches: float = Field(default=1.5, description="Binding / Left margin in inches")
    top_inches: float = Field(default=1.0, description="Top margin in inches")
    right_inches: float = Field(default=1.0, description="Right margin in inches")
    bottom_inches: float = Field(default=1.0, description="Bottom margin in inches")

class PageNumberingModel(BaseModel):
    preliminary: str = Field(default="ROMAN_LOWER", description="ROMAN_LOWER or NONE")
    main_body: str = Field(default="ARABIC", description="ARABIC numbering")
    position: str = Field(default="BOTTOM_CENTER", description="Header or Footer position")

class UniversityConfigModel(BaseModel):
    font_family: str = Field(default="Times New Roman")
    font_size_body: int = Field(default=12)
    font_size_h1: int = Field(default=14)
    font_size_h2: int = Field(default=12)
    font_size_h3: int = Field(default=12)
    line_spacing: float = Field(default=1.5)
    paragraph_space_after: int = Field(default=6)
    paragraph_space_before: int = Field(default=0)
    first_line_indent_inches: float = Field(default=0.5)
    margins: MarginsModel = Field(default_factory=MarginsModel)
    alignment: str = Field(default="JUSTIFY")
    toc_mode: str = Field(default="auto_generate")
    page_numbering: PageNumberingModel = Field(default_factory=PageNumberingModel)

class UniversityPresetItem(BaseModel):
    id: str
    name_en: str
    name_am: str
    display_name: str
    is_custom: bool = False
    config: Optional[UniversityConfigModel] = None

class PresetsListResponse(BaseModel):
    presets: List[UniversityPresetItem]
    custom_options: dict
