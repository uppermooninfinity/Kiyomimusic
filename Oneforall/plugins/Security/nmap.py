from pyrogram import Client, filters
from pyrogram.types import Message
import subprocess
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime

from Oneforall.utils.formatter import format_scan_report
from Oneforall.utils.pdf_report import generate_pdf_report

def parse_nmap_results(nmap_xml_path: str, domain: str):
    """Parse Nmap XML to OneForAll format."""
    try:
        tree = ET.parse(nmap_xml_path)
        root = tree.getroot()
        
        open_ports = []
        services = []
        for port in root.findall('.//port[state/@state="open"]'):
            portid = port.get('portid')
            protocol = port.find('protocol').text if port.find('protocol') is not None else 'tcp'
            service = port.find('service')
            service_name = service.get('name') if service is not None else 'unknown'
            open_ports.append(f"{portid}/{protocol}")
            services.append(f"{service_name}:{portid}")
        
        threats = open_ports or ["No open ports detected"]
        if open_ports:
            threats.append(f"Services: {', '.join(services[:5])}")
        
        score = max(100 - len(open_ports) * 8, 20)  # Simple scoring
        risk = "High" if len(open_ports) > 10 else "Medium" if open_ports else "Low"
        
        return {
            "domain": domain,
            "risk": risk,
            "score": score,
            "threats": threats,
            "recommendations": [
                "Close unnecessary open ports",
                "Update vulnerable services",
                f"Full scan: nmap -sV -sC -O {domain}",
                "Firewall all non-essential ports"
            ]
        }
    except Exception:
        # Fallback mock data
        return {
            "domain": domain,
            "risk": "Unknown",
            "score": 50,
            "threats": ["Nmap XML parse failed - check logs"],
            "recommendations": ["Run manual nmap for details"]
        }

@Client.on_message(filters.command(["nmap"], prefixes="/") & (filters.private | filters.group))
async def nmap_handler(client: Client, message: Message):
    """
    Command: /nmap <website or IP>
    Performs real Nmap scan + formats with OneForAll utils
    """
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: `/nmap example.com` or `/nmap 192.168.1.1`"
            "Scans top 100 ports + service detection"
        )

    target = message.command[1]
    if not re.match(r'^[a-zA-Z0-9.-]+$', target):
        return await message.reply_text("❌ Invalid target (alphanumeric + dots/hyphens only)")

    status_msg = await message.reply_text(f"🔍 Nmap scanning `{target}` (top 100 ports)...")

    xml_path = None
    try:
        # Create secure temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
            xml_path = tmp.name

        # Run Nmap: top 100 ports + service detection + XML output (quick ~10s)
        cmd = [
            "nmap", "-sV", "--top-ports", "100", 
            "-oX", xml_path, "--host-timeout", "30s",
            target
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        
        if proc.returncode != 0:
            await status_msg.edit_text(f"❌ Nmap failed:```{proc.stderr[:1000]}```")
            return

        # Parse results
        result = parse_nmap_results(xml_path, target)

        # Generate formatted report
        text_report = format_scan_report(
            domain=result["domain"],
            risk_level=result["risk"],
            score=result["score"],
            threats=result["threats"],
            recommendations=result["recommendations"],
        )

        # PDF report
        domain_safe = re.sub(r'[^w-_.]', '_', target)
        pdf_path = f"/tmp/nmap_{domain_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        generate_pdf_report(
            file_path=pdf_path,
            domain=result["domain"],
            risk_level=result["risk"],
            score=result["score"],
            threats=result["threats"],
            recommendations=result["recommendations"],
        )

        # Send results
        await status_msg.edit_text(
            f"""✅ Nmap scan complete for `{target}`!"""
            f"""**Risk:** {result['risk']} | **Score:** {result['score']}/100"""
        )
        await message.reply_text(f"```{text_report}```")

        if os.path.exists(pdf_path):
            await message.reply_document(
                pdf_path, 
                caption=f"📄 Nmap Report - {target} | {result['risk']} Risk"
            )

    except subprocess.TimeoutExpired:
        await status_msg.edit_text("⏰ Scan timeout (45s) - target too slow")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        # Cleanup
        if xml_path and os.path.exists(xml_path):
            os.unlink(xml_path)
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.unlink(pdf_path)
        await status_msg.delete()
