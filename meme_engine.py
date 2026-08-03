"""
meme_engine.py — AI Meme Generator Core
Fetches trending topics → Gemini generates meme captions →
Pillow renders memes with classic meme fonts and templates.

Features:
  - 20+ classic meme templates
  - Trending topic detection (RSS + Reddit)
  - AI caption generation (Gemini)
  - Custom text meme creation
  - Multiple meme styles/formats
  - Batch meme generation
  - Meme rating system
"""

import json
import re
import io
import os
import textwrap
import requests
import feedparser
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ── Meme templates ─────────────────────────────────────────────────────────────
MEME_TEMPLATES = {
    "drake":            {"name": "Drake Approves/Rejects",    "format": "two_panel_vertical",  "emoji": "🦉"},
    "distracted_bf":    {"name": "Distracted Boyfriend",      "format": "three_label",          "emoji": "👀"},
    "two_buttons":      {"name": "Two Buttons",               "format": "two_choice",           "emoji": "😰"},
    "brain_expanding":  {"name": "Expanding Brain",           "format": "four_panel",           "emoji": "🧠"},
    "one_does_not":     {"name": "One Does Not Simply",       "format": "caption_bottom",       "emoji": "🧙"},
    "change_my_mind":   {"name": "Change My Mind",            "format": "caption_top",          "emoji": "☕"},
    "this_is_fine":     {"name": "This Is Fine",              "format": "caption_top",          "emoji": "🔥"},
    "surprised_pikachu":{"name": "Surprised Pikachu",         "format": "caption_top",          "emoji": "⚡"},
    "always_has_been":  {"name": "Always Has Been",           "format": "two_panel_dialog",     "emoji": "🌍"},
    "gru_plan":         {"name": "Gru's Plan",                "format": "four_panel",           "emoji": "😏"},
    "success_kid":      {"name": "Success Kid",               "format": "caption_both",         "emoji": "✊"},
    "bad_luck_brian":   {"name": "Bad Luck Brian",            "format": "caption_both",         "emoji": "😬"},
    "roll_safe":        {"name": "Roll Safe",                 "format": "caption_both",         "emoji": "😏"},
    "they_re_the_same": {"name": "They're The Same Picture", "format": "caption_top",          "emoji": "🤷"},
    "first_world":      {"name": "First World Problems",      "format": "caption_both",         "emoji": "😭"},
    "custom":           {"name": "Custom Template",           "format": "caption_both",         "emoji": "✨"},
}

MEME_STYLES = {
    "classic":    {"bg": (0,0,0),       "text": (255,255,255), "stroke": (0,0,0),       "font_size": 36},
    "white_top":  {"bg": (255,255,255), "text": (0,0,0),       "stroke": (255,255,255), "font_size": 32},
    "dank":       {"bg": (0,0,0),       "text": (0,255,0),     "stroke": (0,0,0),       "font_size": 34},
    "reddit":     {"bg": (255,69,0),    "text": (255,255,255), "stroke": (0,0,0),       "font_size": 30},
    "galaxy":     {"bg": (10,10,40),    "text": (200,160,255), "stroke": (10,10,40),    "font_size": 34},
}

# ── Trending topic feeds ───────────────────────────────────────────────────────
TRENDING_FEEDS = {
    "hackernews":  "https://news.ycombinator.com/rss",
    "techcrunch":  "https://techcrunch.com/feed/",
    "reddit_tech": "https://www.reddit.com/r/technology/.rss",
    "reddit_prog": "https://www.reddit.com/r/programming/.rss",
    "reddit_pop":  "https://www.reddit.com/r/popular/.rss",
    "verge":       "https://www.theverge.com/rss/index.xml",
}

MEME_CATEGORIES = [
    "Tech & Programming", "AI & Machine Learning", "Work & Meetings",
    "Monday Mood", "Debugging", "Deadlines", "Coffee & Productivity",
    "Social Media", "Gaming", "Pop Culture", "Life in General",
]


# ── Data structures ────────────────────────────────────────────────────────────
@dataclass
class TrendingTopic:
    title:    str
    source:   str
    url:      str
    category: str


@dataclass
class MemeCaption:
    template:   str
    top_text:   str
    bottom_text: str
    panel_texts: list[str]   # for multi-panel memes
    style:      str
    topic:      str
    humor_type: str          # sarcasm / relatable / absurd / wholesome
    tags:       list[str]


@dataclass
class GeneratedMeme:
    caption:     MemeCaption
    image:       Optional[bytes]   # PNG bytes
    template:    str
    topic:       str
    created_at:  str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


# ── Trending topic fetcher ────────────────────────────────────────────────────
def fetch_trending(max_topics: int = 20) -> list[TrendingTopic]:
    """Fetch trending topics from multiple RSS feeds."""
    topics = []
    for source, url in TRENDING_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                if title and len(title) > 10:
                    # Guess category
                    t = title.lower()
                    if any(w in t for w in ["ai","gpt","llm","model","openai","gemini"]):
                        cat = "AI & Machine Learning"
                    elif any(w in t for w in ["python","code","bug","developer","programming"]):
                        cat = "Tech & Programming"
                    elif any(w in t for w in ["meeting","office","work","boss","deadline"]):
                        cat = "Work & Meetings"
                    elif any(w in t for w in ["game","gaming","steam","xbox","playstation"]):
                        cat = "Gaming"
                    else:
                        cat = "Pop Culture"

                    topics.append(TrendingTopic(
                        title=title,
                        source=source.replace("_"," ").title(),
                        url=entry.get("link",""),
                        category=cat,
                    ))
        except Exception:
            continue

    return topics[:max_topics]


# ── Gemini caption generation ─────────────────────────────────────────────────
def generate_meme_caption(
    topic: str,
    template: str,
    style_hint: str,
    api_key: str,
    custom_context: str = "",
) -> MemeCaption:
    """Generate meme captions for a topic using Gemini."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.9, "max_output_tokens": 600},
    )

    template_info = MEME_TEMPLATES.get(template, MEME_TEMPLATES["custom"])
    fmt = template_info["format"]

    format_instructions = {
        "caption_both":       "top_text: setup/situation, bottom_text: punchline/twist",
        "caption_top":        "top_text: the main joke or statement (bottom_text can be empty)",
        "caption_bottom":     "bottom_text: the main caption (top_text can be empty)",
        "two_panel_vertical": "panel_texts: [rejected thing, accepted thing] — Drake format",
        "four_panel":         "panel_texts: [panel1, panel2, panel3, panel4]",
        "two_choice":         "panel_texts: [option A label, option B label, person sweating description]",
        "three_label":        "panel_texts: [girlfriend label, distracted bf label, new girl label]",
        "two_panel_dialog":   "panel_texts: [astronaut 1 says, astronaut 2 says]",
    }

    prompt = f"""You are a professional meme creator. Create a genuinely funny meme caption.

TOPIC: {topic}
{f'EXTRA CONTEXT: {custom_context}' if custom_context else ''}
MEME TEMPLATE: {template_info['name']}
FORMAT: {format_instructions.get(fmt, 'caption_both')}
STYLE: {style_hint}

Rules:
- Be genuinely funny, relatable, or cleverly absurd
- Keep text SHORT — memes need punchy text (max 8 words per text block)
- Match the classic format of this meme template
- Use internet/tech humor where appropriate
- Don't be offensive or inappropriate

Return ONLY valid JSON:
{{
  "top_text": "<top caption or empty string>",
  "bottom_text": "<bottom caption or empty string>",
  "panel_texts": ["<text for each panel if multi-panel>"],
  "humor_type": "<sarcasm|relatable|absurd|wholesome|dark_humor>",
  "tags": ["<tag1>","<tag2>","<tag3>"]
}}"""

    try:
        r   = model.generate_content(prompt)
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$","",r.text.strip(),flags=re.MULTILINE)
        d   = json.loads(raw.strip())
        return MemeCaption(
            template=template,
            top_text=d.get("top_text","").upper(),
            bottom_text=d.get("bottom_text","").upper(),
            panel_texts=[t.upper() for t in d.get("panel_texts",[])],
            style=style_hint,
            topic=topic,
            humor_type=d.get("humor_type","relatable"),
            tags=d.get("tags",[])[:5],
        )
    except Exception:
        return MemeCaption(
            template=template,
            top_text="WHEN THE AI GENERATES MEMES",
            bottom_text="AND IT ACTUALLY WORKS",
            panel_texts=[],
            style=style_hint,
            topic=topic,
            humor_type="relatable",
            tags=["ai","meme","generated"],
        )


def generate_batch_captions(
    topic: str,
    api_key: str,
    count: int = 5,
) -> list[MemeCaption]:
    """Generate multiple caption variations for one topic."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.95, "max_output_tokens": 1200},
    )

    prompt = f"""Generate {count} different funny meme captions about: {topic}

Make each one a different style: sarcastic, relatable, absurd, wholesome, technical joke.
Keep all text SHORT (max 8 words each).

Return ONLY valid JSON array:
[
  {{
    "top_text": "<CAPS TEXT>",
    "bottom_text": "<CAPS TEXT>",
    "template_suggestion": "<drake|two_buttons|brain_expanding|change_my_mind|success_kid|roll_safe>",
    "humor_type": "<sarcasm|relatable|absurd|wholesome>",
    "tags": ["tag1","tag2"]
  }}
]"""

    try:
        r   = model.generate_content(prompt)
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$","",r.text.strip(),flags=re.MULTILINE)
        items = json.loads(raw.strip())
        return [
            MemeCaption(
                template=item.get("template_suggestion","custom"),
                top_text=item.get("top_text","").upper(),
                bottom_text=item.get("bottom_text","").upper(),
                panel_texts=[],
                style="classic",
                topic=topic,
                humor_type=item.get("humor_type","relatable"),
                tags=item.get("tags",[]),
            )
            for item in items[:count]
        ]
    except Exception:
        return [generate_meme_caption(topic, "custom", "classic", api_key)]


# ── Meme renderer ─────────────────────────────────────────────────────────────
def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to get Impact font (classic meme font), fall back gracefully."""
    font_paths = [
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Impact.ttf",
        "C:/Windows/Fonts/impact.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _draw_text_with_outline(
    draw: ImageDraw.Draw,
    pos: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    stroke_fill: tuple,
    stroke_width: int = 3,
    align: str = "center",
    max_width: int = 500,
):
    """Draw text with stroke/outline, auto-wrap long text."""
    # Wrap text
    avg_char = font.size * 0.6
    chars_per_line = max(10, int(max_width / avg_char))
    wrapped = textwrap.fill(text, width=chars_per_line)

    # Draw stroke
    for dx in range(-stroke_width, stroke_width+1):
        for dy in range(-stroke_width, stroke_width+1):
            if dx != 0 or dy != 0:
                draw.text((pos[0]+dx, pos[1]+dy), wrapped, font=font,
                          fill=stroke_fill, align=align)
    # Draw main text
    draw.text(pos, wrapped, font=font, fill=fill, align=align)


def render_meme(caption: MemeCaption, width: int = 600, height: int = 500) -> bytes:
    """Render a meme image as PNG bytes."""
    style = MEME_STYLES.get(caption.style, MEME_STYLES["classic"])
    template_info = MEME_TEMPLATES.get(caption.template, MEME_TEMPLATES["custom"])
    fmt = template_info["format"]

    font_size = style["font_size"]
    font_large = _get_font(font_size)
    font_small = _get_font(max(20, font_size - 8))

    if fmt in ("four_panel", "two_panel_vertical"):
        img = _render_multi_panel(caption, width, height, style, font_large, font_small)
    elif fmt == "two_panel_dialog":
        img = _render_dialog(caption, width, height//2, style, font_large)
    else:
        img = _render_standard(caption, width, height, style, font_large, fmt)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _render_standard(caption, width, height, style, font, fmt) -> Image.Image:
    """Render a standard top/bottom caption meme."""
    img  = Image.new("RGB", (width, height), color=style["bg"])
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(style["bg"][0] * (1 - ratio*0.3))
        g = int(style["bg"][1] * (1 - ratio*0.3))
        b = int(style["bg"][2] * (1 - ratio*0.3))
        draw.line([(0,y),(width,y)], fill=(r,g,b))

    # Draw decorative elements
    draw.rectangle([10,10,width-10,height-10], outline=style["text"], width=3)

    margin = 30
    text_color  = style["text"]
    stroke_color = style["stroke"] if style["stroke"] != style["bg"] else (
        (0,0,0) if text_color != (0,0,0) else (255,255,255)
    )

    if caption.top_text and fmt != "caption_bottom":
        _draw_text_with_outline(
            draw, (width//2, margin+10), caption.top_text,
            font, text_color, stroke_color, max_width=width-40,
        )

    if caption.bottom_text and fmt != "caption_top":
        _draw_text_with_outline(
            draw, (width//2, height-margin-40), caption.bottom_text,
            font, text_color, stroke_color, max_width=width-40,
        )

    # Center decorative emoji/symbol
    mid_text = MEME_TEMPLATES.get(caption.template, {}).get("emoji","🎭")
    mid_font = _get_font(80)
    draw.text((width//2, height//2), mid_text, font=mid_font,
              fill=(*text_color, 120), anchor="mm")

    # Watermark
    wm_font = _get_font(14)
    draw.text((width-10, height-20), "AI Meme Generator",
              font=wm_font, fill=(*text_color, 80), anchor="rs")

    return img


def _render_multi_panel(caption, width, height, style, font_large, font_small) -> Image.Image:
    """Render a multi-panel meme (Drake, Brain Expanding, Gru's Plan)."""
    texts = caption.panel_texts or [caption.top_text, caption.bottom_text]
    n     = max(len(texts), 2)
    panel_h = height // n
    img   = Image.new("RGB", (width, panel_h * n), color=style["bg"])
    draw  = ImageDraw.Draw(img)

    colors_cycle = [
        style["bg"],
        tuple(min(255, c+30) for c in style["bg"]),
        tuple(max(0, c-20) for c in style["bg"]),
        tuple(min(255, c+50) for c in style["bg"]),
    ]
    text_color = style["text"]
    stroke_c   = (0,0,0) if text_color != (0,0,0) else (255,255,255)

    for i, text in enumerate(texts[:n]):
        y_off  = i * panel_h
        bg_col = colors_cycle[i % len(colors_cycle)]
        draw.rectangle([0, y_off, width, y_off+panel_h], fill=bg_col)
        draw.line([0, y_off, width, y_off], fill=text_color, width=2)

        # Panel number indicator
        num_font = _get_font(20)
        draw.text((20, y_off+10), f"#{i+1}", font=num_font, fill=text_color)

        _draw_text_with_outline(
            draw,
            (width//2, y_off + panel_h//2),
            text or f"Panel {i+1}",
            font_small, text_color, stroke_c,
            max_width=width-60,
        )

    # Border
    draw.rectangle([0,0,width-1,panel_h*n-1], outline=text_color, width=3)

    wm_font = _get_font(12)
    draw.text((width-10, panel_h*n-15), "AI Meme Generator",
              font=wm_font, fill=(*text_color, 60), anchor="rs")
    return img


def _render_dialog(caption, width, height, style, font) -> Image.Image:
    """Render a two-panel dialog meme (Always Has Been style)."""
    texts  = caption.panel_texts or [caption.top_text, caption.bottom_text]
    img    = Image.new("RGB", (width, height*2), color=style["bg"])
    draw   = ImageDraw.Draw(img)
    tc     = style["text"]
    sc     = (0,0,0) if tc != (0,0,0) else (255,255,255)

    for i, (text, y_base) in enumerate(zip(texts[:2], [0, height])):
        col = style["bg"] if i == 0 else tuple(min(255,c+25) for c in style["bg"])
        draw.rectangle([0,y_base,width,y_base+height], fill=col)
        draw.rectangle([5,y_base+5,width-5,y_base+height-5], outline=tc, width=2)

        label = "🌍 Astronaut 1:" if i==0 else "🔫 Astronaut 2:"
        lf    = _get_font(16)
        draw.text((15, y_base+12), label, font=lf, fill=tc)
        _draw_text_with_outline(
            draw, (width//2, y_base+height//2+10),
            text or f"Dialog {i+1}", font, tc, sc, max_width=width-40,
        )

    wm_font = _get_font(12)
    draw.text((width-10, height*2-15), "AI Meme Generator",
              font=wm_font, fill=(*tc,60), anchor="rs")
    return img
