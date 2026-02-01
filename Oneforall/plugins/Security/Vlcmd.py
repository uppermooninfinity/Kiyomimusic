from pyrogram import Client, filters
from pyrogram.types import Message
import os

from Oneforall.utils.formatter import format_scan_report
from Oneforall.utils.pdf_report import generate_pdf_report
from Oneforall.utils.scanner_core import scan_website


@Client.on_message(filters.command(["vlscan"], prefixes="/") & (filters.private | filters.group))
async def vlscan_handler(client: Client, message: Message):
    """
    Command: /vlscan <website>
    Works in private chats and groups (with or without bot mention)
    """

    # Make sure command has argument
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage:\n/vlscan <website>\nExample: /vlscan example.com"
        )

    target = message.command[1]
    status_msg = await message.reply_text(f"🔍 Starting scan for {target}...")

    try:
        # Run the scan
        result = scan_website(target)
    except Exception as e:
        await status_msg.edit(f"❌ Scan failed: {e}")
        return

    # Generate textual report
    text_report = format_scan_report(
        domain=result["domain"],
        risk_level=result["risk"],
        score=result["score"],
        threats=result["threats"],
        recommendations=result["recommendations"],
    )

    # Generate PDF report
    pdf_path = f"/tmp/vlscan_{result['domain'].replace('.', '_')}.pdf"
    generate_pdf_report(
        file_path=pdf_path,
        domain=result["domain"],
        risk_level=result["risk"],
        score=result["score"],
        threats=result["threats"],
        recommendations=result["recommendations"],
    )

    # Send textual report
    await status_msg.edit(f"✅ Scan complete! Sending reports for {target}...")
    await message.reply_text(f"```\n{text_report}\n```", disable_web_page_preview=True)

    # Send PDF
    await message.reply_document(pdf_path, caption="📄 Vulnerability Scan Report (PDF)")

    # Cleanup
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    await status_msg.delete()
