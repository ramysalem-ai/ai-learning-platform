# Build with AI

**A weekly series of hands-on workshops for building real, production-style AI agents - each one teaches by having you build it yourself, file by file, verified at every step.**

Built for genuine beginners: plain-English explanations, one real file built from scratch, a step-by-step setup walkthrough with every command as its own copy-pasteable block, and a "check yourself" full-file view at every checkpoint so you always know if your code matches.

New workshop dropping weekly — this repo grows over time. ⭐ Star it to get notified.

## 🚀 Run it in 2 minutes

```bash
git clone https://github.com/ramysalem-ai/ai-learning-platform.git
cd ai-learning-platform
pip install -r requirements.txt
```

Windows PowerShell — if `pip` is blocked, use `python -m pip` instead:

```powershell
$env:OPENAI_API_KEY="sk-..."
python -m streamlit run Home.py
```

Mac/Linux:

```bash
export OPENAI_API_KEY="sk-..."
streamlit run Home.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`). Once you're in the app, Part 1's "First time doing this?" box walks through every setup step in full detail, including exactly which terminal window to use and where.

Get an OpenAI API key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). The live demo asks for your own key directly in the browser, nothing is billed to anyone but you, and nothing is stored.

## 📂 This week's workshop

### 🎧 Agentic Essentials — Build Production GPT Applications
A single AI agent, built from an empty file to a fully working customer support bot. Five parts, 30 progressive checkpoints, covering the agentic loop, coordinator/subagent patterns, tool design, structured output, and context management.
📁 [`exercises/`](exercises/) · **Beginner**

## 🗂️ Repo structure

```
Home.py                  # Catalog page — entry point
styles.py                # Shared design system (color palette, theme)
pages/                   # Streamlit guide pages
exercises/                # 19 standalone exercise scripts
reference/                # Verified complete reference implementation
```

Your own `agent.py`, the file you build as you work through the guide, is **not** included here. You create it yourself, in your own separate project folder, starting at Part 1's first step. This repo is the guide and the app that runs it, not your exercise work.

## 🔒 A note on API keys

The live demo (the actual running agent, not the guide text) asks you to paste your own OpenAI API key directly into the interface. That key is held only for your browser session, never written to disk, never logged, and there is no fallback to any other credential. If you don't enter a key, the demo simply won't run rather than silently using someone else's.

## 🛠️ Requirements

- Python 3.10+
- An OpenAI API key

## 📜 License

MIT, see [LICENSE](LICENSE). Clone it, learn from it, build on it.

---

Built by [Ramy Salem](https://github.com/ramysalem-ai) — AI Success Architect, Deployment & Adoption.
