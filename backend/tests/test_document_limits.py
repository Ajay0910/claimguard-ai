import fitz
import pytest
import sys
from pathlib import Path
from types import SimpleNamespace

from app.extraction.preprocessor import pdf_to_images


def test_pdf_page_limit_rejects_before_rendering_and_leaves_no_temp_pages(tmp_path):
    pdf_path = tmp_path / "many-pages.pdf"
    document = fitz.open()
    document.new_page()
    document.new_page()
    document.save(pdf_path)
    document.close()

    with pytest.raises(ValueError, match="page count"):
        pdf_to_images(str(pdf_path), max_pages=1)

    assert list(tmp_path.glob("temp_page_*.png")) == []


def test_pdf_aggregate_pixel_budget_rejects_before_rendering(tmp_path, monkeypatch):
    class Page:
        rect = SimpleNamespace(width=2160, height=2160)  # 20.25 MP at 150 DPI

        def __init__(self):
            self.render_calls = 0

        def get_pixmap(self, *, dpi):
            self.render_calls += 1
            return SimpleNamespace(save=lambda path: Path(path).write_bytes(b"page"))

    pages = [Page(), Page()]

    class Document:
        def __len__(self):
            return len(pages)

        def __iter__(self):
            return iter(pages)

        def close(self):
            pass

    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda _path: Document()))

    with pytest.raises(ValueError, match="total pixel"):
        pdf_to_images(str(tmp_path / "large.pdf"))

    assert [page.render_calls for page in pages] == [0, 0]


def test_pdf_temporary_page_names_do_not_collide_across_documents(tmp_path, monkeypatch):
    class Pixmap:
        def save(self, path):
            Path(path).write_bytes(b"page")

    class Page:
        rect = SimpleNamespace(width=72, height=72)

        def get_pixmap(self, *, dpi):
            return Pixmap()

    class Document:
        def __len__(self):
            return 1

        def __iter__(self):
            return iter([Page()])

        def close(self):
            pass

    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda _path: Document()))

    first = pdf_to_images(str(tmp_path / "first.pdf"))
    second = pdf_to_images(str(tmp_path / "second.pdf"))
    try:
        assert first[0] != second[0]
    finally:
        for path in first + second:
            Path(path).unlink(missing_ok=True)
