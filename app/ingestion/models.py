from pydantic import BaseModel


class Block(BaseModel):
    """One citable unit of text: a section (or part of one) on a single page."""

    text: str
    source: str  # filename -> citation
    page: int | None  # None for HTML
    section: str  # nearest heading
    device_model: str
    device_type: str
    doc_type: str  # manual | faq | other
