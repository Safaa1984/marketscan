"""
MarketScan — Flask Backend
Website marketing analysis SaaS: 10 SAR / report
Routes: landing page, checkout, payment webhook, PDF download
"""

import os
import sys
import json
import uuid
import hmac
import hashlib
from pathlib import Path
from datetime import datetime

from flask import (Flask, request, jsonify, send_file,
                   render_template_string, redirect, url_for, abort)

import stripe

# ── Bootstrap ─────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from config import (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY,
                    STRIPE_WEBHOOK_SECRET, REPORT_PRICE_SAR,
                    REPORT_CURRENCY, BASE_URL, SECRET_KEY)
from analyzer import analyze_url
from consultant_framer import frame_report

# Try importing the PDF generator from workspace scripts or global skills
PDF_SCRIPT = None
for candidate in [
    Path(__file__).parent.parent / "scripts" / "generate_pdf_report.py",
    Path.home() / ".claude" / "skills" / "market" / "scripts" / "generate_pdf_report.py",
]:
    if candidate.exists():
        PDF_SCRIPT = candidate
        break

if PDF_SCRIPT:
    import importlib.util
    spec = importlib.util.spec_from_file_location("pdf_gen", PDF_SCRIPT)
    pdf_mod = importlib.util.load_from_spec(spec) if hasattr(importlib.util, "load_from_spec") else None
    # Fallback: direct import via exec
    _ns = {}
    exec(open(PDF_SCRIPT).read(), _ns)
    generate_pdf = _ns.get("generate_report")
else:
    generate_pdf = None

stripe.api_key = STRIPE_SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── Storage (in-memory for MVP; swap for SQLite/Redis in production) ──────────
ORDERS: dict[str, dict] = {}   # token → order info
PDFS:   dict[str, Path] = {}   # token → PDF path

PDF_DIR = Path(__file__).parent / "generated_pdfs"
PDF_DIR.mkdir(exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_token() -> str:
    return uuid.uuid4().hex


def _generate_and_store(token: str):
    """Run analysis + framing + PDF generation for an order."""
    order = ORDERS.get(token)
    if not order or order.get("pdf_ready"):
        return

    url  = order["url"]
    lang = order.get("lang", "ar")

    try:
        analysis    = analyze_url(url)
        report_data = frame_report(analysis, lang)

        out_path = PDF_DIR / f"report_{token}.pdf"
        if generate_pdf:
            generate_pdf(report_data, str(out_path))
        else:
            # Fallback: write JSON so the user can manually generate
            out_path = PDF_DIR / f"report_{token}.json"
            out_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2),
                                encoding="utf-8")

        PDFS[token]           = out_path
        order["pdf_ready"]    = True
        order["pdf_path"]     = str(out_path)
        order["generated_at"] = datetime.now().isoformat()
    except Exception as e:
        order["error"] = str(e)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def landing():
    with open(Path(__file__).parent / "static" / "index.html", encoding="utf-8") as f:
        return f.read()


@app.route("/api/checkout", methods=["POST"])
def create_checkout():
    data  = request.get_json(force=True)
    url   = (data.get("url") or "").strip()
    email = (data.get("email") or "").strip()
    lang  = data.get("lang", "ar")

    if not url or not email:
        return jsonify({"error": "URL and email are required"}), 400

    token = make_token()
    ORDERS[token] = {
        "url":       url,
        "email":     email,
        "lang":      lang,
        "token":     token,
        "paid":      False,
        "pdf_ready": False,
        "created_at": datetime.now().isoformat(),
    }

    product_name = (
        "تقرير تحليل تسويقي احترافي" if lang == "ar"
        else "Professional Marketing Audit Report"
    )

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency":     REPORT_CURRENCY,
                    "unit_amount":  REPORT_PRICE_SAR,
                    "product_data": {
                        "name": product_name,
                        "description": url,
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=email,
            success_url=f"{BASE_URL}/success?token={token}",
            cancel_url=f"{BASE_URL}/?cancelled=1",
            metadata={"token": token},
        )
        return jsonify({"checkout_url": session.url})
    except stripe.StripeError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/success")
def success():
    token = request.args.get("token", "")
    order = ORDERS.get(token)

    if not order:
        return redirect("/?error=invalid_token")

    # Mark paid (in production, verify via webhook instead)
    order["paid"] = True

    # Generate PDF
    _generate_and_store(token)

    lang = order.get("lang", "ar")
    if lang == "ar":
        title    = "تقريرك جاهز! 🎉"
        subtitle = f"تم تحليل موقع {order['url']} وإعداد تقريرك الاحترافي."
        btn_text = "تحميل التقرير PDF ⬇️"
        note     = "سيُفتح الملف في نافذة جديدة. يمكنك حفظه أو طباعته."
    else:
        title    = "Your Report is Ready! 🎉"
        subtitle = f"{order['url']} has been analysed and your professional report is ready."
        btn_text = "Download PDF Report ⬇️"
        note     = "The file will open in a new tab. You can save or print it."

    status = "✅ جاهز" if order.get("pdf_ready") else "⏳ يُعالَج..."
    if lang == "en":
        status = "✅ Ready" if order.get("pdf_ready") else "⏳ Processing..."

    return render_template_string(SUCCESS_HTML,
        title=title, subtitle=subtitle, btn_text=btn_text,
        note=note, token=token, status=status, lang=lang)


@app.route("/download/<token>")
def download(token):
    order = ORDERS.get(token)
    if not order or not order.get("paid"):
        abort(403)

    if not order.get("pdf_ready"):
        _generate_and_store(token)

    pdf_path = PDFS.get(token)
    if not pdf_path or not pdf_path.exists():
        abort(404)

    domain   = order["url"].replace("https://","").replace("http://","").split("/")[0]
    filename = f"MarketScan-{domain}.pdf"
    return send_file(pdf_path, as_attachment=True, download_name=filename)


@app.route("/api/status/<token>")
def status(token):
    order = ORDERS.get(token)
    if not order:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "paid":      order.get("paid"),
        "pdf_ready": order.get("pdf_ready"),
        "error":     order.get("error"),
    })


@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig     = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return jsonify({"error": "invalid signature"}), 400

    if event["type"] == "checkout.session.completed":
        token = event["data"]["object"]["metadata"].get("token")
        if token and token in ORDERS:
            ORDERS[token]["paid"] = True
            _generate_and_store(token)

    return jsonify({"ok": True})


# ── Demo endpoint (no payment) ────────────────────────────────────────────────

@app.route("/demo")
def demo():
    url  = request.args.get("url", "https://provision360.net/")
    lang = request.args.get("lang", "ar")
    token = make_token()
    ORDERS[token] = {"url": url, "email": "demo@demo.com",
                     "lang": lang, "token": token,
                     "paid": True, "pdf_ready": False,
                     "created_at": datetime.now().isoformat()}
    _generate_and_store(token)
    return redirect(f"/download/{token}")


# ── Inline HTML templates ─────────────────────────────────────────────────────

SUCCESS_HTML = """<!DOCTYPE html>
<html lang="{{ lang }}" dir="{{ 'rtl' if lang == 'ar' else 'ltr' }}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<style>
  body{margin:0;font-family:system-ui,sans-serif;background:#0F1E3C;
       color:white;display:flex;align-items:center;justify-content:center;
       min-height:100vh;text-align:center;padding:20px}
  .card{background:#1A2F55;border-radius:16px;padding:48px 40px;
        max-width:480px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.4)}
  h1{font-size:2rem;margin-bottom:12px;color:#F05A28}
  p{color:#94A3B8;font-size:1rem;margin-bottom:8px}
  .status{background:#0E9F6E22;border:1px solid #0E9F6E;border-radius:8px;
          padding:10px 16px;margin:20px 0;font-size:.9rem;color:#0E9F6E}
  .btn{display:inline-block;background:#F05A28;color:white;padding:16px 36px;
       border-radius:10px;text-decoration:none;font-size:1.1rem;font-weight:700;
       margin-top:24px;transition:opacity .2s}
  .btn:hover{opacity:.85}
  .note{color:#64748B;font-size:.8rem;margin-top:16px}
</style>
</head>
<body>
<div class="card">
  <div style="font-size:3rem">🎉</div>
  <h1>{{ title }}</h1>
  <p>{{ subtitle }}</p>
  <div class="status">{{ status }}</div>
  <a class="btn" href="/download/{{ token }}">{{ btn_text }}</a>
  <p class="note">{{ note }}</p>
</div>
</body>
</html>"""


if __name__ == "__main__":
    print("🚀 MarketScan running on http://localhost:5000")
    app.run(debug=True, port=5000)
