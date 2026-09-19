#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات خبری بله — هر ۳ روز یک‌بار اجرا
بدون لینک کامل اخبار، همراه با هشتگ
"""

import json
import os
import random
import hashlib
import time
import re
from datetime import datetime, timedelta
from urllib.parse import quote
from xml.etree import ElementTree as ET

import requests

from config import (
    BALE_TOKEN, CHANNEL_ID, WATERMARK,
    NEWS_FEEDS, CAR_FEEDS,
    ECON_KEYWORDS, CAR_KEYWORDS, MAX_AGE_DAYS
)

BALE_API = f"https://tapi.bale.ai/bot{BALE_TOKEN}"
SENT_FILE = "sent_hashes.json"


# ═══════════════════════════════════════════════════════
#  مدیریت هش‌ها
# ═══════════════════════════════════════════════════════

def load_sent() -> dict:
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_sent(data: dict):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cleanup_old_hashes(data: dict) -> dict:
    cutoff = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).isoformat()
    return {k: v for k, v in data.items() if v > cutoff}


def make_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════
#  ارسال به بله
# ═══════════════════════════════════════════════════════

def send_message(text: str, parse_mode: str = "Markdown") -> bool:
    url = f"{BALE_API}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text + WATERMARK,
        "parse_mode": parse_mode,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("ok"):
                print("  ✅ ارسال شد")
                return True
            print(f"  ❌ خطای API: {result}")
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"  ❌ خطا: {e}")
    return False


# ═══════════════════════════════════════════════════════
#  دریافت RSS
# ═══════════════════════════════════════════════════════

def fetch_rss(url: str) -> list:
    items = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (BaleBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for entry in entries[:10]:
            title, link, desc = "", "", ""

            t = entry.find("title")
            if t is not None and t.text:
                title = t.text.strip()

            l = entry.find("link")
            if l is not None:
                link = (l.text or l.get("href", "")).strip()

            d = entry.find("description")
            if d is not None and d.text:
                desc = re.sub(r"<[^>]+>", "", d.text)[:300].strip()

            if not title:
                t = entry.find("atom:title", ns)
                if t is not None and t.text:
                    title = t.text.strip()
            if not link:
                l = entry.find("atom:link", ns)
                if l is not None:
                    link = l.get("href", "").strip()
            if not desc:
                d = entry.find("atom:summary", ns)
                if d is not None and d.text:
                    desc = d.text.strip()[:300]

            if title:
                items.append({"title": title, "link": link, "summary": desc})
    except Exception as e:
        print(f"  ⚠️ خطا در {url}: {e}")
    return items


# ═══════════════════════════════════════════════════════
#  جستجوی برتینا
# ═══════════════════════════════════════════════════════

def search_bertina(query: str) -> list:
    results = []
    try:
        search_url = f"https://search.bertina.ir/search?q={quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(search_url, headers=headers, timeout=20)
        resp.encoding = "utf-8"
        html = resp.text

        pattern = re.compile(
            r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL
        )
        matches = pattern.findall(html)

        seen = set()
        for link, raw_title in matches[:20]:
            title = re.sub(r"<[^>]+>", "", raw_title).strip()
            if (title and len(title) > 15 and
                    "bertina" not in link.lower() and
                    link not in seen):
                seen.add(link)
                results.append({
                    "title": title[:200],
                    "link": link,
                    "summary": title[:300],
                })
    except Exception as e:
        print(f"  ⚠️ خطا در برتینا: {e}")
    return results[:5]


# ═══════════════════════════════════════════════════════
#  قالب‌بندی (بدون لینک + با هشتگ)
# ═══════════════════════════════════════════════════════

def format_news(item: dict, fmt: int = None) -> str:
    """قالب‌بندی خبر عمومی بدون لینک، همراه با هشتگ"""
    if fmt is None:
        fmt = random.randint(1, 5)
    t = item["title"]
    s = item.get("summary", "")
    now = datetime.now().strftime("%Y/%m/%d %H:%M")

    hashtags = "#اخبار #خبری #بله_نیوز"

    formats = {
        1: f"📰 *{t}*\n\n{s}\n\n{hashtags}",
        2: f"🔹 {t}\n\n{s}\n\n{hashtags}",
        3: f"🗞 *{t}*\n━━━━━━━━━━━━━━━\n{s}\n📅 {now}\n\n{hashtags}",
        4: f"📢 *خبر فوری*\n\n▫️ {t}\n\n{s}\n\n#خبر_فوری #اخبار",
        5: f"⭐ *{t}*\n\n> {s}\n\n{hashtags}",
    }
    return formats.get(fmt, formats[1])


def format_economic(item: dict) -> str:
    """قالب پیش‌بینی اقتصادی بدون لینک"""
    t = item["title"]
    s = item.get("summary", "")
    hashtags = "#اقتصاد #پیش‌بینی_اقتصادی #تحلیل_بازار #تورم #بورس"

    templates = [
        f"📊 *پیش‌بینی اقتصادی*\n\n{t}\n\n{s}\n\n{hashtags}",
        f"📈 *تحلیل اقتصادی*\n\n▫️ {t}\n\n{s}\n\n{hashtags}",
        f"💹 *گزارش اقتصادی*\n\n{t}\n{s}\n\n{hashtags}",
    ]
    return random.choice(templates)


def format_car(item: dict) -> str:
    """قالب اطلاعیه خودرو بدون لینک"""
    t = item["title"]
    s = item.get("summary", "")
    hashtags = "#خودرو #فروش_خودرو #ایران_خودرو #سایپا #طرح_فروش"

    templates = [
        f"🚗 *اطلاعیه فروش خودرو*\n\n{t}\n\n{s}\n\n{hashtags}",
        f"🏎 *آخرین شرایط فروش*\n\n▫️ {t}\n\n{s}\n\n{hashtags}",
        f"📋 *ثبت‌نام خودرو*\n\n{t}\n{s}\n\n{hashtags}",
    ]
    return random.choice(templates)


def format_registration_links() -> str:
    """پیام لینک‌های رایج ثبت‌نام خودرو"""
    return (
        "🚙 *لینک‌های رایج ثبت‌نام خودرو*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "▫️ [ایران خودرو](https://esale.ikco.ir)\n"
        "سامانه فروش محصولات ایران خودرو\n\n"
        "▫️ [سایپا](https://saipa.iranecar.com)\n"
        "سامانه فروش محصولات گروه سایپا\n\n"
        "▫️ [اتونوین](https://atomin.ir)\n"
        "پلتفرم خرید و فروش خودرو\n\n"
        "▫️ [کرمان موتور](https://kermanmotor.ir)\n"
        "فروش محصولات کرمان موتور\n\n"
        "▫️ [بهمن موتور](https://bahman.ir)\n"
        "سامانه فروش گروه بهمن\n\n"
        "▫️ [پارس خودرو](https://parskhodro.ir)\n"
        "فروش محصولات پارس خودرو\n\n"
        "#خودرو #ثبت_نام_خودرو #طرح_فروش"
    )


# ═══════════════════════════════════════════════════════
#  حلقه اصلی
# ═══════════════════════════════════════════════════════

def main():
    print(f"\n{'='*50}")
    print(f"🤖 ربات خبری بله — {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print(f"{'='*50}")

    sent = load_sent()
    sent = cleanup_old_hashes(sent)
    print(f"📦 هش‌های فعال: {len(sent)}")

    all_items = []
    seen_hashes = {}

    # ۱) RSSهای خبری
    for source_name, url in NEWS_FEEDS.items():
        print(f"\n📡 دریافت از: {source_name}")
        items = fetch_rss(url)
        print(f"   → {len(items)} خبر")
        for item in items:
            h = make_hash(item["title"] + item.get("link", ""))
            if h not in sent and h not in seen_hashes:
                item["hash"] = h
                all_items.append(item)
                seen_hashes[h] = True

    # ۲) RSSهای خودرو
    for source_name, url in CAR_FEEDS.items():
        print(f"\n🚗 دریافت از: {source_name}")
        items = fetch_rss(url)
        print(f"   → {len(items)} خبر")
        for item in items:
            h = make_hash(item["title"] + item.get("link", ""))
            if h not in sent and h not in seen_hashes:
                item["hash"] = h
                all_items.append(item)
                seen_hashes[h] = True

    # ۳) جستجوی برتینا
    print(f"\n🔍 جستجو در برتینا...")
    for query in ["اخبار اقتصادی ایران", "طرح فروش خودرو", "پیش‌بینی تورم"]:
        results = search_bertina(query)
        print(f"   → {len(results)} نتیجه برای «{query}»")
        for item in results:
            h = make_hash(item["title"] + item.get("link", ""))
            if h not in sent and h not in seen_hashes:
                item["hash"] = h
                all_items.append(item)
                seen_hashes[h] = True

    if not all_items:
        print("\n✨ خبر جدیدی یافت نشد.")
        save_sent(sent)
        return

    print(f"\n🆕 {len(all_items)} خبر جدید (پس از حذف تکراری‌ها)")

    # دسته‌بندی
    normal, econ, car = [], [], []
    for item in all_items:
        text = item["title"] + " " + item.get("summary", "")
        if any(k in text for k in CAR_KEYWORDS):
            car.append(item)
        elif any(k in text for k in ECON_KEYWORDS):
            econ.append(item)
        else:
            normal.append(item)

    print(f"   📰 عادی: {len(normal)} | 📊 اقتصادی: {len(econ)} | 🚗 خودرو: {len(car)}")

    count = 0

    # ✅ کاهش تعداد: عادی ۳، اقتصادی ۲، خودرو ۲
    for item in normal[:3]:
        print(f"\n📤 ارسال خبر: {item['title'][:50]}...")
        if send_message(format_news(item)):
            sent[item["hash"]] = datetime.now().isoformat()
            count += 1
            time.sleep(2)

    for item in econ[:2]:
        print(f"\n📤 ارسال اقتصادی: {item['title'][:50]}...")
        if send_message(format_economic(item)):
            sent[item["hash"]] = datetime.now().isoformat()
            count += 1
            time.sleep(2)

    for item in car[:2]:
        print(f"\n📤 ارسال خودرو: {item['title'][:50]}...")
        if send_message(format_car(item)):
            sent[item["hash"]] = datetime.now().isoformat()
            count += 1
            time.sleep(2)

    # ✅ لینک‌های رایج ثبت‌نام خودرو (هر ۳ روز یک‌بار با اجرا)
    links_key = "registration_links_" + datetime.now().strftime('%Y%m%d')
    if links_key not in sent:
        print(f"\n📤 ارسال لینک‌های ثبت‌نام خودرو...")
        if send_message(format_registration_links()):
            sent[links_key] = datetime.now().isoformat()
            count += 1

    save_sent(sent)
    print(f"\n{'='*50}")
    print(f"✅ مجموعاً {count} پیام ارسال شد")
    print(f"📦 هش‌های ذخیره‌شده: {len(sent)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
