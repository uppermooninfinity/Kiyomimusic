"""
AI-Powered Voice Abuse Detection System
Detects abusive speech in voice chats using speech recognition and toxicity detection.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Dict

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

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
    """AI-powered detection system for abusive speech in voice chats."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        try:
            self.toxicity_model = Detoxify('original')
            self.ai_enabled = True
        except:
            print("[VoiceAbuse] Detoxify model not available.")
            self.ai_enabled = False
        
        self.TOXICITY_THRESHOLD = 0.6
        self.active_monitoring = {}
        self.user_abuse_scores = {}
        self.voice_muted = {}
        self.detection_settings = {}
        self.voice_logs = {}
    
    def get_settings(self, chat_id: int) -> dict:
        """Get voice abuse detection settings for a chat."""
        if chat_id not in self.detection_settings:
            self.detection_settings[chat_id] = {
                'enabled': True,
                'threshold': self.TOXICITY_THRESHOLD,
                'action': 'warn',
                'warn_limit': 2,
                'mute_duration': 1800,
                'log_enabled': True,
                'ai_model': 'detoxify'
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
                text = self.recognizer.recognize_google(audio)
                print(f"[VoiceAbuse] Transcribed: {text}")
                return text
            except sr.UnknownValueError:
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
        """Analyze text for toxicity using AI model."""
        if not self.ai_enabled or not text:
            return {'toxic': 0.0, 'severe_toxic': 0.0, 'obscene': 0.0, 'insult': 0.0, 'threat': 0.0, 'identity_hate': 0.0}
        
        try:
            results = self.toxicity_model.predict(text)
            return results
        except Exception as e:
            print(f"[VoiceAbuse] Analysis error: {e}")
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


voice_abuse_detector = VoiceAbuseDetector()

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
        f"Mute Duration: {settings['mute_duration']}s"
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
        await message.reply_text("Usage: `/setvoiceabuse <enabled|disabled|threshold|action> <value>`")
        return
    
    try:
        setting = args[1].lower()
        if setting == "enabled" and len(args) > 2:
            voice_abuse_detector.set_settings(chat_id, enabled=args[2].lower() == "true")
            await message.reply_text("✅ Voice abuse detection updated.")
        elif setting == "disabled" and len(args) > 2:
            voice_abuse_detector.set_settings(chat_id, enabled=False)
            await message.reply_text("✅ Voice abuse detection disabled.")
        elif setting == "threshold" and len(args) > 2:
            threshold = float(args[2])
            voice_abuse_detector.set_settings(chat_id, threshold=threshold)
            await message.reply_text(f"✅ Threshold set to {threshold}")
        elif setting == "action" and len(args) > 2:
            action = args[2].lower()
            if action in ['warn', 'mute', 'ban']:
                voice_abuse_detector.set_settings(chat_id, action=action)
                await message.reply_text(f"✅ Action set to {action}")
            else:
                await message.reply_text("❌ Invalid action. Use: warn, mute, ban")
        else:
            await message.reply_text("❌ Invalid setting.")
    except Exception as e:
        print(f"[VoiceAbuse] Error in setvoiceabuse: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")


print("[VoiceAbuse] Module loaded successfully!")
