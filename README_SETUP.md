# MarketScan — إعداد وتشغيل المشروع

## خطوات التشغيل

### 1. تثبيت المتطلبات
```bash
cd webapp
pip install -r requirements.txt
```

### 2. إعداد Stripe (الدفع)
1. أنشئ حساباً على https://dashboard.stripe.com
2. من القائمة: **Developers > API Keys**
3. انسخ **Publishable key** و **Secret key**
4. افتح ملف `.env` وضع المفاتيح

### 3. تشغيل السيرفر
```bash
python app.py
```
افتح المتصفح على: http://localhost:5000

### 4. اختبار بدون دفع (وضع Demo)
```
http://localhost:5000/demo?url=https://provision360.net/&lang=ar
```
يُنشئ التقرير مباشرة بدون Stripe.

---

## هيكل الملفات
```
webapp/
├── app.py              ← السيرفر الرئيسي (Flask)
├── analyzer.py         ← تحليل الموقع + كشف الموقع الجغرافي والقطاع
├── consultant_framer.py← تحويل البيانات للغة استشارية
├── config.py           ← الإعدادات
├── .env                ← مفاتيح API (لا ترفعه على GitHub!)
├── requirements.txt
├── static/
│   └── index.html      ← صفحة المنتج (عربي/إنجليزي)
└── generated_pdfs/     ← التقارير المُنشأة (يُنشأ تلقائياً)
```

## للرفع على الإنترنت (Production)
- **Render.com** أو **Railway.app** — مجاني للبدء
- غيّر `BASE_URL` في `.env` لعنوانك الحقيقي
- فعّل Stripe Webhook على: `https://yoursite.com/webhook/stripe`
