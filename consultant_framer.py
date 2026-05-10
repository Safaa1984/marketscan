"""
Business Consultant Framer
Transforms raw audit data into executive-level business language.
Revenue Leaks · Growth Blockers · Market Opportunities — not "problems".
"""

from analyzer import LOCAL_MARKET_TIPS

# ── Industry-specific insights ────────────────────────────────────────────────

INDUSTRY_INSIGHTS = {
    "restaurant": {
        "ar": {
            "exec_intro": "في قطاع المطاعم، القرار يُتخذ خلال 8 ثوان من رؤية موقعك. كل ثانية إضافية تكلفك طاولة محجوزة.",
            "quick_wins_extra": [
                "أضف زر 'احجز طاولة' أو 'اطلب الآن' في أعلى الصفحة مباشرةً",
                "ارفع صور الأطباق بجودة عالية — الصور تزيد الطلبات 30%",
                "فعّل Google Business Profile وأضف قائمة طعام محدّثة",
            ],
        },
        "en": {
            "exec_intro": "In the restaurant sector, decisions are made within 8 seconds of seeing your site. Every extra second costs you a reservation.",
            "quick_wins_extra": [
                "Add 'Book a Table' or 'Order Now' button at top of page",
                "Upload high-quality food photography — images increase orders by 30%",
                "Activate Google Business Profile with updated menu",
            ],
        },
    },
    "real_estate": {
        "ar": {
            "exec_intro": "في العقارات، الثقة تُباع قبل العقار. موقعك هو معرض عقاراتك — يجب أن يُقنع ويُلهم.",
            "quick_wins_extra": [
                "أضف جولات افتراضية أو فيديو للعقارات — يرفع التواصل 40%",
                "أظهر شهادات المشترين السابقين بالاسم والصورة",
                "أضف حاسبة تمويل عقاري مجانية كـ lead magnet",
            ],
        },
        "en": {
            "exec_intro": "In real estate, trust is sold before the property. Your site is your showroom — it must convince and inspire.",
            "quick_wins_extra": [
                "Add virtual tours or property video — increases inquiries by 40%",
                "Show past buyer testimonials with name and photo",
                "Add a free mortgage calculator as a lead magnet",
            ],
        },
    },
    "ecommerce": {
        "ar": {
            "exec_intro": "69% من عربات التسوق تُترك قبل الدفع. موقعك لديه نقاط تسرب مباشرة تحوّل الزوار إلى مشترين لدى منافسيك.",
            "quick_wins_extra": [
                "أضف 'مؤشر الثقة' بجانب زر الشراء: SSL + سياسة إرجاع واضحة",
                "فعّل إشعار 'X شخص يشاهد هذا المنتج الآن' لخلق urgency",
                "أرسل بريد استرداد عربة التسوق خلال ساعة من الترك",
            ],
        },
        "en": {
            "exec_intro": "69% of shopping carts are abandoned before payment. Your site has direct revenue leaks turning visitors into your competitors' customers.",
            "quick_wins_extra": [
                "Add trust indicators next to buy button: SSL badge + clear return policy",
                "Enable 'X people viewing this product' urgency notification",
                "Send cart recovery email within 1 hour of abandonment",
            ],
        },
    },
    "healthcare": {
        "ar": {
            "exec_intro": "مريضك يبحث عنك في لحظة ضعف — موقعك يجب أن يبث الطمأنينة والثقة فوراً قبل أن يذهب إلى منافس.",
            "quick_wins_extra": [
                "أضف نظام حجز مواعيد إلكتروني — يقلل المكالمات 60% ويرفع الحجوزات",
                "أظهر شهادات المرضى ونتائج العلاج (مع الحفاظ على الخصوصية)",
                "أضف FAQ للأسئلة الشائعة — يبني ثقة ويحسن SEO",
            ],
        },
        "en": {
            "exec_intro": "Your patient searches for you in a moment of vulnerability — your site must radiate trust immediately before they go to a competitor.",
            "quick_wins_extra": [
                "Add online appointment booking — reduces calls 60% and increases bookings",
                "Show patient testimonials and treatment outcomes (privacy-compliant)",
                "Add FAQ section — builds trust and improves SEO",
            ],
        },
    },
    "agency": {
        "ar": {
            "exec_intro": "عميلك يحكم على جودتك التسويقية من خلال موقعك. إذا كان موقعك ضعيف، فكيف يثق أن تسويقه سيكون قوياً؟",
            "quick_wins_extra": [
                "أضف 3 دراسات حالة مع أرقام نتائج حقيقية (مثال: رفعنا المبيعات 3×)",
                "أنشئ 'حاسبة ROI مجانية' كـ lead magnet لجذب العملاء",
                "أضف زر 'استشارة مجانية 30 دقيقة' — يُحوّل الزوار لمبيعات مباشرة",
            ],
        },
        "en": {
            "exec_intro": "Your client judges your marketing quality through your website. If it's weak, how can they trust you with their marketing?",
            "quick_wins_extra": [
                "Add 3 case studies with real result numbers (e.g., 'We grew sales 3×')",
                "Create a free 'ROI Calculator' as a lead magnet",
                "Add 'Free 30-min Consultation' button — converts visitors to direct sales",
            ],
        },
    },
}

# Default
INDUSTRY_INSIGHTS["education"] = INDUSTRY_INSIGHTS["agency"]
INDUSTRY_INSIGHTS["hotel"]     = INDUSTRY_INSIGHTS["restaurant"]
INDUSTRY_INSIGHTS["gym"]       = INDUSTRY_INSIGHTS["healthcare"]
INDUSTRY_INSIGHTS["default"]   = INDUSTRY_INSIGHTS["agency"]

# ── Finding templates ─────────────────────────────────────────────────────────

def build_findings(raw: dict, lang: str) -> list:
    findings = []

    if lang == "ar":
        if raw.get("h1_generic") or not raw.get("h1"):
            findings.append({
                "severity": "Critical",
                "finding": "💸 تسرب إيراداتي: العنوان الرئيسي في صفحتك لا يخبر الزائر لماذا يختارك. كل زائر يغادر خلال 5 ثوان = عميل محتمل مفقود إلى الأبد.",
            })

        if not raw.get("has_cta"):
            findings.append({
                "severity": "Critical",
                "finding": "🚫 حاجز التحويل: لا يوجد زر واضح للتواصل أو الحجز. زوارك مهتمون لكن لا يعرفون ماذا يفعلون — فيغادرون.",
            })

        if not raw.get("has_social_proof"):
            findings.append({
                "severity": "High",
                "finding": "⚠️ فجوة الثقة: لا يوجد آراء عملاء أو نتائج مثبتة. 92% من المشترين يحتاجون مراجعة قبل القرار.",
            })

        if raw.get("imgs_no_alt", 0) > 2:
            findings.append({
                "severity": "High",
                "finding": f"🔍 خسارة مرئية في البحث: {raw['imgs_no_alt']} صورة بلا وصف نصي — محركات البحث تتجاهلها وتفقد موقعك ترتيباً في Google.",
            })

        if not raw.get("meta_ok"):
            findings.append({
                "severity": "High",
                "finding": "📉 فرصة بحثية ضائعة: وصف الصفحة في Google غير محسّن — معدل النقر على نتيجتك أقل 40% مما يجب.",
            })

        if raw.get("social_count", 0) < 2:
            findings.append({
                "severity": "Medium",
                "finding": "📱 غياب في وسائل التواصل: قنوات التواصل الاجتماعي غير متكاملة مع الموقع — تفقد جمهوراً يبحث عنك يومياً.",
            })

        if not raw.get("has_whatsapp"):
            findings.append({
                "severity": "Medium",
                "finding": "💬 تسرب التواصل: لا يوجد زر واتساب مباشر. في السوق العربي، واتساب أسرع طريق للبيع.",
            })

        if not raw.get("has_schema"):
            findings.append({
                "severity": "Low",
                "finding": "🗺️ بيانات منظمة مفقودة: موقعك لا يُعطي Google معلومات كافية عنك — مما يُضعف ظهورك في نتائج البحث المميزة.",
            })

    else:
        if raw.get("h1_generic") or not raw.get("h1"):
            findings.append({
                "severity": "Critical",
                "finding": "💸 Revenue Leak: Your headline fails to communicate value in 5 seconds. Every bounced visitor is a lost opportunity — permanently.",
            })

        if not raw.get("has_cta"):
            findings.append({
                "severity": "Critical",
                "finding": "🚫 Conversion Blocker: No clear call-to-action visible. Interested visitors have nowhere to go — so they leave.",
            })

        if not raw.get("has_social_proof"):
            findings.append({
                "severity": "High",
                "finding": "⚠️ Trust Gap: No customer testimonials or results visible. 92% of buyers need social proof before deciding.",
            })

        if raw.get("imgs_no_alt", 0) > 2:
            findings.append({
                "severity": "High",
                "finding": f"🔍 Search Visibility Loss: {raw['imgs_no_alt']} images have no alt text — Google ignores them, costing you rankings.",
            })

        if not raw.get("meta_ok"):
            findings.append({
                "severity": "High",
                "finding": "📉 Missed Search Opportunity: Meta description is unoptimised — your Google click-through rate is ~40% lower than it could be.",
            })

        if raw.get("social_count", 0) < 2:
            findings.append({
                "severity": "Medium",
                "finding": "📱 Social Media Gap: Social channels are not integrated — you're missing a daily audience actively looking for you.",
            })

        if not raw.get("has_whatsapp"):
            findings.append({
                "severity": "Medium",
                "finding": "💬 Contact Friction: No WhatsApp button. In Arab markets, WhatsApp is the fastest path to a sale.",
            })

        if not raw.get("has_schema"):
            findings.append({
                "severity": "Low",
                "finding": "🗺️ Missing Structured Data: Your site isn't giving Google enough context — weakening your presence in rich search results.",
            })

    return findings


def build_quick_wins(raw: dict, lang: str, industry: str) -> list:
    wins = []
    ins  = INDUSTRY_INSIGHTS.get(industry, INDUSTRY_INSIGHTS["default"]).get(lang, {})

    if lang == "ar":
        if raw.get("h1_generic") or not raw.get("h1"):
            wins.append("أعد كتابة العنوان الرئيسي: بدلاً من اسم الشركة، اكتب النتيجة التي تُحققها للعميل")
        if not raw.get("has_cta"):
            wins.append("أضف زر 'تواصل معنا' أو 'احجز استشارة مجانية' في أعلى كل صفحة — مرئي بدون تمرير")
        if not raw.get("has_whatsapp"):
            wins.append("أضف زر واتساب ثابت في الزاوية السفلية — يرفع معدل التواصل 2-3 أضعاف")
        if raw.get("imgs_no_alt", 0) > 0:
            wins.append(f"أضف وصفاً نصياً لـ {raw['imgs_no_alt']} صورة — تحسين SEO فوري بدون تكلفة")
        if not raw.get("meta_ok"):
            wins.append("اكتب وصفاً محسّناً للصفحة الرئيسية (150 حرف): ما تقدمه + لمن + لماذا أنت الأفضل")
    else:
        if raw.get("h1_generic") or not raw.get("h1"):
            wins.append("Rewrite the headline: instead of your company name, write the outcome you deliver for clients")
        if not raw.get("has_cta"):
            wins.append("Add 'Contact Us' or 'Book Free Consultation' button at the top of every page — visible without scrolling")
        if not raw.get("has_whatsapp"):
            wins.append("Add a fixed WhatsApp button in the bottom corner — increases contact rate 2-3×")
        if raw.get("imgs_no_alt", 0) > 0:
            wins.append(f"Add alt text to {raw['imgs_no_alt']} images — instant SEO boost at zero cost")
        if not raw.get("meta_ok"):
            wins.append("Write an optimised meta description (150 chars): what you offer + who for + why you're best")

    wins += ins.get("quick_wins_extra", [])
    return wins[:6]


def build_medium_term(lang: str, industry: str) -> list:
    if lang == "ar":
        return [
            f"أنشئ صفحة 'من نحن' تحكي قصة نجاح حقيقية بأرقام قابلة للقياس",
            "ابنِ 3 باقات خدمة واضحة بأسعار وميزات محددة — توقف عن بيع المجهول",
            "أطلق مدونة أو محتوى متخصص يستهدف كلمات بحث محلية عالية القيمة",
            "أنشئ صفحة هبوط مخصصة لكل خدمة رئيسية — ليس كل شيء في صفحة واحدة",
            "وحّد هوية علامتك على جميع المنصات: الألوان، اللوغو، الأسلوب",
        ]
    return [
        "Build an 'About Us' page telling a real success story with measurable numbers",
        "Create 3 clear service packages with defined prices and features — stop selling the unknown",
        "Launch a specialised blog targeting high-value local search keywords",
        "Build a dedicated landing page for each core service — not everything on one page",
        "Unify brand identity across all platforms: colours, logo, tone of voice",
    ]


def build_strategic(lang: str, location: str) -> list:
    if lang == "ar":
        return [
            "طوّر استراتيجية محتوى 90 يوم تستهدف المشترين المحتملين في مرحلة البحث",
            "أنشئ برنامج إحالة — كل عميل راضٍ هو مسوّق مجاني لو حفّزته",
            f"استهدف الكلمات المفتاحية المحلية في {location} بمحتوى متخصص وصفحات منطقة جغرافية",
            "أنشئ تسلسل بريد إلكتروني آلي يُرعى الزوار من أول تواصل حتى البيع",
            "طوّر هوية رقمية واضحة: من تخدم + ماذا تحل + ما يجعلك مختلفاً — في جملة واحدة",
        ]
    return [
        "Develop a 90-day content strategy targeting potential buyers in the search phase",
        f"Build a referral programme — every satisfied client is a free marketer if incentivised",
        f"Target local keywords in {location} with specialised content and geo-landing pages",
        "Create an automated email sequence nurturing visitors from first contact to sale",
        "Develop a clear digital identity: who you serve + what you solve + what makes you different — in one sentence",
    ]


def build_executive_summary(data: dict, lang: str) -> str:
    score    = data["overall_score"]
    brand    = data["brand_name"]
    location = data["location"]
    industry = data["industry"]
    ins      = INDUSTRY_INSIGHTS.get(industry, INDUSTRY_INSIGHTS["default"]).get(lang, {})
    intro    = ins.get("exec_intro", "")

    if lang == "ar":
        if score >= 75:
            health = "مرتفع نسبياً"
            action = "التحسينات المقترحة ستُعزز نتائجك وتفتح فرص نمو إضافية"
        elif score >= 55:
            health = "متوسط"
            action = "هناك فرص واضحة لتحويل هذا الموقع إلى آلة توليد عملاء"
        else:
            health = "يحتاج تحسيناً عاجلاً"
            action = "موقعك الحالي يُكلّفك عملاء يومياً — التحسينات الفورية ستُحدث فرقاً فورياً"

        return (
            f"{intro} يُحقق موقع {brand} أداءً {health} (درجة {score}/100) "
            f"في سوق {location}. "
            f"{action}. "
            f"التقرير التالي يُحدد نقاط التسرب التسويقي بالأولوية ويقترح خارطة طريق 90 يوماً لتحقيق نتائج قابلة للقياس."
        )
    else:
        if score >= 75:
            health = "relatively strong"
            action = "The suggested improvements will amplify your results and unlock further growth opportunities"
        elif score >= 55:
            health = "moderate"
            action = "There are clear opportunities to transform this site into a lead-generation machine"
        else:
            health = "in need of urgent improvement"
            action = "Your current site is costing you clients daily — immediate fixes will create immediate impact"

        return (
            f"{intro} {brand}'s website achieves {health} performance (score: {score}/100) "
            f"in the {location} market. "
            f"{action}. "
            f"This report identifies marketing revenue leaks by priority and proposes a 90-day roadmap for measurable results."
        )


def frame_report(analysis: dict, lang: str = None) -> dict:
    """Transform raw analysis into a business consultant report."""
    if lang is None:
        lang = analysis.get("language", "ar")

    raw      = analysis["raw"]
    location = analysis.get("location", "default")
    industry = analysis.get("industry", "agency")

    findings  = build_findings(raw, lang)
    quick_wins= build_quick_wins(raw, lang, industry)
    medium    = build_medium_term(lang, industry)
    strategic = build_strategic(lang, location)
    exec_sum  = build_executive_summary(analysis, lang)
    local_tips= analysis.get("local_tips", {}).get(lang, [])

    return {
        "url":               analysis["url"],
        "date":              analysis["date_ar"] if lang == "ar" else analysis["date"],
        "brand_name":        analysis["brand_name"],
        "overall_score":     analysis["overall_score"],
        "language":          lang,
        "location":          location,
        "industry":          industry,
        "executive_summary": exec_sum,
        "categories":        analysis["categories"],
        "findings":          findings,
        "quick_wins":        quick_wins,
        "medium_term":       medium,
        "strategic":         strategic,
        "local_tips":        local_tips,
    }
