import base64
import datetime
import io
import json
import os
import re
import tempfile
import time

import requests
from flask import Flask, jsonify, render_template, request, send_file, send_from_directory
from moviepy import ColorClip, CompositeVideoClip, TextClip, VideoFileClip
from PIL import Image, ImageFont, ImageOps

app = Flask(__name__)

MINIMAX_URL = os.environ.get(
    "ANTHROPIC_BASE_URL", "https://api.minimax.io/anthropic"
) + "/v1/messages"
MINIMAX_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("MILLY_MODEL", "MiniMax-M3.1-Flash")

ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/flows/video"
VIDEO_MODEL = os.environ.get("MILLY_VIDEO_MODEL", "bytedance-seedance-v2.5")

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")
DEMO_VIDEO = os.path.join(EXAMPLES_DIR, "video/generic_pillow.mp4")
MARKETPLACE_JSON = os.path.join(EXAMPLES_DIR, "marketplace.json")


def chat(messages, max_tokens=1024):
    resp = requests.post(
        MINIMAX_URL,
        headers={
            "x-api-key": MINIMAX_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={"model": MODEL, "max_tokens": max_tokens, "messages": messages},
        timeout=120,
    )
    resp.raise_for_status()
    body = resp.json()
    return "".join(
        block.get("text", "")
        for block in body.get("content", [])
        if block.get("type") == "text"
    )


def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"model did not return JSON: {text[:200]}")
    return json.loads(match.group(0))


@app.errorhandler(ValueError)
def bad_model_output(e):
    return jsonify({"error": str(e)}), 502


def image_to_b64(file_storage, max_px=1024):
    img = ImageOps.exif_transpose(Image.open(file_storage.stream)).convert("RGB")
    img.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()


class BannerError(Exception):
    pass


BANNER_BLUE = (0, 56, 184)  # page blue #0038b8


def banner_font():
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return "Arial"


def format_price(raw):
    text = raw.strip()
    if text.startswith("$"):
        return text
    try:
        value = float(text.replace(",", ""))
    except ValueError:
        return text
    if value.is_integer():
        return f"${int(value)}"
    return f"${value:.2f}"


def banner_text_clip(text, font, font_size):
    # Pillow 11 dropped the metric MoviePy uses to size TextClip, so the
    # default clip is shorter than the font and the baseline falls off the bottom.
    face = ImageFont.truetype(font, font_size)
    ascent, descent = face.getmetrics()
    pad_y = max(2, font_size // 16)
    return TextClip(
        font=font,
        text=text,
        font_size=font_size,
        color="white",
        size=(None, ascent + descent + pad_y),
        vertical_align="top",
    )


def fit_banner_text(name, price_text, font, width, banner_h):
    pad_x = max(12, int(width * 0.03))
    gap = max(16, int(width * 0.04))
    font_size = max(12, int(banner_h * 0.46))
    while True:
        name_clip = banner_text_clip(name, font, font_size)
        price_clip = banner_text_clip(price_text, font, font_size)
        fits = (
            name_clip.w + price_clip.w + pad_x * 2 + gap <= width
            and name_clip.h <= banner_h
            and price_clip.h <= banner_h
        )
        if fits or font_size <= 12:
            return name_clip, price_clip, pad_x
        name_clip.close()
        price_clip.close()
        font_size -= 2


def compose_banner(video, name, price_text):
    width, height = video.size
    banner_h = max(36, int(round(height * 0.14)))
    if banner_h > height // 3:
        banner_h = max(1, height // 3)
    duration = video.duration
    name_clip, price_clip, pad_x = fit_banner_text(
        name, price_text, banner_font(), width, banner_h
    )
    name_clip = name_clip.with_duration(duration).with_position((pad_x, "center"))
    price_clip = price_clip.with_duration(duration).with_position(
        (width - pad_x - price_clip.w, "center")
    )
    bar = CompositeVideoClip(
        [
            ColorClip(size=(width, banner_h), color=BANNER_BLUE, duration=duration),
            name_clip,
            price_clip,
        ],
        size=(width, banner_h),
    ).with_position((0, height - banner_h))
    return CompositeVideoClip([video, bar], size=(width, height))


def render_price_banner(video_bytes, filename, name, price_text):
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}:
        ext = ".mp4"
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in" + ext)
        dst = os.path.join(tmp, "out.mp4")
        with open(src, "wb") as handle:
            handle.write(video_bytes)
        video = None
        try:
            try:
                video = VideoFileClip(src)
            except Exception as exc:
                raise BannerError("could not read video file") from exc
            if not video.duration or video.w < 2 or video.h < 2:
                raise BannerError("could not read video file")
            final = compose_banner(video, name, price_text)
            write_kwargs = {
                "codec": "libx264",
                "fps": video.fps or 24,
                "preset": "veryfast",
                "logger": None,
                "pixel_format": "yuv420p",
            }
            if video.audio is not None:
                write_kwargs["audio_codec"] = "aac"
                write_kwargs["temp_audiofile"] = os.path.join(tmp, "audio.m4a")
            else:
                write_kwargs["audio"] = False
            final.write_videofile(dst, **write_kwargs)
        finally:
            if video is not None:
                video.close()
        with open(dst, "rb") as handle:
            return handle.read()


@app.get("/")
def index():
    return render_template("index.html", studio_enabled=bool(ELEVENLABS_KEY))


@app.get("/demo-video")
def demo_video():
    return send_file(DEMO_VIDEO, mimetype="video/mp4")


@app.get("/api/marketplace")
def marketplace():
    with open(MARKETPLACE_JSON) as f:
        return jsonify(json.load(f))


@app.get("/examples/images/<path:fname>")
def example_image(fname):
    return send_from_directory(os.path.join(EXAMPLES_DIR, "images"), fname)


@app.get("/examples/video/<path:fname>")
def example_video(fname):
    return send_from_directory(os.path.join(EXAMPLES_DIR, "video"), fname)


@app.post("/api/classify")
def classify():
    if "image" not in request.files:
        return jsonify({"error": "no image uploaded"}), 400
    try:
        img_b64 = image_to_b64(request.files["image"])
    except Exception:
        return jsonify({"error": "could not read image file"}), 400
    text = chat(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are the Classifier stage of Milly Bays, an app that "
                            "helps people sell household clutter. Identify the main "
                            "object in this photo. Respond with ONLY a JSON object: "
                            '{"name": "short item name", "description": "1-2 factual '
                            'sentences including brand, color, material if visible", '
                            '"condition": "new|like-new|good|fair|poor"}'
                        ),
                    },
                ],
            }
        ]
    )
    return jsonify(extract_json(text))


@app.post("/api/price")
def price():
    item = request.get_json(force=True)
    today = datetime.date.today().isoformat()
    text = chat(
        [
            {
                "role": "user",
                "content": (
                    "You are the Pricer stage of Milly Bays. Estimate the used resale "
                    f"value of this item on Facebook Marketplace in USD. Today is {today}.\n"
                    f"Item: {item.get('name')}\n"
                    f"Description: {item.get('description')}\n"
                    f"Condition: {item.get('condition')}\n"
                    "Respond with ONLY a JSON object: "
                    '{"suggested_price": number, "price_low": number, '
                    '"price_high": number, "reasoning": "one sentence"}'
                ),
            }
        ]
    )
    return jsonify(extract_json(text))


@app.post("/api/write")
def write():
    item = request.get_json(force=True)
    text = chat(
        [
            {
                "role": "user",
                "content": (
                    "You are the Writer stage of Milly Bays. Given this item and its "
                    "asking price, produce two things:\n"
                    "1. A Facebook Marketplace listing: a punchy title (max 80 chars) "
                    "and a friendly 2-3 sentence description mentioning condition.\n"
                    "2. A transcript for a 10-15 second over-the-top Billy Mays style "
                    "TV ad. High energy, problem-solution formula, ends with a call "
                    "to action and the price. Write only the spoken words.\n"
                    f"Item: {item.get('name')}\n"
                    f"Description: {item.get('description')}\n"
                    f"Condition: {item.get('condition')}\n"
                    f"Price: ${item.get('suggested_price')}\n"
                    "Respond with ONLY a JSON object: "
                    '{"listing_title": "...", "listing_description": "...", '
                    '"transcript": "..."}'
                ),
            }
        ],
        max_tokens=2048,
    )
    return jsonify(extract_json(text))


@app.post("/api/studio")
def studio():
    item = request.get_json(force=True)
    if not ELEVENLABS_KEY:
        return jsonify({"video_url": None})
    headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
    prompt = (
        "A loud, high-energy TV infomercial pitchman in the style of Billy Mays "
        f"enthusiastically sells a {item.get('name')}. Bright studio lighting, "
        "bold gestures, speaking directly to camera. He says: "
        f"{item.get('transcript')}"
    )
    created = requests.post(
        ELEVENLABS_URL,
        headers=headers,
        json={
            "model_id": VIDEO_MODEL,
            "prompt": prompt,
            "duration_secs": 10,
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "generate_audio": True,
        },
        timeout=60,
    )
    created.raise_for_status()
    gen_id = created.json()["id"]
    deadline = time.time() + 300
    while time.time() < deadline:
        status = requests.get(f"{ELEVENLABS_URL}/{gen_id}", headers=headers, timeout=30)
        status.raise_for_status()
        body = status.json()
        if body["status"] == "completed":
            return jsonify({"video_url": body["content_url"]})
        if body["status"] == "failed":
            return jsonify({"error": body.get("error_message", "video failed")}), 502
        time.sleep(5)
    return jsonify({"error": "video generation timed out"}), 504


@app.post("/api/banner")
def banner():
    upload = request.files.get("video")
    if upload is None or not upload.filename:
        return jsonify({"error": "no video uploaded"}), 400
    name = (request.form.get("name") or "").strip()
    price_raw = (request.form.get("price") or "").strip()
    if not name or not price_raw:
        return jsonify({"error": "name and price are required"}), 400
    data = upload.read()
    if not data:
        return jsonify({"error": "no video uploaded"}), 400
    try:
        out = render_price_banner(data, upload.filename, name, format_price(price_raw))
    except BannerError as exc:
        return jsonify({"error": str(exc)}), 400
    return send_file(
        io.BytesIO(out),
        mimetype="video/mp4",
        download_name="banner.mp4",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
