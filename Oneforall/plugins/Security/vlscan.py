import sys
import os
import threading
import asyncio
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from fpdf import FPDF

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import BOT_TOKEN

# ================= CONFIG =================
SEC_HEADERS = [
    "X-Frame-Options",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "Strict-Transport-Security",
    "Referrer-Policy",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

MAX_PAGES = 80
PROGRESS_STEP = 5
TIMEOUT = 10
sys.setrecursionlimit(4000)
# =========================================


# ============== UTILS ==============
def small_caps(text: str) -> str:
    table = str.maketrans(
        "abcdefghijklmnopqrstuvwxyz",
        "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    )
    return text.lower().translate(table)


def pdf_safe(text, max_len=100):
    if not isinstance(text, str):
        text = str(text)
    return text[:max_len].encode("latin-1", "ignore").decode("latin-1")


# ============== ASYNC HELPERS ==============
async def edit_progress(bot, chat_id, msg_id, text):
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=text
        )
    except:
        pass


async def store_results(context, results):
    context.user_data["results"] = results
    context.user_data["results_ready"] = True


# ============== CORE SCANNER ==============
def analyze_and_extract(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if "text/html" not in r.headers.get("Content-Type", ""):
        raise Exception("non-html")

    soup = BeautifulSoup(r.text, "html.parser")

    missing_headers = [h for h in SEC_HEADERS if h not in r.headers]

    cookie_issues = []
    cookies = r.headers.get("Set-Cookie", "")
    if cookies:
        if "secure" not in cookies.lower():
            cookie_issues.append("secure flag missing")
        if "httponly" not in cookies.lower():
            cookie_issues.append("httponly missing")

    params = parse_qs(urlparse(url).query)
    suspicious_params = [
        p for p in params if re.search(r"id|token|auth|key|session", p, re.I)
    ]

    insecure_forms = 0
    for f in soup.find_all("form"):
        action = f.get("action", "")
        if action.startswith("http://"):
            insecure_forms += 1

    js_secrets = 0
    for s in soup.find_all("script"):
        if s.string and re.search(r"api[_-]?key|secret|token", s.string, re.I):
            js_secrets += 1

    links = []
    for a in soup.find_all("a", href=True):
        links.append(a["href"])

    risk = "low"
    if missing_headers or cookie_issues or suspicious_params:
        risk = "medium"
    if js_secrets or insecure_forms:
        risk = "high"

    return {
        "url": url,
        "status": r.status_code,
        "missing_headers": missing_headers,
        "cookie_issues": cookie_issues,
        "params": suspicious_params,
        "insecure_forms": insecure_forms,
        "js_secrets": js_secrets,
        "risk": risk,
        "links": links,
    }


# ============== TEXT REPORT ==============
def generate_text_report(results, limit=10):
    high = medium = low = 0
    findings = []

    for r in results:
        if r["risk"] == "high":
            high += 1
        elif r["risk"] == "medium":
            medium += 1
        else:
            low += 1

        if len(findings) >= limit:
            continue

        issues = []
        if r["missing_headers"]:
            issues.append(f"missing headers ({len(r['missing_headers'])})")
        if r["cookie_issues"]:
            issues.append("cookie insecurity")
        if r["params"]:
            issues.append("suspicious url parameters")
        if r["insecure_forms"]:
            issues.append("insecure http form")
        if r["js_secrets"]:
            issues.append("possible js secret leak")

        if issues:
            findings.append(
                f"• {r['url']}\n  ↳ " + "; ".join(issues)
            )

    report = (
        f"scan summary\n"
        f"pages scanned: {len(results)}\n"
        f"risk distribution → high: {high}, medium: {medium}, low: {low}\n\n"
        f"minor vulnerability findings:\n"
    )

    report += "\n".join(findings) if findings else "no obvious weaknesses detected"
    return small_caps(report)


# ============== THREAD RUNNER ==============
def run_scan(update, context, loop):
    target = context.user_data["target"]
    message = update._scan_message

    visited = set()
    queue = [target]
    results = []
    count = 0

    while queue and len(visited) < MAX_PAGES:
        url = queue.pop(0)
        if url in visited:
            continue
        if urlparse(url).netloc != urlparse(target).netloc:
            continue

        visited.add(url)

        try:
            data = analyze_and_extract(url)
            results.append(data)
            for h in data["links"]:
                full = urljoin(url, h).split("#")[0]
                if full not in visited:
                    queue.append(full)
        except:
            pass

        count += 1
        if count % PROGRESS_STEP == 0:
            asyncio.run_coroutine_threadsafe(
                edit_progress(
                    context.bot,
                    update.effective_chat.id,
                    message.message_id,
                    small_caps(f"scanning… {count} pages"),
                ),
                loop,
            )

    asyncio.run_coroutine_threadsafe(store_results(context, results), loop)

    asyncio.run_coroutine_threadsafe(
        edit_progress(
            context.bot,
            update.effective_chat.id,
            message.message_id,
            small_caps(f"scan completed\npages scanned: {len(results)}"),
        ),
        loop,
    )

    text_report = generate_text_report(results)
    asyncio.run_coroutine_threadsafe(
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_report,
        ),
        loop,
    )


# ============== PDF ==============
def make_pdf(results, user_id):
    name = f"vuln_report_{user_id}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Website Vulnerability Report", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=9)
    for r in results:
        pdf.multi_cell(
            0, 6,
            pdf_safe(
                f"""
URL: {r['url']}
Risk: {r['risk'].upper()}
Missing headers: {', '.join(r['missing_headers']) or 'none'}
Cookie issues: {', '.join(r['cookie_issues']) or 'none'}
Suspicious params: {', '.join(r['params']) or 'none'}
Insecure forms: {r['insecure_forms']}
JS exposure signs: {r['js_secrets']}
------------------------------
"""
            ),
        )

    pdf.output(name)
    return name


# ============== TELEGRAM COMMANDS ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🔍 start scan", callback_data="scan")],
        [InlineKeyboardButton("📄 generate pdf", callback_data="pdf")],
    ]
    await update.message.reply_text(
        "🛡 advanced vulnerability scanner\n\n"
        "/vlscan <url>\n"
        "/vlpdf",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def vlscan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            small_caps("usage:\n/vlscan https://example.com")
        )
        return

    target = context.args[0].rstrip("/")
    context.user_data.clear()
    context.user_data["target"] = target
    context.user_data["results_ready"] = False

    msg = await update.message.reply_text(
        small_caps("initializing deep scan…")
    )

    update._scan_message = msg
    loop = asyncio.get_running_loop()

    threading.Thread(
        target=run_scan,
        args=(update, context, loop),
        daemon=True,
    ).start()


async def vlpdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("results_ready"):
        await update.message.reply_text(
            small_caps("no scan data available")
        )
        return

    file = make_pdf(
        context.user_data["results"],
        update.effective_user.id,
    )

    with open(file, "rb") as f:
        await update.message.reply_document(f)

    os.remove(file)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "scan":
        if "target" not in context.user_data:
            await q.edit_message_text(
                small_caps("use /vlscan <url> first")
            )
            return

        q.message.edit_text(small_caps("starting scan…"))
        update._scan_message = q.message
        loop = asyncio.get_running_loop()

        threading.Thread(
            target=run_scan,
            args=(update, context, loop),
            daemon=True,
        ).start()

    elif q.data == "pdf":
        if not context.user_data.get("results_ready"):
            await q.edit_message_text(
                small_caps("scan not completed yet")
            )
            return

        file = make_pdf(
            context.user_data["results"],
            update.effective_user.id,
        )

        with open(file, "rb") as f:
            await q.message.reply_document(f)

        os.remove(file)


# ============== RUN ==============
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("vlscan", vlscan))
app.add_handler(CommandHandler("vlpdf", vlpdf))
app.add_handler(CallbackQueryHandler(buttons))
app.run_polling()
