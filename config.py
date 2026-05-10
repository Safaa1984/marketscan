"""
Configuration — copy .env.example to .env and fill in your keys.
"""
import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_YOUR_KEY")
STRIPE_WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_YOUR_SECRET")

# Price in the smallest currency unit (halalas for SAR: 10 SAR = 1000 halalas)
REPORT_PRICE_SAR    = 900           # 9 SAR
REPORT_CURRENCY     = "sar"
REPORT_PRODUCT_NAME = "تقرير تحليل تسويقي احترافي"

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-32chars!")
BASE_URL   = os.getenv("BASE_URL", "http://localhost:5000")
