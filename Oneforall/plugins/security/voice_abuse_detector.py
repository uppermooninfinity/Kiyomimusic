"""
AI-Powered Voice Abuse Detection System
Detects abusive speech in voice chats using speech recognition and toxicity detection.
Supports English and Hindi abusive words with automatic actions (ban/mute/warn).
"""

import asyncio
import os
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
    from Oneforall.core.userbot import assistants, assistantids
except ImportError as e:
    raise ImportError(f"Could not import required modules: {e}")


class VoiceAbuseDetector:
    """AI-powered detection system for abusive speech in voice chats."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        try:
            self.toxicity_model = Detoxify('original')
            self.ai_enabled = True
        except Exception as e:
            print(f"[VoiceAbuse] Detoxify model not available: {e}")
            self.ai_enabled = False
        
        self.TOXICITY_THRESHOLD = 0.6
        self.active_monitoring = {}
        self.user_abuse_scores = {}
        self.voice_muted = {}
        self.detection_settings = {}
        self.voice_logs = {}
        
        # Multilingual abusive words dictionary
        self.abusive_words_en = {
            "fuck", "shit", "bitch", "asshole", "bastard", "crap", "damn",
            "hell", "piss", "ass", "dick", "motherfucker", "goddamn", "cunt",
            "twat", "arsehole", "bollocks", "bugger", "dammit", "frick",
            "douchebag", "jackass", "jerk", "prick", "slut", "whore"
        }
        
        # Hindi abusive words
        self.abusive_words_hi = {
            "chutiya", "madarchod", "bhenchod", "saala", "harami", "nalayak",
            "gawaar", "ullu", "gadha", "kumara", "behaya", "badmash", "randi",
            "khota", "mera_lund", "tere_maa_ki", "gangbang", "immorals"
        }
    
    def get_settings(self, chat_id: int) -> dict:
        """Get voice abuse detection settings for a chat."""
        if chat_id not in self.detection_settings:
            self.detection_settings[chat_id] = {
                'enabled': True,
                'threshold': self.TOXICITY_THRESHOLD,
                'action': 'warn',  # warn, mute, ban
                'warn_limit': 2,
                'mute_duration': 1800,
                'log_enabled': True,
                'ai_model': 'detoxify',
                'use_userbot': True,
                'monitor_active': False
            }
        return self.detection_settings[chat_id]
    
    def set_settings(self, chat_id: int, **kwargs):
        """Update voice abuse detection settings."""
        settings = self.get_settings(chat_id)
        for key, value in kwargs.items():
            if key in settings:
                settings[key] = value
    
    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Convert audio file to text using speech recognition."""
        try:
            if not audio_path.endswith('.wav'):
                try:
                    audio = AudioSegment.from_file(audio_path)
                    wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                    audio.export(wav_path, format='wav')
                    audio_path = wav_path
                except Exception as e:
                    print(f"[VoiceAbuse] Audio conversion failed: {e}")
                    return None
            
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
                print(f"[VoiceAbuse] Transcribed (EN): {text}")
                return text
            except sr.UnknownValueError:
                try:
                    # Try Hindi recognition
                    text = self.recognizer.recognize_google(audio, language='hi-IN')
                    print(f"[VoiceAbuse] Transcribed (HI): {text}")
                    return text
                except:
                    return None
            except sr.RequestError as e:
                print(f"[VoiceAbuse] API error: {e}")
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    return text
                except:
                    return None
        except Exception as e:
            print(f"[VoiceAbuse] Error: {e}")
            return None
    
    def analyze_toxicity(self, text: str) -> Dict[str, float]:
        """Analyze text for toxicity using AI model and keyword matching."""
        if not text:
            return {'toxic': 0.0, 'severe_toxic': 0.0, 'obscene': 0.0, 'insult': 0.0, 'threat': 0.0, 'identity_hate': 0.0}
        
        # Check multilingual words first
        text_lower = text.lower()
        has_en_abuse = any(word in text_lower for word in self.abusive_words_en)
        has_hi_abuse = any(word in text_lower for word in self.abusive_words_hi)
        
        if has_en_abuse or has_hi_abuse:
            return {'toxic': 0.8, 'severe_toxic': 0.7, 'obscene': 0.9, 'insult': 0.85, 'threat': 0.5, 'identity_hate': 0.6}
        
        # Use AI model if enabled
        if self.ai_enabled:
            try:
                results = self.toxicity_model.predict(text)
                return results
            except Exception as e:
                print(f"[VoiceAbuse] Analysis error: {e}")
                return {'toxic': 0.0, 'severe_toxic': 0.0, 'obscene': 0.0, 'insult': 0.0, 'threat': 0.0, 'identity_hate': 0.0}
        
        return {'toxic': 0.0, 'severe_toxic': 0.0, 'obscene': 0.0, 'insult': 0.0, 'threat': 0.0, 'identity_hate': 0.0}
    
    def get_abuse_score(self, toxicity_results: Dict[str, float]) -> float:
        """Calculate overall abuse score (0-1)."""
        score = (
            toxicity_results.get('toxic', 0.0) * 0.2 +
            toxicity_results.get('severe_toxic', 0.0) * 0.4 +
            toxicity_results.get('obscene', 0.0) * 0.2 +
            toxicity_results.get('insult', 0.0) * 0.1 +
            toxicity_results.get('threat', 0.0) * 0.5 +
            toxicity_results.get('identity_hate', 0.0) * 0.4
        )
        return min(score, 1.0)
    
    def add_warning(self, chat_id: int, user_id: int) -> int:
        """Add abuse warning to user."""
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
    
    try:
        # Download voice message
        voice_path = await message.download()
        
        # Transcribe audio
        text = await voice_abuse_detector.transcribe_audio(voice_path)
        
        if not text:
            print(f"[VoiceAbuse] Could not transcribe voice from user {user_id}")
            if os.path.exists(voice_path):
                os.remove(voice_path)
            return
        
        print(f"[VoiceAbuse] Voice detected: '{text}' from user {user_id}")
        
        # Analyze for abuse
        toxicity_results = voice_abuse_detector.analyze_toxicity(text)
        abuse_score = voice_abuse_detector.get_abuse_score(toxicity_results)
        
        print(f"[VoiceAbuse] Abuse score: {abuse_score} (threshold: {settings['threshold']})")
        
        if abuse_score >= settings['threshold']:
            print(f"[VoiceAbuse] 🚨 Abuse detected! Score: {abuse_score}")
            
            # Log the incident
            if settings['log_enabled']:
                voice_abuse_detector.voice_logs[chat_id] = {
                    'user_id': user_id,
                    'username': message.from_user.mention,
                    'timestamp': datetime.now(),
                    'text': text,
                    'score': abuse_score
                }
            
            # Add warning
            warning_count = voice_abuse_detector.add_warning(chat_id, user_id)
            
            # Get user member status
            try:
                member = await client.get_chat_member(chat_id, user_id)
                is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
            except:
                is_admin = False
            
            # Take action
            action = settings['action']
            warn_limit = settings['warn_limit']
            
            if action == 'warn':
                if warning_count >= warn_limit:
                    try:
                        await client.ban_chat_member(chat_id, user_id)
                        await message.reply_text(
                            f"🚫 **User Banned** - {message.from_user.mention}\n"
                            f"Reason: Abusive voice message (Warnings exceeded)\n"
                            f"Score: {abuse_score:.2f}"
                        )
                        print(f"[VoiceAbuse] Banned user {user_id} after {warning_count} warnings")
                    except RPCError as e:
                        print(f"[VoiceAbuse] Failed to ban: {e}")
                else:
                    try:
                        await message.reply_text(
                            f"⚠️ **Warning** - {message.from_user.mention}\n"
                            f"Reason: Abusive voice message\n"
                            f"Warnings: {warning_count}/{warn_limit}\n"
                            f"Content Score: {abuse_score:.2f}"
                        )
                        print(f"[VoiceAbuse] Warned user {user_id} (Warning {warning_count}/{warn_limit})")
                    except Exception as e:
                        print(f"[VoiceAbuse] Failed to send warning: {e}")
            
            elif action == 'mute':
                try:
                    from pyrogram.types import ChatPermissions
                    await client.restrict_chat_member(
                        chat_id,
                        user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=datetime.now() + timedelta(seconds=settings['mute_duration'])
                    )
                    await message.reply_text(
                        f"🔇 **User Muted** - {message.from_user.mention}\n"
                        f"Duration: {settings['mute_duration']}s\n"
                        f"Reason: Abusive voice message"
                    )
                    print(f"[VoiceAbuse] Muted user {user_id}")
                except RPCError as e:
                    print(f"[VoiceAbuse] Failed to mute: {e}")
            
            elif action == 'ban':
                try:
                    await client.ban_chat_member(chat_id, user_id)
                    await message.reply_text(
                        f"🚫 **User Banned** - {message.from_user.mention}\n"
                        f"Reason: Abusive voice message\n"
                        f"Score: {abuse_score:.2f}"
                    )
                    print(f"[VoiceAbuse] Banned user {user_id}")
                except RPCError as e:
                    print(f"[VoiceAbuse] Failed to ban: {e}")
        
        # Cleanup
        if os.path.exists(voice_path):
            os.remove(voice_path)
    
    except Exception as e:
        print(f"[VoiceAbuse] Error processing voice message: {e}")
        if 'voice_path' in locals() and os.path.exists(voice_path):
            os.remove(voice_path)


# --- COMMANDS ---

@app.on_message(filters.command("voiceabuse") & filters.group)
async def handle_voiceabuse_command(client, message):
    """Command: /voiceabuse - Show voice abuse detection status."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    print(f"[VoiceAbuse] /voiceabuse command received from {user_id} in chat {chat_id}")
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        print(f"[VoiceAbuse] Error checking member: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins can use this command.")
        return
    
    settings = voice_abuse_detector.get_settings(chat_id)
    status = "✅ ENABLED" if settings['enabled'] else "❌ DISABLED"
    
    await message.reply_text(
        f"🎤 **Voice Abuse Detection**\n\n"
        f"Status: {status}\n"
        f"Threshold: {settings['threshold']}\n"
        f"Action: {settings['action'].upper()}\n"
        f"Warn Limit: {settings['warn_limit']}\n"
        f"Mute Duration: {settings['mute_duration']}s\n"
        f"AI Model: {settings['ai_model']}\n"
        f"Userbot Enabled: {'✅' if settings['use_userbot'] else '❌'}"
    )
    print(f"[VoiceAbuse] Sent voice abuse status to user {user_id}")


@app.on_message(filters.command("setvoiceabuse") & filters.group)
async def handle_setvoiceabuse_command(client, message):
    """Command: /setvoiceabuse <enabled|disabled|threshold|action> <value>"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    print(f"[VoiceAbuse] /setvoiceabuse command received from {user_id} in chat {chat_id}")
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        print(f"[VoiceAbuse] Error checking member: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")
        return
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins can use this command.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: `/setvoiceabuse <enabled|disabled|threshold|action|warnlimit> <value>`")
        return
    
    try:
        setting = args[1].lower()
        
        if setting == "enabled":
            voice_abuse_detector.set_settings(chat_id, enabled=True)
            await message.reply_text("✅ Voice abuse detection **ENABLED**")
        
        elif setting == "disabled":
            voice_abuse_detector.set_settings(chat_id, enabled=False)
            await message.reply_text("✅ Voice abuse detection **DISABLED**")
        
        elif setting == "threshold" and len(args) > 2:
            threshold = float(args[2])
            if 0 <= threshold <= 1:
                voice_abuse_detector.set_settings(chat_id, threshold=threshold)
                await message.reply_text(f"✅ Threshold set to {threshold}")
            else:
                await message.reply_text("❌ Threshold must be between 0 and 1")
        
        elif setting == "action" and len(args) > 2:
            action = args[2].lower()
            if action in ['warn', 'mute', 'ban']:
                voice_abuse_detector.set_settings(chat_id, action=action)
                await message.reply_text(f"✅ Action set to **{action.upper()}**")
            else:
                await message.reply_text("❌ Invalid action. Use: warn, mute, ban")
        
        elif setting == "warnlimit" and len(args) > 2:
            limit = int(args[2])
            voice_abuse_detector.set_settings(chat_id, warn_limit=limit)
            await message.reply_text(f"✅ Warning limit set to {limit}")
        
        else:
            await message.reply_text("❌ Invalid setting or missing value.")
    
    except ValueError as e:
        await message.reply_text(f"❌ Invalid value type: {str(e)}")
    except Exception as e:
        print(f"[VoiceAbuse] Error in setvoiceabuse: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.command("voicelogs") & filters.group)
async def handle_voicelogs_command(client, message):
    """Command: /voicelogs - Show recent voice abuse incidents."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_admin = False
    
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS
    if not (is_admin or is_owner_or_sudo):
        await message.reply_text("❌ Only admins can use this command.")
        return
    
    if chat_id not in voice_abuse_detector.voice_logs:
        await message.reply_text("✅ No abuse incidents logged.")
        return
    
    log = voice_abuse_detector.voice_logs[chat_id]
    await message.reply_text(
        f"📋 **Recent Voice Abuse Incident**\n\n"
        f"User: {log['username']}\n"
        f"Time: {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Score: {log['score']:.2f}\n"
        f"Content: `{log['text']}`"
    )


print("[VoiceAbuse] Module loaded successfully with multilingual support!")
