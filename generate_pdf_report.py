#!/usr/bin/env python3
"""
Professional Marketing Report Generator — Client-Ready PDF
Executive-quality design: cover page, score gauge, ROI projections,
before/after comparison, phased action plan, and closing pitch.

Requires: reportlab (pip install reportlab)
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch, mm
    from reportlab.lib.colors import HexColor, white, black, Color
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.platypus.flowables import Flowable
    from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Line
    from reportlab.graphics import renderPDF
except ImportError:
    print("Error: reportlab is required.  pip install reportlab")
    sys.exit(1)

# ── Arabic font support ───────────────────────────────────────────────────────
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as _TTFont

def _get_arabic_font(script_file):
    fp = Path(script_file).parent / "static" / "fonts" / "Cairo-Regular.ttf"
    if fp.exists():
        try:
            pdfmetrics.registerFont(_TTFont("Cairo", str(fp)))
            return "Cairo"
        except Exception:
            pass
    return "Helvetica"

def _reshape(text):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


PAGE_W, PAGE_H = A4  # 595 x 842 pts

# ── Palette ──────────────────────────────────────────────────────────────────
C = {
    # ── ProVision 360 Brand Colors ──────────────────────────────────────
    "navy":      HexColor("#1A1464"),   # brand dark navy
    "navy_mid":  HexColor("#221880"),   # brand mid
    "blue":      HexColor("#4B35C8"),   # brand purple
    "blue_lt":   HexColor("#EDEAFF"),   # brand purple light
    "orange":    HexColor("#4B35C8"),   # mapped → brand purple
    "orange_lt": HexColor("#EDEAFF"),   # mapped → brand purple light
    "pink":      HexColor("#C87DB8"),   # brand rose/pink
    "pink_lt":   HexColor("#FCF0F8"),   # brand rose light
    # ── Semantic colors (kept neutral) ──────────────────────────────────
    "green":     HexColor("#0E9F6E"),
    "green_lt":  HexColor("#E8FFF5"),
    "yellow":    HexColor("#D97706"),
    "yellow_lt": HexColor("#FEFCE8"),
    "red":       HexColor("#DC2626"),
    "red_lt":    HexColor("#FEF2F2"),
    "gray":      HexColor("#6B7280"),
    "gray_lt":   HexColor("#F3F4F6"),
    "gray_bd":   HexColor("#E5E7EB"),
    "slate":     HexColor("#94A3B8"),
    "white":     white,
    "text":      HexColor("#111827"),
    "text_md":   HexColor("#374151"),
    "text_lt":   HexColor("#6B7280"),
}


def score_color(score, light=False):
    if score >= 75:
        return C["green_lt"] if light else C["green"]
    elif score >= 60:
        return C["blue_lt"] if light else C["blue"]
    elif score >= 45:
        return C["yellow_lt"] if light else C["yellow"]
    else:
        return C["red_lt"] if light else C["red"]


def score_grade(score):
    for threshold, grade in [(90,"A+"),(80,"A"),(70,"B"),(60,"C"),(50,"D")]:
        if score >= threshold:
            return grade
    return "F"


def score_label(score):
    if score >= 75: return "Strong"
    if score >= 60: return "Good"
    if score >= 45: return "Needs Work"
    return "Critical"


def hex_str(color):
    try:
        v = color.hexval()
        return v[1:] if v.startswith("#") else v
    except Exception:
        r = int(color.red * 255)
        g = int(color.green * 255)
        b = int(color.blue * 255)
        return f"{r:02x}{g:02x}{b:02x}"


# ── Custom Flowables ──────────────────────────────────────────────────────────

class SectionBanner(Flowable):
    """Full-width navy section banner with orange left accent."""
    def __init__(self, title, subtitle="", height=42):
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self._height = height

    def wrap(self, aw, ah):
        self._width = aw
        return aw, self._height

    def draw(self):
        c = self.canv
        w, h = self._width, self._height
        c.setFillColor(C["navy"])
        c.roundRect(0, 0, w, h, 5, fill=1, stroke=0)
        c.setFillColor(C["orange"])
        c.rect(0, 0, 5, h, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 13)
        ty = h / 2 + (5 if self.subtitle else -4)
        c.drawString(16, ty, self.title)
        if self.subtitle:
            c.setFillColor(C["slate"])
            c.setFont("Helvetica", 8)
            c.drawString(16, h / 2 - 10, self.subtitle)


class ScoreGauge(Flowable):
    """Donut-style score gauge drawn with thick arc strokes."""
    def __init__(self, score, size=140, label="Overall Score"):
        super().__init__()
        self.score = score
        self.size = size
        self.label = label

    def wrap(self, aw, ah):
        return self.size, self.size + 16

    def draw(self):
        c = self.canv
        sz = self.size
        cx, cy = sz / 2, sz / 2 + 8
        r = sz / 2 - 6
        ring = r * 0.28
        arc_r = r - ring / 2

        c.saveState()
        c.setLineCap(1)
        c.setLineWidth(ring)

        # Background arc: from 315 deg CCW 270 deg to 225 deg
        c.setStrokeColor(C["gray_lt"])
        c.arc(cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r,
              startAng=315, extent=270)

        # Score arc (filled portion)
        score_ext = (self.score / 100) * 270
        start_ang = 225 - score_ext
        c.setStrokeColor(score_color(self.score))
        c.arc(cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r,
              startAng=start_ang, extent=score_ext)

        c.restoreState()

        # White center fill
        c.setFillColor(white)
        c.circle(cx, cy, arc_r - ring / 2 - 2, stroke=0, fill=1)

        # Score number
        fg = score_color(self.score)
        c.setFillColor(fg)
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(cx, cy + 4, str(int(self.score)))

        c.setFillColor(C["text_lt"])
        c.setFont("Helvetica", 9)
        c.drawCentredString(cx, cy - 14, "/ 100")

        c.setFillColor(C["text_md"])
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(cx, 2, self.label)


class CategoryBar(Flowable):
    """Horizontal labeled progress bar for a category score."""
    def __init__(self, label, score, weight="", height=26):
        super().__init__()
        self.label = label
        self.score = score
        self.weight = weight
        self._height = height

    def wrap(self, aw, ah):
        self._width = aw
        return aw, self._height

    def draw(self):
        c = self.canv
        aw, h = self._width, self._height
        label_w = 175
        score_w = 38
        bar_x = label_w + 8
        bar_w = aw - label_w - score_w - 16
        mid = h / 2

        lbl = self.label + (f"  ({self.weight})" if self.weight else "")
        c.setFillColor(C["text_md"])
        c.setFont("Helvetica", 9)
        c.drawString(0, mid - 4, lbl)

        c.setFillColor(C["gray_lt"])
        c.roundRect(bar_x, mid - 6, bar_w, 12, 6, fill=1, stroke=0)

        fill_w = max(12, (self.score / 100) * bar_w)
        c.setFillColor(score_color(self.score))
        c.roundRect(bar_x, mid - 6, fill_w, 12, 6, fill=1, stroke=0)

        c.setFillColor(score_color(self.score))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(bar_x + bar_w + 8, mid - 4, str(int(self.score)))


class FindingCard(Flowable):
    """Colored finding card — reframed as a growth opportunity."""
    SEV_MAP = {
        "Critical": ("red",    "URGENT REVENUE RISK"),
        "High":     ("orange", "HIGH-IMPACT OPPORTUNITY"),
        "Medium":   ("yellow", "GROWTH LEVER"),
        "Low":      ("blue",   "OPTIMIZATION WIN"),
    }

    def __init__(self, number, severity, text):
        super().__init__()
        self.number = number
        self.severity = severity
        self.text = text

    def wrap(self, aw, ah):
        self._width = aw
        lines = math.ceil(len(self.text) / 88) + 1
        self._height = max(54, lines * 14 + 28)
        return aw, self._height

    def draw(self):
        c = self.canv
        w, h = self._width, self._height
        key, opp_label = self.SEV_MAP.get(self.severity, ("blue", "OPPORTUNITY"))
        fg = C[key]
        bg = C[key + "_lt"]

        c.setFillColor(bg)
        c.roundRect(0, 0, w, h, 5, fill=1, stroke=0)
        c.setFillColor(fg)
        c.rect(0, 0, 4, h, fill=1, stroke=0)

        c.setFillColor(fg)
        c.circle(22, h / 2, 11, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(22, h / 2 - 3, str(self.number))

        c.setFillColor(fg)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(42, h - 14, opp_label)

        c.setFillColor(C["text_md"])
        c.setFont("Helvetica", 9)
        words = self.text.split()
        lines, line = [], []
        for word in words:
            test = " ".join(line + [word])
            if c.stringWidth(test, "Helvetica", 9) < w - 58:
                line.append(word)
            else:
                lines.append(" ".join(line))
                line = [word]
        if line:
            lines.append(" ".join(line))
        for i, ln in enumerate(lines):
            c.drawString(42, h - 26 - i * 13, ln)


# ── Page Callbacks ────────────────────────────────────────────────────────────

def make_callbacks(brand, url, date_str, report_score):

    def cover(canvas, doc):
        w, h = A4
        canvas.setFillColor(C["navy"])
        canvas.rect(0, 0, w, h, fill=1, stroke=0)

        # Decorative circles
        canvas.setFillColor(C["navy_mid"])
        canvas.circle(w + 20, h - 80, 150, fill=1, stroke=0)
        canvas.circle(-30, 60, 100, fill=1, stroke=0)

        # Top orange stripe
        canvas.setFillColor(C["orange"])
        canvas.rect(0, h - 5, w, 5, fill=1, stroke=0)

        # PROVISION360 logo PNG — top-left header
        _logo = Path(__file__).parent.parent / "webapp" / "static" / "logo.png"
        if not _logo.exists():
            _logo = Path(__file__).parent / "logo.png"
        if _logo.exists():
            logo_h = 28
            logo_w = logo_h * 3.2   # approximate aspect ratio
            canvas.drawImage(str(_logo), 50, h - 42, width=logo_w, height=logo_h,
                             preserveAspectRatio=True, mask="auto")
            canvas.setFillColor(HexColor("#94A3B8"))
            canvas.setFont("Helvetica", 8)
            canvas.drawString(50 + logo_w + 8, h - 28, "provision360.net")
        else:
            # Fallback text badge
            canvas.setFillColor(HexColor("#4B35C8"))
            canvas.roundRect(50, h - 40, 135, 26, 5, fill=1, stroke=0)
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(58, h - 26, "PROVISION")
            canvas.setFillColor(HexColor("#C87DB8"))
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(120, h - 26, "360")

        # Right: report label + date
        canvas.setFillColor(HexColor("#C87DB8"))
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(w - 50, h - 22, "MARKETING AUDIT REPORT")
        canvas.setFillColor(C["slate"])
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(w - 50, h - 32, f"Confidential  ·  {date_str}")

        # Brand
        canvas.setFillColor(white)
        canvas.setFont("Helvetica-Bold", 42)
        canvas.drawString(50, h / 2 + 95, brand.upper())

        canvas.setFillColor(C["slate"])
        canvas.setFont("Helvetica", 13)
        canvas.drawString(50, h / 2 + 68, url)

        # Divider
        canvas.setStrokeColor(C["orange"])
        canvas.setLineWidth(2)
        canvas.line(50, h / 2 + 55, w - 50, h / 2 + 55)

        # Tagline
        canvas.setFillColor(HexColor("#CBD5E1"))
        canvas.setFont("Helvetica", 12)
        canvas.drawString(50, h / 2 + 36,
                          "Full-Funnel Marketing Performance Analysis & Growth Roadmap")

        # Score badge
        sc_col = score_color(report_score)
        badge_x, badge_y, badge_r = w - 110, h / 2 + 68, 52
        canvas.setFillColor(sc_col)
        canvas.circle(badge_x, badge_y, badge_r, stroke=0, fill=1)
        canvas.setFillColor(HexColor("#07111F"))
        canvas.circle(badge_x, badge_y, badge_r - 9, stroke=0, fill=1)
        canvas.setFillColor(sc_col)
        canvas.setFont("Helvetica-Bold", 28)
        canvas.drawCentredString(badge_x, badge_y + 3, str(int(report_score)))
        canvas.setFillColor(C["slate"])
        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(badge_x, badge_y - 14, "/ 100")

        # Content pills
        pills = ["Executive Dashboard", "Score Breakdown",
                 "Growth Opportunities", "ROI Projections", "90-Day Roadmap"]
        px, py = 50, h / 2 - 18
        canvas.setFont("Helvetica", 8)
        for pill in pills:
            pw = canvas.stringWidth(pill, "Helvetica", 8) + 16
            if px + pw > w - 60:
                px, py = 50, py - 26
            canvas.setFillColor(C["navy_mid"])
            canvas.roundRect(px, py, pw, 18, 9, fill=1, stroke=0)
            canvas.setStrokeColor(C["slate"])
            canvas.setLineWidth(0.5)
            canvas.roundRect(px, py, pw, 18, 9, fill=0, stroke=1)
            canvas.setFillColor(C["slate"])
            canvas.drawString(px + 8, py + 5, pill)
            px += pw + 8

        # Bottom strip
        canvas.setFillColor(HexColor("#07111F"))
        canvas.rect(0, 0, w, 44, fill=1, stroke=0)
        # PROVISION360 logo PNG — bottom-left of cover footer
        _logo = Path(__file__).parent.parent / "webapp" / "static" / "logo.png"
        if not _logo.exists():
            _logo = Path(__file__).parent / "logo.png"
        if _logo.exists():
            logo_h = 26
            logo_w = logo_h * 3.2
            canvas.drawImage(str(_logo), 50, 9, width=logo_w, height=logo_h,
                             preserveAspectRatio=True, mask="auto")
            canvas.setFillColor(HexColor("#94A3B8"))
            canvas.setFont("Helvetica", 7)
            canvas.drawString(50 + logo_w + 8, 22, "provision360.net")
            canvas.setFillColor(C["slate"])
            canvas.setFont("Helvetica", 7)
            canvas.drawString(50 + logo_w + 8, 13, f"Generated {date_str}")
        else:
            canvas.setFillColor(HexColor("#4B35C8"))
            canvas.roundRect(50, 9, 130, 26, 5, fill=1, stroke=0)
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(58, 22, "PROVISION")
            canvas.setFillColor(HexColor("#C87DB8"))
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(120, 22, "360")
            canvas.setFillColor(C["slate"])
            canvas.setFont("Helvetica", 7)
            canvas.drawString(192, 22, "provision360.net")
            canvas.drawString(192, 13, f"Generated {date_str}")
        canvas.drawRightString(w - 50, 15, "Page 1  —  Confidential")

    def later(canvas, doc):
        w, h = A4
        canvas.setFillColor(C["navy"])
        canvas.rect(0, h - 30, w, 30, fill=1, stroke=0)
        canvas.setFillColor(C["orange"])
        canvas.rect(0, h - 33, w, 3, fill=1, stroke=0)
        # PROVISION360 mini logo PNG in header
        _logo = Path(__file__).parent.parent / "webapp" / "static" / "logo.png"
        if not _logo.exists():
            _logo = Path(__file__).parent / "logo.png"
        if _logo.exists():
            logo_h = 18
            logo_w = logo_h * 3.2
            canvas.drawImage(str(_logo), 50, h - 27, width=logo_w, height=logo_h,
                             preserveAspectRatio=True, mask="auto")
            _after_logo = 50 + logo_w + 8
        else:
            canvas.setFillColor(HexColor("#4B35C8"))
            canvas.roundRect(50, h - 26, 90, 16, 3, fill=1, stroke=0)
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 6)
            canvas.drawString(55, h - 18, "PROVISION")
            canvas.setFillColor(HexColor("#C87DB8"))
            canvas.setFont("Helvetica-Bold", 6)
            canvas.drawString(110, h - 18, "360")
            _after_logo = 148

        canvas.setFillColor(C["slate"])
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(_after_logo, h - 21, f"· {brand}  ·  Marketing Audit Report")
        canvas.drawRightString(w - 50, h - 21, "CONFIDENTIAL")
        canvas.setFillColor(C["gray_lt"])
        canvas.rect(0, 0, w, 24, fill=1, stroke=0)
        canvas.setStrokeColor(C["gray_bd"])
        canvas.setLineWidth(0.5)
        canvas.line(0, 24, w, 24)
        canvas.setFillColor(C["text_lt"])
        canvas.setFont("Helvetica", 7)
        canvas.drawString(50, 8, f"© PROVISION360  ·  provision360.net  ·  {url}")
        canvas.drawRightString(w - 50, 8, f"Page {doc.page}")

    return cover, later


# ── Styles ────────────────────────────────────────────────────────────────────

def make_styles():
    S = {}
    S["h1"] = ParagraphStyle("H1", fontSize=20, fontName="Helvetica-Bold",
                             textColor=C["navy"], spaceBefore=14, spaceAfter=6, leading=26)
    S["h2"] = ParagraphStyle("H2", fontSize=13, fontName="Helvetica-Bold",
                             textColor=C["navy"], spaceBefore=10, spaceAfter=5)
    S["h3"] = ParagraphStyle("H3", fontSize=10, fontName="Helvetica-Bold",
                             textColor=C["text_md"], spaceBefore=6, spaceAfter=3)
    S["body"] = ParagraphStyle("Body", fontSize=9.5, fontName="Helvetica",
                               textColor=C["text_md"], spaceAfter=5, leading=15,
                               alignment=TA_JUSTIFY)
    S["sm"] = ParagraphStyle("Sm", fontSize=8.5, fontName="Helvetica",
                             textColor=C["text_md"], spaceAfter=4, leading=13)
    S["caption"] = ParagraphStyle("Cap", fontSize=7.5, fontName="Helvetica",
                                  textColor=C["text_lt"], spaceAfter=3)
    S["center"] = ParagraphStyle("Ctr", fontSize=9.5, fontName="Helvetica",
                                 textColor=C["text_md"], alignment=TA_CENTER)
    S["bullet"] = ParagraphStyle("Bul", fontSize=9, fontName="Helvetica",
                                 textColor=C["text_md"], spaceAfter=4, leading=14,
                                 leftIndent=14, firstLineIndent=-14)
    return S


# ── KPI strip ─────────────────────────────────────────────────────────────────

def kpi_row(score, findings, quick_wins):
    grade    = score_grade(score)
    priority = sum(1 for f in findings if f.get("severity") in ("Critical", "High"))
    qw_count = len(quick_wins)

    items = [
        (str(int(score)), "Marketing Score",
         score_color(score, True), score_color(score)),
        (grade,           "Performance Grade", C["blue_lt"],  C["blue"]),
        (str(priority),   "Priority Issues",
         C["red_lt"] if priority >= 2 else C["yellow_lt"],
         C["red"]    if priority >= 2 else C["yellow"]),
        (str(qw_count),   "Quick Wins",        C["green_lt"], C["green"]),
    ]

    cells = []
    for val, lbl, bg, fg in items:
        inner = Table([
            [Paragraph(f'<font color="#{hex_str(fg)}"><b>{val}</b></font>',
                       ParagraphStyle("KV", fontSize=26, fontName="Helvetica-Bold",
                                      alignment=TA_CENTER, spaceAfter=0))],
            [Paragraph(lbl, ParagraphStyle("KL", fontSize=7.5, fontName="Helvetica",
                                           textColor=C["text_lt"],
                                           alignment=TA_CENTER))],
        ], colWidths=[115])
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("BOX",           (0, 0), (-1, -1), 1.5, fg),
            ("TOPPADDING",    (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        cells.append(inner)

    t = Table([cells], colWidths=[118, 118, 118, 118], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# ── Action card ───────────────────────────────────────────────────────────────

def action_card(number, text, fg, bg, S):
    inner = Table([[
        Paragraph(f'<font color="#{hex_str(fg)}"><b>{number}</b></font>',
                  ParagraphStyle("AN", fontSize=13, fontName="Helvetica-Bold",
                                 alignment=TA_CENTER)),
        Paragraph(text, S["sm"]),
    ]], colWidths=[28, 452])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 0.8, fg),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (0, -1), 6),
        ("RIGHTPADDING",  (1, 0), (1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return inner


# ── State comparison box ──────────────────────────────────────────────────────

def state_box(title, score_txt, bullets, fg, bg):
    content = [
        Paragraph(f'<font color="#{hex_str(fg)}"><b>{title}</b></font>',
                  ParagraphStyle("ST", fontSize=9, fontName="Helvetica-Bold",
                                 alignment=TA_CENTER)),
        Paragraph(f'<font color="#{hex_str(fg)}"><b>{score_txt}</b></font>',
                  ParagraphStyle("SS", fontSize=18, fontName="Helvetica-Bold",
                                 alignment=TA_CENTER, spaceAfter=4)),
        Paragraph(bullets,
                  ParagraphStyle("SB", fontSize=8, fontName="Helvetica",
                                 textColor=C["text_md"], alignment=TA_CENTER,
                                 leading=13)),
    ]
    t = Table([[c] for c in content], colWidths=[215])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, fg),
    ]))
    return t


# ── Main generator ────────────────────────────────────────────────────────────

def generate_report(data, output_path):
    brand     = data.get("brand_name", "Company")
    url       = data.get("url", "")
    score     = data.get("overall_score", 0)
    date_str  = data.get("date", datetime.now().strftime("%B %d, %Y"))
    findings  = data.get("findings", [])
    qw        = data.get("quick_wins", [])
    mid       = data.get("medium_term", [])
    strategic = data.get("strategic", [])
    cats      = data.get("categories", {})

    cover_cb, later_cb = make_callbacks(brand, url, date_str, score)
    S = make_styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=44, bottomMargin=36,
    )

    els = []

    # ── COVER  (canvas callback draws it; PageBreak ends the blank page) ────
    els.append(PageBreak())

    # ── PAGE 2: EXECUTIVE DASHBOARD ─────────────────────────────────────────
    els.append(SectionBanner("Executive Dashboard",
                             "At-a-Glance Performance Overview"))
    els.append(Spacer(1, 10))

    gauge = ScoreGauge(score, size=140, label="Overall Score")
    grade = score_grade(score)
    exec_txt = data.get("executive_summary", "")

    gauge_wrap = Table([[gauge]], colWidths=[155])
    gauge_wrap.setStyle(TableStyle([
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    summary_wrap = Table([
        [Paragraph("EXECUTIVE SUMMARY", S["caption"])],
        [Paragraph(exec_txt, S["body"])],
        [Spacer(1, 4)],
        [Paragraph(
            f'<font color="#{hex_str(score_color(score))}"><b>'
            f'Grade: {grade} — {score_label(score)}</b></font>  '
            f'This report identifies the highest-leverage improvements to drive '
            f'more leads, higher conversion, and stronger market positioning.',
            S["sm"]
        )],
    ], colWidths=[330])
    summary_wrap.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    two_col = Table([[gauge_wrap, summary_wrap]], colWidths=[158, 337])
    two_col.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    els.append(two_col)
    els.append(Spacer(1, 14))
    els.append(kpi_row(score, findings, qw))
    els.append(PageBreak())

    # ── PAGE 3: PERFORMANCE SCORECARD ───────────────────────────────────────
    els.append(SectionBanner("Performance Scorecard",
                             "Category-by-Category Analysis"))
    els.append(Spacer(1, 14))

    for cat_name, cat_data in cats.items():
        els.append(CategoryBar(cat_name,
                               cat_data.get("score", 50),
                               cat_data.get("weight", "")))
        els.append(Spacer(1, 5))

    els.append(Spacer(1, 18))
    els.append(Paragraph("Score Interpretation Guide", S["h2"]))

    legend = [
        ["Range",    "Grade", "Status",    "What It Means"],
        ["75–100", "A",    "Strong",    "Best-in-class. Maintain and build on this."],
        ["60–74",  "B/C",  "Good",      "Solid foundation. Small wins will compound."],
        ["45–59",  "D",    "Needs Work","Significant gaps. Prioritise for real impact."],
        ["0–44",   "F",    "Critical",  "Immediate attention required — high revenue risk."],
    ]
    row_bgs = [None, C["green_lt"], C["blue_lt"], C["yellow_lt"], C["red_lt"]]
    leg_t = Table(legend, colWidths=[68, 45, 78, 295])
    ts = [
        ("BACKGROUND",    (0, 0), (-1, 0), C["navy"]),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("GRID",          (0, 0), (-1, -1), 0.4, C["gray_bd"]),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ALIGN",         (0, 0), (1, -1), "CENTER"),
    ]
    for i, bg in enumerate(row_bgs):
        if bg:
            ts.append(("BACKGROUND", (0, i), (-1, i), bg))
    leg_t.setStyle(TableStyle(ts))
    els.append(leg_t)
    els.append(PageBreak())

    # ── PAGE 4: GROWTH OPPORTUNITIES ────────────────────────────────────────
    els.append(SectionBanner("Growth Opportunities",
                             "Findings Ranked by Business Impact"))
    els.append(Spacer(1, 8))
    els.append(Paragraph(
        "Each finding below is a revenue leverage point. Addressing them in priority "
        "order will unlock higher conversion rates, stronger search visibility, and "
        "improved client trust — compounding results over 90 days.",
        S["body"]
    ))
    els.append(Spacer(1, 10))

    for idx, f in enumerate(findings, 1):
        els.append(FindingCard(idx, f.get("severity", "Medium"),
                               f.get("finding", "")))
        els.append(Spacer(1, 6))

    els.append(PageBreak())

    # ── PAGE 5: ROI IMPACT PROJECTION ───────────────────────────────────────
    els.append(SectionBanner("Revenue Impact Projection",
                             "Estimated Growth from Implementing Recommendations"))
    els.append(Spacer(1, 8))
    els.append(Paragraph(
        "Directional estimates based on industry benchmarks for comparable digital agencies. "
        "Actual results depend on execution speed and market conditions.",
        S["body"]
    ))
    els.append(Spacer(1, 12))

    roi_rows = [
        ["Optimisation Area",       "Current State",              "Optimised State",             "Est. Lift"],
        ["Homepage Hero Messaging", "Generic, outcome-less copy", "Specific client outcome CTA",  "+15–25%\nlead capture"],
        ["Service Packaging",       "No structured packages",     "3-tier outcome-based offers",  "+20–35%\navg deal size"],
        ["CTA Copy & Placement",    "‘For More...’ vague", "'Request Strategy Call'",  "+10–20%\ncontact rate"],
        ["SEO Title & Meta",        "Generic ‘Home -’ title", "Keyword-optimised titles", "+25–40%\norganic traffic"],
        ["Trust & Social Proof",    "No case studies / proof",    "Client results + testimonials","+15–30%\nconversion"],
        ["Lead Capture",            "No lead magnet",             "Free audit / download offer",  "+30–50%\nemail subscribers"],
    ]
    roi_t = Table(roi_rows, colWidths=[118, 110, 128, 88])
    roi_ts = [
        ("BACKGROUND",    (0, 0), (-1, 0), C["navy"]),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.4, C["gray_bd"]),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",     (0, 1), (0, -1), C["navy"]),
        ("TEXTCOLOR",     (3, 1), (3, -1), C["green"]),
        ("FONTNAME",      (3, 1), (3, -1), "Helvetica-Bold"),
        ("ALIGN",         (3, 0), (3, -1), "CENTER"),
    ]
    for i in range(1, len(roi_rows)):
        bg = white if i % 2 == 0 else C["gray_lt"]
        roi_ts.append(("BACKGROUND", (0, i), (-1, i), bg))
    roi_t.setStyle(TableStyle(roi_ts))
    els.append(roi_t)
    els.append(Spacer(1, 20))

    # Before / After
    els.append(Paragraph("Before vs. After", S["h2"]))
    els.append(Spacer(1, 6))

    before = state_box(
        "CURRENT STATE", f"{int(score)} / 100",
        "Generic messaging · Weak CTAs<br/>No service packages · Thin SEO<br/>No trust signals",
        C["red"], C["red_lt"]
    )
    after = state_box(
        "OPTIMISED STATE", "75–85 / 100",
        "Clear value proposition · Strong CTAs<br/>Outcome-based packages · SEO-ready<br/>Case studies + testimonials",
        C["green"], C["green_lt"]
    )
    arrow = Paragraph("→",
                      ParagraphStyle("AR", fontSize=22, fontName="Helvetica-Bold",
                                     textColor=C["navy"], alignment=TA_CENTER))
    ba = Table([[before, arrow, after]], colWidths=[220, 45, 220])
    ba.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (1, 0),   "CENTER"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    els.append(ba)
    els.append(PageBreak())

    # ── PAGE 6: 90-DAY ACTION PLAN ───────────────────────────────────────────
    els.append(SectionBanner("90-Day Action Plan",
                             "Prioritised Roadmap for Maximum Impact"))
    els.append(Spacer(1, 12))

    els.append(Paragraph("Phase 1 — Quick Wins  (This Week)", S["h2"]))
    els.append(Paragraph("High-impact, low-effort — can be done in days.", S["sm"]))
    els.append(Spacer(1, 6))
    for i, w in enumerate(qw, 1):
        els.append(action_card(i, w, C["green"], C["green_lt"], S))
        els.append(Spacer(1, 4))

    els.append(Spacer(1, 10))
    els.append(Paragraph("Phase 2 — Growth Sprint  (Months 1–3)", S["h2"]))
    els.append(Paragraph("Structural improvements that build compounding returns.", S["sm"]))
    els.append(Spacer(1, 6))
    for i, a in enumerate(mid, 1):
        els.append(action_card(i, a, C["blue"], C["blue_lt"], S))
        els.append(Spacer(1, 4))

    els.append(Spacer(1, 10))
    els.append(Paragraph("Phase 3 — Market Leadership  (Months 3–6)", S["h2"]))
    els.append(Paragraph("Strategic moves to build authority and repeatable growth engines.", S["sm"]))
    els.append(Spacer(1, 6))
    for i, a in enumerate(strategic, 1):
        els.append(action_card(i, a, C["navy"], C["blue_lt"], S))
        els.append(Spacer(1, 4))

    els.append(PageBreak())

    # ── PAGE 7: CLOSING / NEXT STEPS ────────────────────────────────────────
    els.append(SectionBanner("Next Steps", "Your Path to Growth Starts Here"))
    els.append(Spacer(1, 16))

    els.append(Paragraph(f"What We Found for {brand.title()}", S["h1"]))
    els.append(Paragraph(
        f"This audit identified <b>{len(findings)} key opportunities</b> across "
        f"6 marketing dimensions. With a current score of <b>{int(score)}/100</b> "
        f"there is significant room to improve lead generation, conversion rates, "
        f"and competitive positioning. The 90-day roadmap above gives you a clear, "
        f"sequenced path forward.",
        S["body"]
    ))
    els.append(Spacer(1, 12))

    els.append(Paragraph("The 3 Most Important Actions Right Now", S["h2"]))
    els.append(Spacer(1, 6))
    for i, w in enumerate((qw or ["Improve homepage hero messaging"])[:3], 1):
        els.append(Paragraph(f"<b>{i}.</b>  {w}", S["bullet"]))
        els.append(Spacer(1, 4))

    els.append(Spacer(1, 28))

    # ── Services invitation page ──────────────────────────────────────────────
    from reportlab.platypus import PageBreak
    els.append(PageBreak())

    # Section header
    els.append(Spacer(1, 10))

    svc_title = (
        "هل تريد فريق متخصص ينفّذ هذه التحسينات بدلاً عنك؟"
        if lang == "ar" else
        "Want an Expert Team to Implement These Improvements for You?"
    )
    els.append(Paragraph(svc_title, ParagraphStyle(
        "SvcH", fontSize=18, fontName="Helvetica-Bold",
        textColor=C["navy"], alignment=TA_CENTER, spaceAfter=10, leading=26
    )))

    svc_sub = (
        "التقرير يكشف المشاكل — فريق PROVISION360 يحلّها ويقيس النتائج"
        if lang == "ar" else
        "The report reveals the problems — PROVISION360's team fixes them and tracks results"
    )
    els.append(Paragraph(svc_sub, ParagraphStyle(
        "SvcS", fontSize=11, fontName="Helvetica",
        textColor=C["slate"], alignment=TA_CENTER, spaceAfter=24, leading=18
    )))

    # Divider
    els.append(HRFlowable(width="100%", thickness=1, color=C["blue_lt"], spaceAfter=20))

    # Services grid — two columns
    if lang == "ar":
        services = [
            ("تحسين محركات البحث (SEO)",
             "بناء استراتيجية ظهور متكاملة: كلمات مفتاحية، روابط داخلية، بيانات منظّمة، وتقارير شهرية"),
            ("محتوى تسويقي احترافي",
             "كتابة صفحات المبيعات والمدونات والإعلانات بأسلوب يحوّل الزوار لعملاء"),
            ("تحسين سرعة الموقع",
             "تقنيات Core Web Vitals، ضغط الصور، التخزين المؤقت، وتقليل وقت التحميل"),
            ("تجربة المستخدم (UX)",
             "إعادة تصميم مسارات التحويل، صفحات الهبوط، والنماذج لزيادة معدل البيع"),
            ("إدارة الإعلانات المدفوعة",
             "حملات Google Ads وMeta Ads مدارة باحترافية مع تحسين مستمر للعائد"),
            ("تحليل البيانات والتقارير",
             "لوحات تحكم Google Analytics وSearch Console مع تقارير أداء شهرية واضحة"),
        ]
    else:
        services = [
            ("Search Engine Optimization (SEO)",
             "Full visibility strategy: keyword research, internal linking, structured data, and monthly reporting"),
            ("Professional Marketing Content",
             "Sales pages, blogs, and ad copy written to convert visitors into paying customers"),
            ("Website Speed Optimization",
             "Core Web Vitals improvements, image compression, caching, and load time reduction"),
            ("User Experience (UX) Design",
             "Redesigning conversion paths, landing pages, and forms to maximize sales rate"),
            ("Paid Advertising Management",
             "Google Ads and Meta Ads managed professionally with continuous ROI optimization"),
            ("Analytics & Performance Reports",
             "Google Analytics and Search Console dashboards with clear monthly performance reports"),
        ]

    svc_rows = []
    for i in range(0, len(services), 2):
        left  = services[i]
        right = services[i + 1] if i + 1 < len(services) else ("", "")

        def svc_cell(svc):
            if not svc[0]:
                return Paragraph("", S["body"])
            icon_map = {0: "01", 1: "02", 2: "03", 3: "04", 4: "05", 5: "06"}
            return Table([
                [Paragraph(f"<b>{svc[0]}</b>", ParagraphStyle(
                    "SN", fontSize=10, fontName="Helvetica-Bold",
                    textColor=C["navy"], spaceAfter=4
                ))],
                [Paragraph(svc[1], ParagraphStyle(
                    "SD", fontSize=8.5, fontName="Helvetica",
                    textColor=C["muted"] if "muted" in C else HexColor("#6B7280"),
                    leading=13, spaceAfter=0
                ))],
            ], colWidths=[200])

        svc_rows.append([svc_cell(left), svc_cell(right)])

    svc_table = Table(svc_rows, colWidths=[225, 225], hAlign="CENTER")
    svc_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), white),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [C["blue_lt"], white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, C["gray_bd"] if "gray_bd" in C else HexColor("#E5E7EB")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ROUNDEDCORNERS", [8], ),
    ]))
    els.append(svc_table)
    els.append(Spacer(1, 28))

    # Why PROVISION360 banner
    why_title = "لماذا PROVISION360؟" if lang == "ar" else "Why PROVISION360?"
    els.append(Paragraph(why_title, ParagraphStyle(
        "WhyH", fontSize=13, fontName="Helvetica-Bold",
        textColor=C["navy"], alignment=TA_CENTER, spaceAfter=16
    )))

    if lang == "ar":
        points = [
            ("خبرة متخصصة", "فريق متخصص في السوق السعودي والخليجي مع فهم عميق للمستهلك المحلي"),
            ("نتائج قابلة للقياس", "كل خدمة مرتبطة بمؤشرات أداء واضحة وتقارير شهرية شفافة"),
            ("تكامل كامل", "نجمع بين التقنية والمحتوى والتسويق في حلول متكاملة وليس خدمات منفصلة"),
            ("شراكة طويلة الأمد", "لسنا مجرد مقدمي خدمة — نحن شريكك في النمو الرقمي"),
        ]
    else:
        points = [
            ("Specialized Expertise", "A team specialized in Saudi and Gulf markets with deep local consumer insight"),
            ("Measurable Results", "Every service tied to clear KPIs with transparent monthly reporting"),
            ("Full Integration", "We combine tech, content, and marketing into unified solutions — not isolated services"),
            ("Long-Term Partnership", "We're not just a vendor — we're your digital growth partner"),
        ]

    why_rows = [[
        Paragraph(f"<b>{p[0]}</b><br/><font size='8' color='#6B7280'>{p[1]}</font>",
                  ParagraphStyle("WP", fontSize=9, fontName="Helvetica",
                                 textColor=C["navy"], leading=14, spaceAfter=0))
        for p in points[:2]
    ], [
        Paragraph(f"<b>{p[0]}</b><br/><font size='8' color='#6B7280'>{p[1]}</font>",
                  ParagraphStyle("WP2", fontSize=9, fontName="Helvetica",
                                 textColor=C["navy"], leading=14, spaceAfter=0))
        for p in points[2:]
    ]]

    why_table = Table(why_rows, colWidths=[225, 225], hAlign="CENTER")
    why_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C["blue_lt"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("GRID",          (0, 0), (-1, -1), 0.5, HexColor("#DDD6FE")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    els.append(why_table)
    els.append(Spacer(1, 28))

    # Final CTA box
    if lang == "ar":
        cta_lines = [
            ("تواصل معنا اليوم ونبدأ تحسين موقعك", 13, C["pink"]),
            ("نراجع تقريرك معك مجاناً ونضع خطة عمل مخصصة لموقعك", 9, white),
            ("info@provision360.net  |  +966 11 503 0388  |  provision360.net", 8.5, C["pink"]),
        ]
    else:
        cta_lines = [
            ("Contact Us Today and We'll Start Improving Your Website", 13, C["pink"]),
            ("We'll review your report with you for free and build a tailored action plan", 9, white),
            ("info@provision360.net  |  +966 11 503 0388  |  provision360.net", 8.5, C["pink"]),
        ]

    cta_cells = [[Paragraph(
        f'<font size="{sz}" color="#{hex_str(col)}"><b>{txt}</b></font>' if i == 0
        else f'<font size="{sz}" color="#{hex_str(col)}">{txt}</font>',
        ParagraphStyle(f"CTA{i}", fontName="Helvetica-Bold" if i == 0 else "Helvetica",
                       alignment=TA_CENTER, leading=18, spaceAfter=4)
    )] for i, (txt, sz, col) in enumerate(cta_lines)]

    cta_table = Table(cta_cells, colWidths=[455])
    cta_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C["navy"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("LEFTPADDING",   (0, 0), (-1, -1), 24),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 24),
        ("ROUNDEDCORNERS", [10]),
    ]))
    els.append(cta_table)
    els.append(Spacer(1, 20))

    els.append(Paragraph(
        f"Report prepared by PROVISION360  |  provision360.net  |  {date_str}  |  {url}",
        ParagraphStyle("Foot2", fontSize=7.5, fontName="Helvetica",
                       textColor=C["text_lt"], alignment=TA_CENTER)
    ))

    doc.build(els, onFirstPage=cover_cb, onLaterPages=later_cb)
    print(f"Report generated: {output_path}")
    return output_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf_report.py <data.json> [output.pdf]")
        sys.exit(0)

    input_file  = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "MARKETING-REPORT.pdf"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    generate_report(data, output_file)


if __name__ == "__main__":
    main()
