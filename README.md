# 🎭 AI Meme Generator

<div align="center">

![Banner](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,18,24&height=200&section=header&text=AI%20Meme%20Generator&fontSize=52&fontColor=fff&animation=twinkling&fontAlignY=35&desc=Trending%20Topics%20%E2%80%A2%20AI%20Captions%20%E2%80%A2%2020%2B%20Templates%20%E2%80%A2%20Batch%20Mode%20%E2%80%A2%20Free%20Gemini%20API&descAlignY=55&descSize=14)

<p>
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini%201.5%20Flash-Free%20API-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pillow-Image%20Rendering-yellow?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/20%2B%20Templates-Included-a855f7?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge"/>
</p>

<p>
  <b>Enter any topic → Gemini AI writes the perfect meme caption → Pillow renders it with classic meme formatting → Download instantly. Includes trending topic fetcher, batch mode, and 20+ templates.</b>
</p>

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Caption Generation** | Gemini writes punchy, funny captions in multiple humor styles |
| 🔥 **Trending Topics** | Fetches live trending topics from HN, Reddit, TechCrunch, The Verge |
| 🖼️ **20+ Meme Templates** | Drake, Distracted BF, Two Buttons, Brain Expanding, Gru's Plan, and more |
| 🎨 **5 Color Styles** | Classic, White Top, Dank, Reddit, Galaxy |
| 🎯 **Batch Mode** | Generate 2-6 meme variations on the same topic at once |
| ✏️ **Custom Text Mode** | Type your own captions — AI just renders them |
| 🖼️ **Meme Gallery** | Session gallery with all generated memes |
| ⬇️ **PNG Download** | Download any meme instantly |
| 📐 **Custom Size** | Adjust width and height |
| 🎲 **Random Template** | Surprise yourself with a random template |

---

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/ai-meme-generator.git
cd ai-meme-generator
pip install -r requirements.txt
streamlit run app.py
```

---

## 🎭 Meme Templates

| Template | Format | Emoji |
|---|---|---|
| Drake Approves/Rejects | Two-panel vertical | 🦉 |
| Distracted Boyfriend | Three-label | 👀 |
| Two Buttons | Two-choice panic | 😰 |
| Expanding Brain | Four-panel | 🧠 |
| One Does Not Simply | Caption bottom | 🧙 |
| Change My Mind | Caption top | ☕ |
| This Is Fine | Caption top | 🔥 |
| Surprised Pikachu | Caption top | ⚡ |
| Always Has Been | Two-panel dialog | 🌍 |
| Gru's Plan | Four-panel | 😏 |
| Success Kid | Caption both | ✊ |
| Bad Luck Brian | Caption both | 😬 |
| Roll Safe | Caption both | 😏 |
| They're The Same Picture | Caption top | 🤷 |
| First World Problems | Caption both | 😭 |
| Custom | Any format | ✨ |

---

## 🧠 How It Works

```
User inputs topic
      │
      ▼
Gemini 1.5 Flash (temp=0.9 for creativity)
Generates: top_text + bottom_text + panel_texts
           + humor_type + tags
      │
      ▼
Pillow renders meme image:
  - Gradient background
  - Impact font with black stroke outline
  - Multi-panel layouts for Drake/Brain/Gru
  - Template emoji as center decoration
  - Watermark
      │
      ▼
PNG bytes → display + download
```

---

## 📁 Project Structure

```
ai-meme-generator/
├── app.py                  # 🖥️ Streamlit UI — 4 tabs
├── src/
│   └── meme_engine.py      # 🧠 Caption generation + Pillow rendering
├── requirements.txt        # 📦 5 dependencies
├── README.md
└── LICENSE
```

---

## 🗺️ Roadmap

- [ ] Image-based templates (actual meme images as backgrounds)
- [ ] GIF meme support
- [ ] Share directly to Twitter/Reddit
- [ ] Meme rating / upvote system
- [ ] More languages
- [ ] Voice-to-meme (speak the topic)

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**⭐ Star this repo if it made you laugh!**

*The internet runs on memes. Now AI makes them.*

![Footer](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,18,24&height=100&section=footer)

</div>
