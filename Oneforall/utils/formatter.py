# -*- coding: utf-8 -*-

"""
Text formatting utilities
Small-caps • Bullet points • Telegram-safe
"""

SMALL_CAPS_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ",
)


def small_caps(text: str) -> str:
    """Convert normal text to small caps"""
    return text.lower().translate(SMALL_CAPS_MAP)


def bulletize(lines: list, bullet: str = "•") -> str:
    """Convert list into bullet points"""
    return "\n".join(f"{bullet} {small_caps(line)}" for line in lines)


def section(title: str, content: str) -> str:
    """Create a formatted section"""
    return f"\n\n⟐ {small_caps(title)} ⟐\n{content}"


def format_scan_report(
    domain: str,
    risk_level: str,
    score: int,
    threats: list,
    recommendations: list,
) -> str:
    """
    Final textual report for Telegram
    """

    header = (
        f"🛡 {small_caps('website vulnerability scan')}\n"
        f"▸ {small_caps('target')} : {small_caps(domain)}\n"
        f"▸ {small_caps('risk level')} : {small_caps(risk_level)}\n"
        f"▸ {small_caps('risk score')} : {score}/10"
    )

    threats_text = bulletize(threats)
    rec_text = bulletize(recommendations, bullet="➤")

    report = (
        header
        + section("identified threats", threats_text)
        + section("security recommendations", rec_text)
        + "\n\n⛨ " + small_caps("passive scan • no exploitation performed")
    )

    return report
