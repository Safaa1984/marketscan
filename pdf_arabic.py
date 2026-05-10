"""
Arabic text helper for reportlab PDF generation.
Registers Cairo font and provides ar() function for proper Arabic shaping.
"""

from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Register Cairo font ───────────────────────────────────────────────────────
_FONT_PATH = Path(__file__).parent / "static" / "fonts" / "Cairo-Regular.ttf"
_FONT_REGISTERED = False

def register_arabic_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return "Cairo"
    if _FONT_PATH.exists():
        try:
            pdfmetrics.registerFont(TTFont("Cairo", str(_FONT_PATH)))
            _FONT_REGISTERED = True
            return "Cairo"
        except Exception:
            pass
    return "Helvetica"

ARABIC_FONT = register_arabic_font()


# ── Text shaping ──────────────────────────────────────────────────────────────
def ar(text: str) -> str:
    """Reshape and reorder Arabic text for correct PDF rendering."""
    if not text:
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)


def is_arabic(text: str) -> bool:
    """Return True if text contains Arabic characters."""
    return any('؀' <= c <= 'ۿ' for c in str(text))
