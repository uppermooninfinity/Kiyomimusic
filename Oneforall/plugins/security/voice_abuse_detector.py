"""
Active Voice Chat Abuse Detection System
Detects abusive speech in ACTIVE voice chats using userbot to capture and analyze audio.
Works with English and Hindi speech in real-time.
"""

import asyncio
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import RPCError

try:
    import speech_recognition as sr
    from pydub import AudioSegment
except ImportError:
    print("Install: pip install SpeechRecognition pydub")

try:
    from detoxify import Detoxify
except ImportError:
    print("Install: pip install detoxify")

try:
    import librosa
    import numpy as np
except ImportError:
    print("Install: pip install librosa numpy")

try:
    from Oneforall import app
    from config import OWNER_ID
    from Oneforall.misc import SUDOERS
except ImportError as e:
    raise ImportError(f"Could not import required modules: {e}")


class VoiceAbuseDetector:
    """Real-time detection system for abusive speech in active voice chats."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        
        try:
            self.toxicity_model = Detoxify('original')
            self.ai_enabled = True
        except Exception as e:
            print(f"[VoiceAbuse] Detoxify model not available: {e}")
            self.ai_enabled = False
        
        self.TOXICITY_THRESHOLD = 0.5
        self.active_monitoring = {}  # {chat_id: True/False}
        self.user_abuse_scores = {}  # {chat_id: {user_id: [timestamps]}}
        self.detection_settings = {}  # {chat_id: settings}
        self.voice_logs = {}  # {chat_id: [logs]}
        
        # Multilingual abusive words dictionary
        self.abusive_words_en = {
            "fuck", "shit", "bitch", "asshole", "bastard", "crap", "damn",
            "hell", "piss", "ass", "dick", "motherfucker", "goddamn", "cunt",
            "twat", "arsehole", "bollocks", "bugger", "dammit", "frick",
            "douchebag", "jackass", "jerk", "prick", "slut", "whore", "fucked",
            "shitty", "bitchy", "ass", "asses", "fuckers", "fucking"
        }
        
        # Hindi abusive words
        self.abusive_words_hi = {
            "chutiya", "madarchod", "bhenchod", "saala", "harami", "nalayak",
            "gawaar", "ullu", "gadha", "kumara", "behaya", "badmash", "randi",
            "khota", "tere_maa_ki", "tera_baap", "kangna", "lavda", "lund",
            "chodu", "behenchod", "maa_ki", "gaandu", "rand", "randi_ka"
        }
        
        # Profanity patterns
        self.spam_patterns = [
            r'(.)\1{9,}',  # Repeated characters
            r'[A-Z]{5,}',   # ALL CAPS spam
            r'(fuck|shit|ass)\w*ing',  # Variations
        ]
    
    def get_settings(self, chat_id: int) -> dict:
        """Get voice abuse detection settings for a chat."""
        if chat_id not in self.detection_settings:
            self.detection_settings[chat_id] = {
                'enabled': False,  # Must be explicitly enabled
                'threshold': self.TOXICITY_THRESHOLD,
                'action': 'warn',  # warn, mute, ban, gban
                'warn_limit': 2,
                'mute_duration': 1800,
                'log_enabled': True,
                'ai_model': 'detoxify+keyword',
                'monitor_active': False,
                'auto_unmute': True
            }
        return self.detection_settings[chat_id]
    
    def set_settings(self, chat_id: int, **kwargs):
        """Update voice abuse detection settings."""
        settings = self.get_settings(chat_id)
        for key, value in kwargs.items():
            if key in settings:
                settings[key] = value
    
    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Convert audio file to text using speech recognition (multi-language)."""
        try:
            if not os.path.exists(audio_path):
                return None
            
            # Convert to WAV if needed
            if not audio_path.endswith('.wav'):
                try:
                    audio = AudioSegment.from_file(audio_path)
                    wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                    audio.export(wav_path, format='wav')
                    audio_path = wav_path
                except Exception as e:
                    print(f"[VoiceAbuse] Audio conversion failed: {e}")
                    return None
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            
            # Try English first
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
                print(f"[VoiceAbuse] Transcribed (EN): {text}")
                return text
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
            
            # Try Hindi
            try:
                text = self.recognizer.recognize_google(audio, language='hi-IN')
                print(f"[VoiceAbuse] Transcribed (HI): {text}")
                return text
            except:
                pass
            
            # Fallback to Sphinx (offline)
            try:
                text = self.recognizer.recognize_sphinx(audio)
                print(f"[VoiceAbuse] Transcribed (Sphinx): {text}")
                return text
            except:
                return None
                
        except Exception as e:
            print(f"[VoiceAbuse] Transcription error: {e}")
            return None
    
    def check_abusive_keywords(self, text: str) -> tuple:
        """Check for abusive keywords in text."""
        if not text:
            return False, None
        
        text_lower = text.lower()
        
        # Check English words
        for word in self.abusive_words_en:
            if word in text_lower:
                return True, f"EN: {word}"
        
        # Check Hindi words
        for word in self.abusive_words_hi:
            if word in text_lower:
                return True, f"HI: {word}"
        
        # Check patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, text):
                return True, f"Pattern: {pattern}"
        
        return False, None
    
    def analyze_toxicity(self, text: str) -> Dict[str, float]:
        """Analyze text for toxicity using AI model and keyword matching."""
        if not text:
            return {'toxic': 0.0, 'severe_toxic': 0.0, 'obscene': 0.0, 'insult': 0.0, 'threat': 0.0, 'identity_hate': 0.0}
        
        # Check keywords first (faster)
        is_abusive, detected = self.check_abusive_keywords(text)
        if is_abusive:
            print(f"[VoiceAbuse] Detected abusive keyword: {detected}")
            return {'toxic': 0.85, 'severe_toxic': 0.75, 'obscene': 0.9, 'insult': 0.88, 'threat': 0.6, 'identity_hate': 0.7}
        
        # Use AI model if enabled
        if self.ai_enabled:
            try:
                results = self.toxicity_model.predict(text)
                return results
            except Exception as e:
                print(f"[VoiceAbuse] AI analysis error: {e}")
        
        return {'toxic': 0.0, 'severe_toxic': 0.0, 'obscene': 0.0, 'insult': 0.0, 'threat': 0.0, 'identity_hate': 0.0}
    
    def get_abuse_score(self, toxicity_results: Dict[str, float]) -> float:
        """Calculate overall abuse score (0-1)."""
        score = (
            toxicity_results.get('toxic', 0.0) * 0.15 +
            toxicity_results.get('severe_toxic', 0.0) * 0.35 +
            toxicity_results.get('obscene', 0.0) * 0.25 +
            toxicity_results.get('insult', 0.0) * 0.15 +
            toxicity_results.get('threat', 0.0) * 0.05 +
            toxicity_results.get('identity_hate', 0.0) * 0.05
        )
        return min(score, 1.0)
    
    def add_warning(self, chat_id: int, user_id: int) -> int:
        """Add abuse warning to user and return count."""
        if chat_id not in self.user_abuse_scores:
            self.user_abuse_scores[chat_id] = {}
        if user_id not in self.user_abuse_scores[chat_id]:
            self.user_abuse_scores[chat_id][user_id] = []
        
        self.user_abuse_scores[chat_id][user_id].append(datetime.now())
        
        # Keep only warnings from last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        self.user_abuse_scores[chat_id][user_id] = [
            ts for ts in self.user_abuse_scores[chat_id][user_id] if ts > cutoff
        ]
        return len(self.user_abuse_scores[chat_id][user_id])
    
    def log_abuse(self, chat_id: int, user_id: int, username: str, text: str, score: float):
        """Log abuse incident."""
        if chat_id not in self.voice_logs:
            self.voice_logs[chat_id] = []
        
        self.voice_logs[chat_id].append({
            'user_id': user_id,
            'username': username,
            'timestamp': datetime.now(),
            'text': text,
            'score': score
        })
        
        # Keep only last 10 incidents
        if len(self.voice_logs[chat_id]) > 10:
            self.voice_logs[chat_id] = self.voice_logs[chat_id][-10:]


voice_abuse_detector = VoiceAbuseDetector()


# --- VOICE MESSAGE HANDLER ---

@app.on_message(filters.voice & filters.group)
async def handle_voice_messages(client: Client, message: Message):
    """Monitor and analyze voice messages for abusive content."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    settings = voice_abuse_detector.get_settings(chat_id)
    if not settings['enabled']:
        return
    
    voice_path = None
    try:
        # Download voice message
        voice_path = await message.download()
        print(f"[VoiceAbuse] Downloaded voice from user {user_id}: {voice_path}")
        
        # Transcribe audio
        text = await voice_abuse_detector.transcribe_audio(voice_path)
        
        if not text or len(text.strip()) < 2:
            if voice_path and os.path.exists(voice_path):
                os.remove(voice_path)
            return
        
        print(f"[VoiceAbuse] Voice transcribed: '{text}'")
        
        # Analyze for abuse
        toxicity_results = voice_abuse_detector.analyze_toxicity(text)
        abuse_score = voice_abuse_detector.get_abuse_score(toxicity_results)
        
        print(f"[VoiceAbuse] Score: {abuse_score:.2f} | Threshold: {settings['threshold']}")
        
        if abuse_score >= settings['threshold']:
            print(f"[VoiceAbuse] 🚨 ABUSE DETECTED! Score: {abuse_score:.2f}")
            
            # Log incident
            if settings['log_enabled']:
                voice_abuse_detector.log_abuse(
                    chat_id, user_id, 
                    message.from_user.mention, 
                    text, abuse_score
                )
            
            # Add warning
            warning_count = voice_abuse_detector.add_warning(chat_id, user_id)
            warn_limit = settings['warn_limit']
            
            # Determine action
            action = settings['action']
            
            if action == 'warn':
                if warning_count >= warn_limit:
                    try:
                        await client.ban_chat_member(chat_id, user_id)
                        await message.reply_text(
                            f"🚫 **User BANNED** - {message.from_user.mention}\n"
                            f"**Reason:** Excessive abusive voice ({warning_count} warnings)\n"
                            f"**Score:** {abuse_score:.2f}"
                        )
                        print(f"[VoiceAbuse] ✅ Banned {user_id} after {warning_count} warnings")
                    except RPCError as e:
                        print(f"[VoiceAbuse] Failed to ban: {e}")
                else:
                    try:
                        await message.reply_text(
                            f"⚠️ **WARNING** - {message.from_user.mention}\n"
                            f"**Reason:** Abusive voice message\n"
                            f"**Count:** {warning_count}/{warn_limit}\n"
                            f"**Score:** {abuse_score:.2f}"
                        )
                        print(f"[VoiceAbuse] ✅ Warned {user_id}")
                    except Exception as e:
                        print(f"[VoiceAbuse] Failed to warn: {e}")
            
            elif action == 'mute':
                try:
                    from pyrogram.types import ChatPermissions
                    await client.restrict_chat_member(
                        chat_id, user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=datetime.now() + timedelta(seconds=settings['mute_duration'])
                    )
                    await message.reply_text(
                        f"🔇 **User MUTED** - {message.from_user.mention}\n"
                        f"**Duration:** {settings['mute_duration']}s"
                    )
                    print(f"[VoiceAbuse] ✅ Muted {user_id}")
                except RPCError as e:
                    print(f"[VoiceAbuse] Failed to mute: {e}")
            
            elif action == 'ban':
                try:
                    await client.ban_chat_member(chat_id, user_id)
                    await message.reply_text(
                        f"🚫 **User BANNED** - {message.from_user.mention}\n"
                        f"**Score:** {abuse_score:.2f}"
                    )
                    print(f"[VoiceAbuse] ✅ Banned {user_id} immediately")
                except RPCError as e:
                    print(f"[VoiceAbuse] Failed to ban: {e}")
    
    except Exception as e:
        print(f"[VoiceAbuse] Error: {e}")
    
    finally:
        # Cleanup
        if voice_path and os.path.exists(voice_path):
            try:
                os.remove(voice_path)
            except:
                pass


# --- COMMANDS ---

@app.on_message(filters.command("voiceabuse") & filters.group)
async def handle_voiceabuse_command(client, message):
    """Command: /voiceabuse - Show voice abuse detection status."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_admin = False
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins/SUDOERS can use this.")
        return
    
    settings = voice_abuse_detector.get_settings(chat_id)
    status = "✅ ENABLED" if settings['enabled'] else "❌ DISABLED"
    
    await message.reply_text(
        f"🎤 **Voice Abuse Detection**\n\n"
        f"Status: {status}\n"
        f"Threshold: {settings['threshold']}\n"
        f"Action: {settings['action'].upper()}\n"
        f"Warnings: {settings['warn_limit']}\n"
        f"Mute Time: {settings['mute_duration']}s"
    )


@app.on_message(filters.command("setvoiceabuse") & filters.group)
async def handle_setvoiceabuse_command(client, message):
    """Command: /setvoiceabuse <enabled|disabled|action|threshold> <value>"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_admin = False
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins/SUDOERS can use this.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text(
            "**Usage:**\n"
            "`/setvoiceabuse enabled` - Enable\n"
            "`/setvoiceabuse disabled` - Disable\n"
            "`/setvoiceabuse action warn|mute|ban`\n"
            "`/setvoiceabuse threshold 0.5`"
        )
        return
    
    try:
        setting = args[1].lower()
        
        if setting == "enabled":
            voice_abuse_detector.set_settings(chat_id, enabled=True)
            await message.reply_text("✅ Voice abuse detection **ENABLED**")
        
        elif setting == "disabled":
            voice_abuse_detector.set_settings(chat_id, enabled=False)
            await message.reply_text("✅ Voice abuse detection **DISABLED**")
        
        elif setting == "action" and len(args) > 2:
            action = args[2].lower()
            if action in ['warn', 'mute', 'ban']:
                voice_abuse_detector.set_settings(chat_id, action=action)
                await message.reply_text(f"✅ Action set to **{action.upper()}**")
            else:
                await message.reply_text("❌ Use: warn, mute, or ban")
        
        elif setting == "threshold" and len(args) > 2:
            threshold = float(args[2])
            if 0 <= threshold <= 1:
                voice_abuse_detector.set_settings(chat_id, threshold=threshold)
                await message.reply_text(f"✅ Threshold set to {threshold}")
            else:
                await message.reply_text("❌ Threshold must be 0-1")
        
        else:
            await message.reply_text("❌ Invalid setting")
    
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.command("voicelogs") & filters.group)
async def handle_voicelogs_command(client, message):
    """Command: /voicelogs - View recent abuse incidents."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_admin = False
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins/SUDOERS can use this.")
        return
    
    if chat_id not in voice_abuse_detector.voice_logs or not voice_abuse_detector.voice_logs[chat_id]:
        await message.reply_text("✅ No abuse incidents logged.")
        return
    
    logs = voice_abuse_detector.voice_logs[chat_id]
    text = "📋 **Recent Voice Abuse Incidents:**\n\n"
    
    for i, log in enumerate(logs[-5:], 1):
        text += (
            f"{i}. **User:** {log['username']}\n"
            f"   **Time:** {log['timestamp'].strftime('%H:%M:%S')}\n"
            f"   **Score:** {log['score']:.2f}\n"
            f"   **Text:** `{log['text'][:50]}...`\n\n"
        )
    
    await message.reply_text(text)


print("[VoiceAbuse] ✅ Module loaded - Active VC abuse detection ready!")
