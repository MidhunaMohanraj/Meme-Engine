"""
app.py — AI Meme Generator Dashboard
"""
import sys, io, json, random
import streamlit as st
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent / "src"))
from meme_engine import (
    MEME_TEMPLATES, MEME_STYLES, MEME_CATEGORIES,
    fetch_trending, generate_meme_caption, generate_batch_captions,
    render_meme, MemeCaption, TrendingTopic,
)
st.set_page_config(
    page_title="AI Meme Generator", 
    page_icon="🎭",
    layout="wide", 
    initial_sidebar_state="expanded",
) 
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Bangers&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .main { background: #07080d; }

  .hero {
    background: linear-gradient(135deg,#1a0530 0%,#07080d 40%,#1a1005 100%);
    border:1px solid #2a1a40; border-radius:16px;
    padding:30px 40px; text-align:center; margin-bottom:20px;
  }
  .hero h1 { font-size:42px; font-weight:700; color:#fff; margin:0 0 6px;
             font-family:'Bangers',cursive; letter-spacing:2px; }
  .hero p  { color:#64748b; font-size:14px; margin:0; }

  .meme-card {  
    background:#0b0d18; border:1px solid #1e2040;
    border-radius:12px; padding:16px; margin:8px 0; text-align:center;
  }
  .topic-chip {
    display:inline-block; background:#0f0520; border:1px solid #4c1d95;
    color:#c4b5fd; padding:5px 14px; border-radius:20px;
    font-size:12px; margin:3px; cursor:pointer;
  }
  .trending-row {
    background:#080a14; border:1px solid #1e2040; border-radius:8px;
    padding:10px 14px; margin:4px 0; font-size:13px;
    display:flex; justify-content:space-between; align-items:center;
    cursor:pointer;
  }
  .tag-chip {
    display:inline-block; background:#051510; border:1px solid #064e3b;
    color:#6ee7b7; padding:2px 8px; border-radius:12px; font-size:11px; margin:2px;
  }
  .stat-card {
    background:#0b0d18; border:1px solid #1e2040;
    border-radius:10px; padding:14px; text-align:center;
  }
  .stat-val   { font-size:24px; font-weight:700; }
  .stat-label { font-size:10px; color:#475569; text-transform:uppercase; letter-spacing:1.5px; margin-top:3px; }

  div.stButton > button {
    background:linear-gradient(135deg,#4c1d95,#a855f7);
    color:white; font-weight:700; border:none; border-radius:10px;
    padding:12px 28px; font-size:15px; width:100%;
  }
  div.stButton > button:hover { opacity:0.85; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎭 Meme Generator")
    st.markdown("---")
    st.markdown("### 🔑 Gemini API Key")
    api_key = st.text_input("Free Gemini API Key", type="password", placeholder="AIza...")
    if not api_key:
        st.info("🆓 Free at [aistudio.google.com](https://aistudio.google.com)")

    st.markdown("---")
    st.markdown("### 🖼️ Template")
    template = st.selectbox(
        "Meme Template",
        list(MEME_TEMPLATES.keys()),
        format_func=lambda x: f"{MEME_TEMPLATES[x]['emoji']} {MEME_TEMPLATES[x]['name']}",
    )

    st.markdown("### 🎨 Style")
    style = st.selectbox("Color Style", list(MEME_STYLES.keys()),
                         format_func=lambda x: x.replace("_"," ").title())

    st.markdown("### 📐 Size")
    width  = st.slider("Width",  400, 800, 600, step=50)
    height = st.slider("Height", 300, 700, 500, step=50)

    st.markdown("---")
    st.markdown("### 🎲 Random")
    if st.button("🎲 Random Template"):
        st.session_state["random_template"] = random.choice(list(MEME_TEMPLATES.keys()))
    if "random_template" in st.session_state:
        st.success(f"Template: {MEME_TEMPLATES[st.session_state['random_template']]['name']}")

# ── Main UI ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎭 AI Meme Generator</h1>
  <p>Trending topics → AI captions → Instant memes · 20+ templates · Multiple styles</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "✨ Generate Meme", "🔥 Trending Topics", "🎯 Batch Mode", "🖼️ Gallery"
])

# ── Tab 1: Generate ────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### ✨ Generate a Meme")

    col_input, col_preview = st.columns([1, 1])

    with col_input:
        mode = st.radio("Input mode", ["💡 AI Topic", "✏️ Custom Text"], horizontal=True)

        if mode == "💡 AI Topic":
            topic = st.text_input(
                "Topic or situation",
                placeholder="e.g. Fixing a bug at 2am, AI taking over jobs, Monday mornings...",
                value=st.session_state.get("selected_topic", ""),
            )
            style_hint = st.selectbox(
                "Humor style",
                ["relatable", "sarcasm", "absurd", "wholesome", "dark humor", "tech humor"],
            )
            context = st.text_input("Extra context (optional)",
                                    placeholder="e.g. Python developers, startup founders...")
            generate_btn = st.button("🎭 Generate Meme!")

        else:  # Custom text
            top_text    = st.text_input("Top text (CAPS auto-applied)",
                                        placeholder="WHEN YOU FINALLY FIX THE BUG")
            bottom_text = st.text_input("Bottom text",
                                        placeholder="IT WAS A MISSING SEMICOLON")
            panel_texts = []
            template_fmt = MEME_TEMPLATES.get(template, {}).get("format","caption_both")
            if "panel" in template_fmt or "four" in template_fmt:
                n_panels = 4 if "four" in template_fmt else 2
                st.caption(f"This template uses {n_panels} panels:")
                for i in range(n_panels):
                    pt = st.text_input(f"Panel {i+1} text", key=f"panel_{i}",
                                       placeholder=f"Panel {i+1}...")
                    panel_texts.append(pt.upper() if pt else "")
            generate_btn = st.button("🎭 Render Meme!")
            topic = top_text or "Custom meme"

        # Category quick-select
        st.markdown("**💡 Quick topics:**")
        quick_cols = st.columns(4)
        quick_topics = [
            "Debugging at 3am", "AI replacing jobs", "Monday meetings",
            "Coffee vs decaf", "Stack Overflow", "Git merge conflicts",
            "Infinite loading spinner", "My code in production",
        ]
        for i, qt in enumerate(quick_topics):
            with quick_cols[i % 4]:
                if st.button(f"💬 {qt[:18]}", key=f"qt_{i}"):
                    st.session_state["selected_topic"] = qt
                    st.rerun()

    with col_preview:
        st.markdown("### 🖼️ Preview")
        preview_placeholder = st.empty()
        info_placeholder    = st.empty()

    if generate_btn:
        if not api_key and mode == "💡 AI Topic":
            st.error("⚠️ Add your free Gemini API key to generate AI captions.")
        elif not topic.strip() and mode == "💡 AI Topic":
            st.warning("⚠️ Enter a topic first.")
        else:
            with st.spinner("🤖 Generating meme..."):
                if mode == "💡 AI Topic":
                    caption = generate_meme_caption(
                        topic, template, style_hint, api_key, context
                    )
                else:
                    caption = MemeCaption(
                        template=template,
                        top_text=top_text.upper() if top_text else "",
                        bottom_text=bottom_text.upper() if bottom_text else "",
                        panel_texts=panel_texts,
                        style=style,
                        topic=topic,
                        humor_type="custom",
                        tags=[],
                    )
                caption.style = style
                img_bytes = render_meme(caption, width, height)

            with col_preview:
                preview_placeholder.image(img_bytes, caption=f"🎭 {topic}", use_container_width=True)
                info_placeholder.markdown(f"""
<div class="meme-card">
  <div style="font-size:12px;color:#64748b;margin-bottom:8px;">Generated at {datetime.now().strftime('%H:%M:%S')}</div>
  <div style="font-size:13px;color:#e2e8f0;margin-bottom:6px;"><b>Top:</b> {caption.top_text or '—'}</div>
  <div style="font-size:13px;color:#e2e8f0;margin-bottom:8px;"><b>Bottom:</b> {caption.bottom_text or '—'}</div>
  <div>{''.join(f'<span class="tag-chip">#{t}</span>' for t in caption.tags)}</div>
</div>
""", unsafe_allow_html=True)

            # Download
            st.download_button(
                "⬇️ Download Meme (.png)",
                data=img_bytes,
                file_name=f"meme_{topic[:20].replace(' ','_')}.png",
                mime="image/png",
            )

            # Save to gallery
            if "gallery" not in st.session_state:
                st.session_state["gallery"] = []
            st.session_state["gallery"].append({
                "img": img_bytes, "topic": topic,
                "template": template, "caption": caption,
                "created": datetime.now().strftime("%H:%M"),
            })

# ── Tab 2: Trending ────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🔥 Trending Topics")
    if st.button("📡 Fetch Live Trending Topics"):
        with st.spinner("Fetching trends..."):
            trends = fetch_trending(20)
            st.session_state["trends"] = trends

    trends = st.session_state.get("trends", [])
    if trends:
        # Group by category
        by_cat: dict = {}
        for t in trends:
            by_cat.setdefault(t.category, []).append(t)

        for cat, items in by_cat.items():
            st.markdown(f"**{cat}**")
            for item in items[:4]:
                col_t, col_btn = st.columns([5,1])
                with col_t:
                    st.markdown(f'<div class="trending-row"><span>🔥 {item.title[:70]}</span><span style="color:#475569;font-size:11px;">{item.source}</span></div>', unsafe_allow_html=True)
                with col_btn:
                    if st.button("🎭", key=f"trend_{item.title[:15]}"):
                        st.session_state["selected_topic"] = item.title
                        st.success(f"Topic selected! Go to Generate tab.")
    else:
        st.info("Click 'Fetch Live Trending Topics' to load current trends from tech & news feeds.")

        # Static fallback topics
        st.markdown("**Or try these popular meme topics:**")
        cats = {
            "💻 Tech": ["AI is going to replace us", "Works on my machine", "Stack Overflow is down"],
            "☕ Work Life": ["Another meeting that could've been an email", "5pm on Friday", "Imposter syndrome"],
            "🧠 Developer Life": ["CSS is broken again", "Just one more feature", "Technical debt"],
            "😂 Pop Culture": ["NFTs in 2024", "Crypto moon", "The metaverse"],
        }
        for cat_name, topics in cats.items():
            st.markdown(f"*{cat_name}*")
            cols = st.columns(3)
            for i, tp in enumerate(topics):
                with cols[i % 3]:
                    if st.button(f"💬 {tp[:25]}", key=f"static_{tp[:10]}"):
                        st.session_state["selected_topic"] = tp
                        st.success("Topic selected! Go to Generate tab →")

# ── Tab 3: Batch Mode ──────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 🎯 Batch Meme Generator")
    st.caption("Generate multiple meme variations on the same topic at once")

    batch_topic = st.text_input("Topic for batch generation",
                                 placeholder="e.g. Imposter syndrome in tech...")
    batch_count = st.slider("Number of variations", 2, 6, 4)
    batch_btn   = st.button("🎭 Generate Batch!")

    if batch_btn:
        if not api_key:
            st.error("⚠️ Add your Gemini API key.")
        elif not batch_topic.strip():
            st.warning("⚠️ Enter a topic.")
        else:
            with st.spinner(f"Generating {batch_count} meme variations..."):
                captions = generate_batch_captions(batch_topic, api_key, batch_count)

            cols = st.columns(2)
            for i, cap in enumerate(captions):
                cap.style = style
                tmpl = cap.template if cap.template in MEME_TEMPLATES else "custom"
                img  = render_meme(cap, width, height)

                with cols[i % 2]:
                    st.image(img, caption=f"Variation {i+1} · {MEME_TEMPLATES[tmpl]['name']}",
                             use_container_width=True)
                    st.markdown(f'<div style="text-align:center;font-size:12px;color:#475569;">😊 {cap.top_text or "—"} / {cap.bottom_text or "—"}</div>', unsafe_allow_html=True)
                    st.download_button(
                        f"⬇️ Download #{i+1}",
                        data=img,
                        file_name=f"meme_{batch_topic[:15].replace(' ','_')}_{i+1}.png",
                        mime="image/png",
                        key=f"batch_dl_{i}",
                    )

                if "gallery" not in st.session_state:
                    st.session_state["gallery"] = []
                st.session_state["gallery"].append({
                    "img": img, "topic": batch_topic,
                    "template": tmpl, "caption": cap,
                    "created": datetime.now().strftime("%H:%M"),
                })

# ── Tab 4: Gallery ─────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### 🖼️ Meme Gallery")
    gallery = st.session_state.get("gallery", [])

    if not gallery:
        st.info("Generate some memes to see them here!")
        st.markdown("""
<div style="text-align:center;padding:40px;color:#334155;">
  <div style="font-size:64px;margin-bottom:12px;">🎭</div>
  <p>Your generated memes will appear here.<br>Start by generating a meme in the first tab!</p>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"**{len(gallery)} memes generated this session**")
        cols = st.columns(3)
        for i, item in enumerate(reversed(gallery)):
            with cols[i % 3]:
                st.image(item["img"], caption=f"🎭 {item['topic'][:30]}", use_container_width=True)
                st.markdown(f'<div style="text-align:center;font-size:11px;color:#475569;">{item["template"]} · {item["created"]}</div>', unsafe_allow_html=True)
                st.download_button(
                    "⬇️",
                    data=item["img"],
                    file_name=f"meme_{i}.png",
                    mime="image/png",
                    key=f"gal_dl_{i}",
                    use_container_width=True,
                )

        if st.button("🗑️ Clear Gallery"):
            st.session_state["gallery"] = []
            st.rerun()

# ── Stats bar ──────────────────────────────────────────────────────────────────
st.markdown("---")
gallery = st.session_state.get("gallery",[])
s1,s2,s3,s4 = st.columns(4)
for col,(val,label,color) in zip([s1,s2,s3,s4],[
    (len(gallery),                    "Memes Generated",  "#a855f7"),
    (len(MEME_TEMPLATES),             "Templates",        "#22c55e"),
    (len(MEME_STYLES),                "Color Styles",     "#f59e0b"),
    (len(set(g["template"] for g in gallery)) if gallery else 0, "Templates Used", "#60a5fa"),
]):
    with col:
        st.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{color};">{val}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
