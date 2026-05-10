#!/usr/bin/env python3
"""
Simple 1-page preview report — free demo tier.
Shows overall score + top 3 issues + upgrade CTA.
Requires: reportlab
"""

from pathlib import Path
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdfcanvas
except ImportError:
    raise ImportError("pip install reportlab")

W, H = A4

C = {
    "navy":   HexColor("#1A1464"),
    "blue":   HexColor("#4B35C8"),
    "pink":   HexColor("#C87DB8"),
    "green":  HexColor("#0E9F6E"),
    "yellow": HexColor("#D97706"),
    "red":    HexColor("#DC2626"),
    "slate":  HexColor("#94A3B8"),
    "light":  HexColor("#F3F0FF"),
    "gray":   HexColor("#F9FAFB"),
    "border": HexColor("#E5E7EB"),
    "text":   HexColor("#111827"),
    "muted":  HexColor("#6B7280"),
}


def score_color(s):
    if s >= 70: return C["green"]
    if s >= 45: return C["yellow"]
    return C["red"]


def score_label(s, lang):
    if lang == "ar":
        if s >= 70: return "جيد"
        if s >= 45: return "متوسط"
        return "ضعيف"
    else:
        if s >= 70: return "Good"
        if s >= 45: return "Average"
        return "Weak"


def draw_gauge(c, cx, cy, r, score):
    import math
    col = score_color(score)
    # Background arc
    c.setStrokeColor(C["border"])
    c.setLineWidth(8)
    c.arc(cx - r, cy - r, cx + r, cy + r, 0, 360)
    # Score arc (portion)
    c.setStrokeColor(col)
    c.setLineWidth(8)
    angle = score / 100 * 360
    c.arc(cx - r, cy - r, cx + r, cy + r, 90, 90 - angle)
    # Center score
    c.setFillColor(col)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(cx, cy + 5, str(int(score)))
    c.setFillColor(C["muted"])
    c.setFont("Helvetica", 9)
    c.drawCentredString(cx, cy - 10, "/ 100")


def generate_simple_report(report_data: dict, output_path: str):
    url   = report_data.get("url", "")
    lang  = report_data.get("lang", "ar")
    score = float(report_data.get("score", 50))
    findings = report_data.get("findings", [])[:3]
    date_str = datetime.now().strftime("%Y-%m-%d")
    ar = lang == "ar"

    c = pdfcanvas.Canvas(output_path, pagesize=A4)
    c.setTitle("MarketScan Preview — ProVision360")

    # ── Background ──────────────────────────────────────────────────────────
    c.setFillColor(C["gray"])
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Header strip ────────────────────────────────────────────────────────
    c.setFillColor(C["navy"])
    c.rect(0, H - 72, W, 72, fill=1, stroke=0)
    # Gradient accent line
    c.setFillColor(C["blue"])
    c.rect(0, H - 75, W * 0.55, 3, fill=1, stroke=0)
    c.setFillColor(C["pink"])
    c.rect(W * 0.55, H - 75, W * 0.45, 3, fill=1, stroke=0)

    # Logo
    logo = Path(__file__).parent / "static" / "logo.png"
    if logo.exists():
        c.drawImage(str(logo), 40, H - 62, width=90, height=28,
                    preserveAspectRatio=True, mask="auto")
    else:
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, H - 48, "PROVISION360")

    # Header right text
    c.setFillColor(C["pink"])
    c.setFont("Helvetica-Bold", 8)
    label = "تقرير تسويقي — نسخة مجانية" if ar else "Marketing Report — Free Preview"
    c.drawRightString(W - 40, H - 38, label)
    c.setFillColor(C["slate"])
    c.setFont("Helvetica", 7)
    c.drawRightString(W - 40, H - 52, date_str)

    y = H - 100

    # ── Title block ─────────────────────────────────────────────────────────
    c.setFillColor(white)
    c.roundRect(30, y - 70, W - 60, 82, 10, fill=1, stroke=0)
    c.setFillColor(C["navy"])
    c.setFont("Helvetica-Bold", 15)
    title = "ملخص تحليل موقعك التسويقي" if ar else "Your Website Marketing Analysis"
    c.drawCentredString(W / 2, y - 20, title)
    c.setFillColor(C["muted"])
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, y - 38, url)
    c.setFillColor(C["border"])
    c.rect(40, y - 52, W - 80, 0.5, fill=1, stroke=0)
    c.setFillColor(C["slate"])
    c.setFont("Helvetica", 7.5)
    note = "هذه نسخة مجانية · اشترِ التقرير الكامل للحصول على خطة عمل متكاملة من 7 صفحات" if ar \
           else "Free preview · Purchase the full report for a complete 7-page action plan"
    c.drawCentredString(W / 2, y - 65, note)

    y -= 90

    # ── Score card ──────────────────────────────────────────────────────────
    card_w = 140
    cx = W / 2
    c.setFillColor(white)
    c.roundRect(cx - card_w / 2, y - 130, card_w, 130, 10, fill=1, stroke=0)

    lbl = "التقييم العام" if ar else "Overall Score"
    c.setFillColor(C["navy"])
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx, y - 18, lbl)

    draw_gauge(c, cx, y - 78, 42, score)

    sc_lbl = score_label(score, lang)
    sc_col = score_color(score)
    c.setFillColor(sc_col)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx, y - 108, sc_lbl)

    y -= 148

    # ── Top findings ─────────────────────────────────────────────────────────
    sec_title = "أبرز 3 مشاكل وجدناها في موقعك" if ar else "Top 3 Issues Found on Your Website"
    c.setFillColor(C["navy"])
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, y - 14, sec_title)
    y -= 30

    icons = ["🔴", "🟡", "🔵"]
    priorities = (
        ["عاجل", "مهم", "للتحسين"] if ar
        else ["Urgent", "Important", "Improve"]
    )
    pri_colors = [C["red"], C["yellow"], C["blue"]]

    if not findings:
        findings = [
            {"title": "لا توجد بيانات كافية" if ar else "Insufficient data",
             "detail": "" , "impact": "medium"}
        ]

    for i, f in enumerate(findings[:3]):
        fh = 72
        c.setFillColor(white)
        c.roundRect(30, y - fh, W - 60, fh, 8, fill=1, stroke=0)

        # Priority tag
        tag_col = pri_colors[i]
        c.setFillColor(tag_col)
        tag_w = 52
        if ar:
            c.roundRect(W - 30 - tag_w - 10, y - 22, tag_w, 16, 4, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(W - 30 - tag_w / 2 - 10, y - 14, priorities[i])
        else:
            c.roundRect(40, y - 22, tag_w, 16, 4, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(40 + tag_w / 2, y - 14, priorities[i])

        # Title
        title_txt = f.get("title", "")
        c.setFillColor(C["text"])
        c.setFont("Helvetica-Bold", 10)
        if ar:
            c.drawRightString(W - 30 - tag_w - 16, y - 30, title_txt[:55])
        else:
            c.drawString(40 + tag_w + 10, y - 30, title_txt[:55])

        # Detail (blurred / teaser)
        detail = f.get("detail", "")
        if detail:
            teaser = detail[:60] + "..." if len(detail) > 60 else detail
        else:
            teaser = ("احصل على التقرير الكامل لرؤية التفاصيل والحل" if ar
                      else "Get the full report to see details and solution")
        c.setFillColor(C["muted"])
        c.setFont("Helvetica", 8)
        if ar:
            c.drawRightString(W - 40, y - 48, teaser[:70])
        else:
            c.drawString(42, y - 48, teaser[:70])

        # Lock icon hint
        c.setFillColor(C["border"])
        c.setFont("Helvetica", 7)
        lock = "🔒 الحل التفصيلي متاح في التقرير الكامل" if ar else "🔒 Detailed solution in full report"
        c.drawCentredString(W / 2, y - 62, lock)

        y -= fh + 10

    # ── CTA upgrade banner ───────────────────────────────────────────────────
    y -= 8
    banner_h = 88
    # Gradient simulation with two rects
    c.setFillColor(C["navy"])
    c.roundRect(30, y - banner_h, W - 60, banner_h, 12, fill=1, stroke=0)
    c.setFillColor(C["blue"])
    c.roundRect(W / 2, y - banner_h, W / 2 - 30, banner_h, 12, fill=1, stroke=0)
    # Re-cover seam
    c.setFillColor(C["blue"])
    c.rect(W / 2, y - banner_h, 12, banner_h, fill=1, stroke=0)
    c.setFillColor(C["navy"])
    c.roundRect(30, y - banner_h, W - 60, banner_h, 12, fill=1, stroke=0)
    # Overlay pink tint right
    c.setFillColor(HexColor("#3D2DA8"))
    c.roundRect(W * 0.5, y - banner_h, W * 0.5 - 30, banner_h, 12, fill=1, stroke=0)
    c.rect(W * 0.5, y - banner_h, 12, banner_h, fill=1, stroke=0)

    if ar:
        c.setFillColor(C["pink"])
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(W - 50, y - 22, "🚀 احصل على التقرير الكامل — 9 ريال فقط")
        c.setFillColor(white)
        c.setFont("Helvetica", 8.5)
        c.drawRightString(W - 50, y - 38, "7 صفحات · تحليل SEO كامل · خطة عمل مرحلية · مقارنة المنافسين")
        c.drawRightString(W - 50, y - 52, "توقعات ROI · أسرع 10 إجراءات · تقرير PDF احترافي")
        c.setFillColor(C["pink"])
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(W - 50, y - 70, "provision360.net/scan  ←")
    else:
        c.setFillColor(C["pink"])
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y - 22, "🚀 Get the Full Report — Only 9 SAR")
        c.setFillColor(white)
        c.setFont("Helvetica", 8.5)
        c.drawString(50, y - 38, "7 pages · Full SEO audit · Phased action plan · Competitor benchmark")
        c.drawString(50, y - 52, "ROI projections · Top 10 quick wins · Professional PDF")
        c.setFillColor(C["pink"])
        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y - 70, "→  provision360.net/scan")

    # ── Footer ───────────────────────────────────────────────────────────────
    c.setFillColor(C["border"])
    c.rect(30, 18, W - 60, 0.5, fill=1, stroke=0)
    c.setFillColor(C["slate"])
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, 8, f"© 2026 PROVISION360  ·  provision360.net  ·  info@provision360.net")

    c.save()
