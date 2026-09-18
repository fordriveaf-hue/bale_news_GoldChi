# -*- coding: utf-8 -*-
import os

# ─── توکن از متغیر محیطی خوانده می‌شود (مخفی) ───
BALE_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "5107422630")

if not BALE_TOKEN:
    raise ValueError("❌ متغیر محیطی BALE_BOT_TOKEN تنظیم نشده است!")

# ─── واترمارک ───
WATERMARK = "\n\n🔗 @GoldChi\n🔗 ble.ir/join/HaifASLDFZ"

# ─── منابع RSS خبری ───
NEWS_FEEDS = {
    "مهر - آخرین اخبار": "https://www.mehrnews.com/rss",
    "مهر - اقتصادی": "https://www.mehrnews.com/rss/pl/108",
    "مهر - فوری": "https://www.mehrnews.com/rss/pl/224",
    "ایرسا": "https://www.irasin.ir/rss",
    "ایمنا": "https://www.imna.ir/rss",
    "ایکنا": "https://icana.ir/rss",
}

# ─── منابع اختصاصی خودرو ───
CAR_FEEDS = {
    "پرشین خودرو - طرح‌های فروش": "https://persiankhodro.com/rss/tp/3",
    "پرشین خودرو - اخبار خودرو": "https://persiankhodro.com/rss/tp/2",
    "پرشین خودرو - سهام خودروسازان": "https://persiankhodro.com/rss/tp/5",
}

# ─── کلیدواژه‌ها ───
ECON_KEYWORDS = [
    "پیش‌بینی", "رشد اقتصادی", "تورم", "صندوق بین‌المللی پول",
    "بانک جهانی", "اقتصاد ایران", "شاخص", "بورس", "ارز",
    "دلار", "نرخ بهره", "تولید ناخالص",
]

CAR_KEYWORDS = [
    "ثبت نام خودرو", "فروش خودرو", "ایران خودرو", "سایپا",
    "پیش فروش", "قرعه کشی خودرو", "سامانه فروش",
    "esale.ikco.ir", "saipa.iranecar.com", "طرح فروش",
    "خودرو", "قیمت خودرو", "مشارکت در تولید",
]

MAX_AGE_DAYS = 30
