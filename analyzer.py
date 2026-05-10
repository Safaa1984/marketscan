"""
Website Analyzer — scrapes a URL and returns structured marketing data.
Detects: location, industry, language, CTAs, SEO, trust signals.
"""

import re
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Location detection ────────────────────────────────────────────────────────

PHONE_PATTERNS = {
    "Saudi Arabia": r"(\+966|00966|0?(5[0-9])\d{7})",
    "UAE":          r"(\+971|00971|0?(5[0-9])\d{7})",
    "Kuwait":       r"(\+965|00965)",
    "Qatar":        r"(\+974|00974)",
    "Bahrain":      r"(\+973|00973)",
    "Jordan":       r"(\+962|00962)",
    "Egypt":        r"(\+20|0020)",
    "Iraq":         r"(\+964|00964)",
}

CURRENCY_PATTERNS = {
    "Saudi Arabia": r"(ريال|SAR|SR\b|رس\b)",
    "UAE":          r"(درهم|AED|دراهم)",
    "Kuwait":       r"(دينار كويتي|KWD)",
    "Qatar":        r"(ريال قطري|QAR)",
    "Egypt":        r"(جنيه|EGP)",
}

INDUSTRY_KEYWORDS = {
    "restaurant":   ["مطعم","restaurant","food","طعام","وجبة","menu","قائمة","توصيل","delivery"],
    "real_estate":  ["عقار","real estate","property","villa","شقة","apartment","للبيع","للإيجار","lease"],
    "ecommerce":    ["تسوق","shop","store","cart","checkout","منتج","product","buy","اشتر"],
    "healthcare":   ["clinic","عيادة","hospital","مستشفى","doctor","طبيب","health","صحة","appointment"],
    "education":    ["دورة","course","academy","أكاديمية","training","تدريب","school","مدرسة","learn"],
    "agency":       ["agency","وكالة","marketing","تسويق","branding","design","تصميم","digital"],
    "hotel":        ["hotel","فندق","resort","منتجع","booking","حجز","accommodation","إقامة"],
    "gym":          ["gym","صالة","fitness","لياقة","workout","تمرين","sports","رياضة"],
}

LOCAL_MARKET_TIPS = {
    "Saudi Arabia": {
        "ar": [
            "🇸🇦 التسويق عبر سناب شات ضروري — المملكة من أعلى الدول استخداماً له",
            "📱 تحسين ظهورك في Google Maps أولوية لأن 73% من البحث محلي",
            "🕌 خصص محتواك لمواسم رمضان والحج والأعياد الوطنية",
            "💳 أضف MADA و Apple Pay — 68% من العمليات بدون نقد",
            "🌙 تذكر: أوقات الذروة للجمهور السعودي 9م-2ص",
        ],
        "en": [
            "🇸🇦 Snapchat marketing is essential — Saudi Arabia is top globally in usage",
            "📱 Google Maps optimisation is priority — 73% of searches are local",
            "🕌 Customise content for Ramadan, Hajj, and National Day seasons",
            "💳 Add MADA and Apple Pay — 68% of transactions are cashless",
            "🌙 Peak audience hours in Saudi: 9PM–2AM",
        ],
    },
    "UAE": {
        "ar": [
            "🇦🇪 إنستقرام وتيك توك الأقوى في الإمارات — استثمر فيهما",
            "🌍 محتواك يجب أن يخاطب جنسيات متعددة (عربي + إنجليزي)",
            "💰 العملاء الإماراتيون يقدّرون الفخامة — أظهر القيمة وليس السعر فقط",
            "📍 تواجدك في Google Business Profile مهم جداً في دبي وأبوظبي",
        ],
        "en": [
            "🇦🇪 Instagram and TikTok dominate in UAE — invest heavily here",
            "🌍 Address multiple nationalities in your content (Arabic + English)",
            "💰 UAE customers value luxury — show value, not just price",
            "📍 Google Business Profile is critical in Dubai and Abu Dhabi",
        ],
    },
    "default": {
        "ar": [
            "🌍 تحسين تجربة المستخدم على الجوال ضروري في منطقتك",
            "📊 ابدأ بـ Google Analytics لفهم سلوك زوارك",
            "🤝 التسويق بالتوصيات يبني ثقة أسرع في الأسواق العربية",
        ],
        "en": [
            "🌍 Mobile UX optimisation is critical for your region",
            "📊 Start with Google Analytics to understand visitor behaviour",
            "🤝 Referral marketing builds trust faster in Arab markets",
        ],
    },
}


def detect_location(text: str) -> str:
    for country, pattern in PHONE_PATTERNS.items():
        if re.search(pattern, text):
            return country
    for country, pattern in CURRENCY_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return country
    return "default"


def detect_industry(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        scores[industry] = sum(1 for kw in keywords if kw.lower() in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "agency"


def detect_language(text: str) -> str:
    arabic_chars = len(re.findall(r"[؀-ۿ]", text))
    total = max(len(text.strip()), 1)
    return "ar" if arabic_chars / total > 0.15 else "en"


def score_item(condition: bool, weight: int = 10) -> int:
    return weight if condition else 0


def analyze_url(url: str) -> dict:
    """Scrape URL and return structured analysis data."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        html = resp.text
    except Exception as e:
        return {"error": str(e), "url": url}

    soup = BeautifulSoup(html, "lxml")
    text_content = soup.get_text(" ", strip=True)
    domain = urlparse(url).netloc.replace("www.", "")
    brand  = domain.split(".")[0].capitalize()

    # ── Basic metadata ───────────────────────────────────────────────────────
    title      = soup.title.string.strip() if soup.title else ""
    meta_desc  = ""
    meta_tag   = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "").strip()

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")][:5]

    # ── CTAs ─────────────────────────────────────────────────────────────────
    cta_keywords_en = ["get started","contact","book","schedule","free","try","buy","sign up","request"]
    cta_keywords_ar = ["تواصل","احجز","ابدأ","اطلب","جرب","سجل","اشتر","اكتشف"]
    all_links  = soup.find_all("a", href=True)
    all_btns   = soup.find_all(["button", "a"])
    cta_texts  = [el.get_text(strip=True).lower() for el in all_btns if el.get_text(strip=True)]
    has_cta    = any(kw in t for t in cta_texts
                     for kw in cta_keywords_en + cta_keywords_ar)

    # ── Images ───────────────────────────────────────────────────────────────
    images     = soup.find_all("img")
    imgs_total = len(images)
    imgs_no_alt= sum(1 for img in images if not img.get("alt", "").strip())

    # ── Social proof ─────────────────────────────────────────────────────────
    proof_keywords = ["testimonial","review","client","عميل","تقييم","شهادة","نجاح","success story"]
    has_social_proof = any(kw in text_content.lower() for kw in proof_keywords)

    # ── Contact ──────────────────────────────────────────────────────────────
    has_phone  = bool(re.search(r"\+?\d[\d\s\-]{8,14}\d", text_content))
    has_email  = bool(re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text_content))
    has_whatsapp = "whatsapp" in text_content.lower() or "واتساب" in text_content

    # ── Social media ─────────────────────────────────────────────────────────
    social_links = {
        "instagram": any("instagram.com" in (a.get("href","")) for a in all_links),
        "twitter":   any("twitter.com" in (a.get("href","")) or "x.com" in (a.get("href","")) for a in all_links),
        "facebook":  any("facebook.com" in (a.get("href","")) for a in all_links),
        "linkedin":  any("linkedin.com" in (a.get("href","")) for a in all_links),
        "snapchat":  any("snapchat.com" in (a.get("href","")) for a in all_links),
        "tiktok":    any("tiktok.com" in (a.get("href","")) for a in all_links),
        "youtube":   any("youtube.com" in (a.get("href","")) for a in all_links),
    }
    social_count = sum(social_links.values())

    # ── SEO basics ───────────────────────────────────────────────────────────
    title_ok    = 20 < len(title) < 70
    meta_ok     = 50 < len(meta_desc) < 160
    has_h1      = len(h1_tags) == 1
    h1_generic  = h1_tags[0].lower() in ["home","الرئيسية","welcome","مرحباً","مرحبا"] if h1_tags else True

    # ── Schema / structured data ──────────────────────────────────────────────
    has_schema  = bool(soup.find("script", attrs={"type":"application/ld+json"}))

    # ── Mobile ────────────────────────────────────────────────────────────────
    viewport    = soup.find("meta", attrs={"name":"viewport"})
    has_viewport= bool(viewport)

    # ── HTTPS ─────────────────────────────────────────────────────────────────
    is_https    = url.startswith("https://")

    # ── Location / industry / language ───────────────────────────────────────
    location    = detect_location(text_content)
    industry    = detect_industry(text_content)
    lang        = detect_language(text_content)

    # ── Score categories ──────────────────────────────────────────────────────
    content_score = (
        score_item(len(h1_tags) > 0, 20) +
        score_item(not h1_generic, 20) +
        score_item(len(meta_desc) > 50, 15) +
        score_item(has_cta, 25) +
        score_item(has_social_proof, 20)
    )

    conversion_score = (
        score_item(has_cta, 30) +
        score_item(has_social_proof, 25) +
        score_item(has_phone or has_whatsapp, 20) +
        score_item(has_email, 15) +
        score_item(social_count >= 2, 10)
    )

    seo_score = (
        score_item(title_ok, 25) +
        score_item(meta_ok, 25) +
        score_item(has_h1 and not h1_generic, 20) +
        score_item(imgs_no_alt == 0 or imgs_total == 0, 15) +
        score_item(has_schema, 10) +
        score_item(is_https, 5)
    )

    brand_score = (
        score_item(has_social_proof, 30) +
        score_item(social_count >= 2, 25) +
        score_item(is_https, 20) +
        score_item(has_viewport, 25)
    )

    competitive_score = (
        score_item(has_social_proof, 35) +
        score_item(has_cta, 25) +
        score_item(social_count >= 3, 20) +
        score_item(not h1_generic, 20)
    )

    growth_score = (
        score_item(social_count >= 3, 30) +
        score_item(has_email, 20) +
        score_item(has_whatsapp, 25) +
        score_item(has_schema, 25)
    )

    overall = round(
        content_score * 0.25 +
        conversion_score * 0.20 +
        seo_score * 0.20 +
        competitive_score * 0.15 +
        brand_score * 0.10 +
        growth_score * 0.10
    )

    return {
        "url":        url,
        "domain":     domain,
        "brand_name": brand,
        "date":       datetime.now().strftime("%B %d, %Y"),
        "date_ar":    _arabic_date(),
        "language":   lang,
        "location":   location,
        "industry":   industry,
        "overall_score": overall,
        "categories": {
            "Content & Messaging":    {"score": content_score,    "weight": "25%"},
            "Conversion Optimization":{"score": conversion_score, "weight": "20%"},
            "SEO & Discoverability":  {"score": seo_score,        "weight": "20%"},
            "Competitive Positioning":{"score": competitive_score,"weight": "15%"},
            "Brand & Trust":          {"score": brand_score,      "weight": "10%"},
            "Growth & Strategy":      {"score": growth_score,     "weight": "10%"},
        },
        "raw": {
            "title":         title,
            "meta_desc":     meta_desc,
            "h1":            h1_tags,
            "h2":            h2_tags,
            "has_cta":       has_cta,
            "cta_texts":     cta_texts[:5],
            "has_social_proof": has_social_proof,
            "has_phone":     has_phone,
            "has_whatsapp":  has_whatsapp,
            "has_email":     has_email,
            "social_links":  social_links,
            "social_count":  social_count,
            "imgs_total":    imgs_total,
            "imgs_no_alt":   imgs_no_alt,
            "has_schema":    has_schema,
            "has_viewport":  has_viewport,
            "is_https":      is_https,
            "title_ok":      title_ok,
            "meta_ok":       meta_ok,
            "h1_generic":    h1_generic,
        },
        "local_tips": LOCAL_MARKET_TIPS.get(location, LOCAL_MARKET_TIPS["default"]),
    }


def _arabic_date() -> str:
    months = {
        1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
        7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
    }
    now = datetime.now()
    return f"{now.day} {months[now.month]} {now.year}"
