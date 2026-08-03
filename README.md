# 🎬 YouTube Long-Form "How-To" Video Bot

An automated Python-based pipeline designed to generate long-form "How-To" YouTube video content, complete with AI script generation, voiceover text mapping, storyboard generation, and YouTube upload readiness.

---

## 🚀 Features
- **AI-Powered Scriptwriting:** Automatically generates engaging hooks, step-by-step instructions, troubleshooting tips, and CTAs using LLM APIs.
- **Storyboard & B-Roll Planner:** Maps out visual cues and scene descriptions for each step.
- **Voiceover Integration:** Structured text output ready for TTS (Text-to-Speech) engines like ElevenLabs or Edge-TTS.
- **Automated Metadata Generator:** Generates SEO-optimized Titles, Descriptions, Tags, and Chapter Timestamps.

---

## 📁 Project Structure
```text
youtube-howto-bot/
├── config.json          # Configuration settings & API keys placeholders
├── main.py              # Main pipeline runner script
├── requirements.txt     # Python dependencies
├── generator.py         # Core logic for script & metadata generation
└── README.md            # Documentation
```

---

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/youtube-howto-bot.git
   cd youtube-howto-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API keys:**
   Copy `config.json.example` to `config.json` and add your API keys.

4. **Run the bot:**
   ```bash
   python main.py
   ```
