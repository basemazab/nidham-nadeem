import asyncio
import base64
import io
import json
import os
import re
import time
import wave

import edge_tts
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")

TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")
EDGE_VOICE = os.getenv("EDGE_VOICE", "ar-EG-SalmaNeural")
ORPHEUS_MODEL = os.getenv("ORPHEUS_MODEL", "canopylabs/orpheus-arabic-saudi")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVEN_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
GEMINI_VOICE = os.getenv("GEMINI_VOICE", "Kore")
HAKIM_KEY = os.getenv("HAKIM_API_KEY", "")
HAKIM_MODEL = os.getenv("HAKIM_MODEL", "hakim-flash-v1")
HAKIM_VOICE = os.getenv("HAKIM_VOICE", "yusuf-egyptian")
HAKIM_SPEED = float(os.getenv("HAKIM_SPEED", "0.9"))
HAKIM_FORMAT = os.getenv("HAKIM_FORMAT", "wav")
ACCESS_KEY = os.getenv("ACCESS_KEY", "")

SYSTEM_PROMPT = """انت "نديم" — مندوب مبيعات صوتي لمنظومة NidhamHR، نظام موارد بشرية مصري.

أهم قاعدة: اتكلم بالمصري العامي اللي بيتهدى بيه في الشارع المصري — "إزيك، أهو، ماشي، تمام، يعني إيه، طب". ممنوع تمامًا الفصحى أو اللغة الكتابية.

شخصيتك: ودود، مفعم بطاقة، بتسمع كويس. ردودك قصيرة جدًا (جملتين لأربع جمل قصيرة) لأنك بتتكلم مش بتكتب. تجنب الأرقام والرموز والاختصارات الإنجليزية في الكلام عشان النطق يطلع سليم.

معرفتك بالمنتج:
- NidhamHR نظام إدارة موارد بشرية سحابي معمول خصيصًا للسوق المصري.
- الرواتب والمرتبات متوافقة مع قانون العمل المصري 12 لسنة 2003 (مكافأة نهاية الخدمة، بدلات الإجازات، كل الحسابات أوتوماتيك).
- التأمينات الاجتماعية: حساب الاشتراكات تلقائي ونماذج جاهزة لمصلحة التأمينات.
- الحضور والانصراف: ربط بأجهزة البصمة ZKTeco وتقارير تأخير وإضافي جاهزة.
- الإجازات: الموظف يطلب من موبايله والمدير يعتمد، والأرصدة بتتحسب لوحدها.
- العقود: عقود عمل عربية، إنذارات، تقييم أداء.
- شغل بالفروع والورديات المختلفة.
- فيه تطبيق موبايل للموظفين.

قواعد لازم تلتزم بيها:
1. لو سألوا عن أسعار أو تفاصيل تعاقدية: قول "الأسعار بتختلف حسب حجم الشركة، وهحولك زميل بشري يظبطلك العرض على مقاسك" — ممنوع نهائيًا تخترع أرقام.
2. لو سؤال خارج معرفتك: اعتذر بصراحة وقول هتحول لمسؤول.
3. هدفك في كل محادثة: توصل العميل لحجز ديمو، وخد منه اسمه وشركته ورقم تليفونه بشكل طبيعي مش مستفز.
4. لو العميل اتكلم إنجليزي رد عليه بالمصري برضه بس بسيط."""

sessions = {}

app = FastAPI(title="Nadeem Voice")


def transcribe(audio_bytes):
    r = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        files={
            "file": ("speech.webm", audio_bytes, "audio/webm"),
            "model": (None, WHISPER_MODEL),
            "language": (None, "ar"),
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("text", "").strip()


def ask_groq_stream_tokens(history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:]
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 250,
            "stream": True,
        },
        stream=True,
        timeout=60,
    )
    r.raise_for_status()
    for line in r.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8")
        if line.startswith("data: ") and line != "data: [DONE]":
            chunk = json.loads(line[6:])
            tok = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            if tok:
                yield tok


async def tts_edge(text):
    mp3 = bytearray()
    comm = edge_tts.Communicate(text, EDGE_VOICE)
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            mp3.extend(chunk["data"])
    return "mp3", bytes(mp3)


def tts_orpheus(text):
    r = requests.post(
        "https://api.groq.com/openai/v1/audio/speech",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": ORPHEUS_MODEL, "input": text, "response_format": "mp3"},
        timeout=60,
    )
    r.raise_for_status()
    return "mp3", r.content


def tts_elevenlabs(text):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}",
        headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=60,
    )
    r.raise_for_status()
    return "mp3", r.content


def tts_gemini(text):
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_KEY, "Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": "قل بنبرة ودودة مصرية واضحة: " + text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GEMINI_VOICE}}
                },
            },
        },
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    part = data["candidates"][0]["content"]["parts"][0]
    return "pcm", base64.b64decode(part["inlineData"]["data"])


def tts_hakim(text):
    r = requests.post(
        "https://api.tryhakim.ai/v1/audio/speech",
        headers={"Authorization": f"Bearer {HAKIM_KEY}", "Content-Type": "application/json"},
        json={
            "model": HAKIM_MODEL,
            "voice": HAKIM_VOICE,
            "input": text,
            "response_format": HAKIM_FORMAT,
            "sample_rate": 24000,
            "speed": HAKIM_SPEED,
        },
        timeout=60,
    )
    r.raise_for_status()
    fmt = "wav" if HAKIM_FORMAT == "wav" else "mp3"
    return fmt, r.content


async def tts_one(text):
    last_err = None
    for attempt in range(3):
        try:
            if TTS_ENGINE == "groq_orpheus":
                return await asyncio.to_thread(tts_orpheus, text)
            if TTS_ENGINE == "elevenlabs":
                return await asyncio.to_thread(tts_elevenlabs, text)
            if TTS_ENGINE == "gemini":
                return await asyncio.to_thread(tts_gemini, text)
            if TTS_ENGINE == "hakim":
                return await asyncio.to_thread(tts_hakim, text)
            return await tts_edge(text)
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"TTS فشل بعد 3 محاولات: {last_err}")


def pcm_to_wav(pcm, rate=24000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


@app.get("/")
async def home():
    return FileResponse("static/index.html")


@app.post("/api/talk")
async def talk(file: UploadFile = File(...), session_id: str = Form(...), k: str = Form("")):
    if ACCESS_KEY and k != ACCESS_KEY:
        return JSONResponse({"error": "🔒 كود الدعوة غير صحيح — اطلب اللينك الكامل من ندحم HR"}, status_code=403)

    t0 = time.time()
    audio = await file.read()
    if len(audio) < 1000:
        return JSONResponse({"error": "التسجيل قصير جدًا"}, status_code=400)

    try:
        user_text = await asyncio.to_thread(transcribe, audio)
    except Exception as e:
        return JSONResponse({"error": f"مشكلة في السمع: {e}"}, status_code=500)

    if not user_text:
        return JSONResponse({"error": "معرفتش أسمعك، كرر تاني"}, status_code=200)

    history = sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_text})

    tts_tasks = []
    full_reply = ""
    buf = ""

    def flush_sentence(s):
        s = s.strip()
        if s:
            tts_tasks.append(asyncio.create_task(tts_one(s)))

    try:
        gen = ask_groq_stream_tokens(history)
        while True:
            tok = await asyncio.to_thread(next, gen, None)
            if tok is None:
                break
            full_reply += tok
            buf += tok
            parts = re.split(r"(?<=[.!؟?\n])\s+", buf)
            if len(parts) > 1:
                buf = parts[-1]
                for s in parts[:-1]:
                    flush_sentence(s)
        flush_sentence(buf)
    except Exception as e:
        history.pop()
        return JSONResponse({"error": f"مشكلة في التفكير: {e}"}, status_code=500)

    if not full_reply.strip():
        history.pop()
        return JSONResponse({"error": "مفيش رد، جرب تاني"}, status_code=500)

    history.append({"role": "assistant", "content": full_reply})

    try:
        results = await asyncio.gather(*tts_tasks)
    except Exception as e:
        return JSONResponse({"error": f"مشكلة في الصوت: {e}"}, status_code=500)

    fmt = results[0][0] if results else "mp3"
    payload = b"".join(r[1] for r in results)

    if fmt == "pcm":
        final_audio = pcm_to_wav(payload)
        mime = "audio/wav"
    elif fmt == "wav":
        final_audio = payload
        mime = "audio/wav"
    else:
        final_audio = payload
        mime = "audio/mpeg"

    total = time.time() - t0
    print(f"[توقيت] رد كامل={total:.1f}s | جمل={len(results)} | صوت={len(final_audio)} بايت")

    return {
        "client_text": user_text,
        "reply": full_reply,
        "audio": base64.b64encode(final_audio).decode(),
        "mime": mime,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
