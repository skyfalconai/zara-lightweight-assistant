# ZARA – Modular AI Assistant

**ZARA** is a local, modular AI assistant that supports both CLI and GUI modes. It is built for extensibility through agent modules and can be run from anywhere using the PATH-configured `bin/` directory.

---

## 🔧 Project Structure

```

ZARA/
├── agents        # Custom agent modules (each defines a self\_description and a main() function)
├── bin          # Add this directory to your system PATH to run ZARA globally
├── ui             # UI interfaces (Gradio GUI and CLI)
├── zara           # Core logic and infra (model handling, database, etc.)
├── models         # LLM wrapper and chat history
├── requirements.txt
└── README.md

````

---

## 🧠 Agent System

Each agent should follow this format:

```python
# agents.py

self_description = "This agent handles XYZ functionality"

def main(self,keywords, user_input):
    # Implement logic here
    return result
````

Agents are automatically loaded and called based on intent or keyword matching.

Current Built-in Agents:

* ✅ `x`: Twitter integration (requires Twitter API keys)
* ✅ `weather`: Get real-time weather updates
* ✅ `news`: Fetch latest headlines
* ✅ `generate_image`: Image generation from text
* ✅ `youtube`: Search/play YouTube videos
* ✅ `google`: Google search and web summarization
* ✅ `PdfReader `: Read pdf through path

To use these, **users must obtain their own API keys** and set them in the `.env` file (see below).

---

## 🔑 Environment Setup

```env
MODEL_NAME=ZARA

SARWAM_API_KEY=
SARWAM_API_URL=

WEATHER_API_KEY=
NEWS_API_KEY=

GOOGLE_SEARCH_API_KEY=
GOOGLE_CSX_ID=

YOUTUBE_API_KEY=

HF_TOKEN=

X_API_KEY=
X_API_SECRET=
X_BEARER_TOKEN=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=

MONGO_DB_URL=
```

---

## 🧪 Running ZARA

### 1. Using CLI or GUI

Run the main interface selection script:

```bash
python ui.py
```

Choose between:

* CLI Mode
* Gradio GUI Mode

---

## 📦 Global Access (Optional)

To run ZARA from anywhere:

1. Add the `bin/` directory to your system’s `PATH`.
2. Example `.bat` or `.sh` file inside `bin/` might look like:

```bat
@echo off
REM Update the path to point to your UI file
python D:\path\to\ZARA\ui\ui.py %*
```

---

## 🤖 Libraries Used

* `pyttsx3`: Text-to-speech
* `requests`: HTTP requests
* `os`, `json`, `time`, `re`, etc.: System and utility functions
* `gradio`: GUI interface
* `trafilatura`: Web article extraction
* `dotenv`: Environment variable loading
* `beautifulsoup4`: HTML parsing
* `pypdf`: PDF reading
* `tweepy`: Twitter API integration
* `huggingface_hub`: Inference API client
* `tqdm`: Progress bar
* `IPython.display`: Display control
* Custom modules: `errHandler`, `infra`, `models`, `agents`

---

## 🛠 Requirements

See `requirements.txt` for dependencies.

---

## 🧩 Modular & Extensible

Feel free to add your own agents to the `agents` file. All independent researchers and developers are welcome to fork and contribute.

