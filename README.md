# AI-Agents-for-Medical-Diagnostics

<img width="900" alt="image" src="https://github.com/user-attachments/assets/b7c87bf6-dfff-42fe-b8d1-9be9e6c7ce86">

A Python project that creates specialized **LLM-based AI agents** to analyze complex medical cases.
The system integrates insights from different medical specialists to provide comprehensive assessments
and suggested treatment directions, demonstrating the potential of AI in multidisciplinary medicine.

> ⚠️ **Disclaimer**: This project is for research and educational purposes only.
> It is **not intended for clinical diagnosis or medical advice**.

---

## What's New

- Migrated from OpenAI (GPT) to **Google Gemini API** (`GEMINI_API_KEY`)
- Added **FastAPI web UI** — paste a report and view results in the browser
- Added reusable **pipeline module** (`pipeline.py`) with `ThreadPoolExecutor` concurrency
- Added **free Render deployment** config (`render.yaml`)
- Cross-platform path handling via `pathlib`

---

## How It Works

Three specialist AI agents analyze the medical report **in parallel**:

| Agent | Focus |
|---|---|
| Cardiologist | Cardiac issues (arrhythmias, structural abnormalities) |
| Psychologist | Mental health (anxiety, depression, panic disorder) |
| Pulmonologist | Respiratory issues (asthma, COPD, breathing disorders) |

Their outputs are then passed to a **Multidisciplinary Team agent** which summarises the three most likely health issues.

---

## Repository Structure

```
.
├── app.py              ← FastAPI web server (GET / UI + POST /diagnose API)
├── pipeline.py         ← Reusable diagnosis pipeline (ThreadPoolExecutor)
├── Main.py             ← CLI entry point (calls pipeline.py)
├── Utils/
│   └── Agents.py       ← Gemini-powered agent classes
├── Medical Reports/    ← Sample medical report text files
├── Results/            ← Agent output files (gitignored)
├── render.yaml         ← Free Render deployment config
└── requirements.txt
```

---

## Local Run (Web UI)

**Step 1 – Clone the repository**
```bash
git clone https://github.com/2025bcacsbharshit22313-hub/nagar.git
cd nagar
```

**Step 2 – Create and activate a virtual environment**

macOS / Linux:
```bash
python -m venv venv
source venv/bin/activate
```

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

**Step 3 – Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 – Set your Gemini API key**

Create `apikey.env` in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
```
Get a free key at https://aistudio.google.com/app/apikey

Or export it directly:

macOS / Linux:
```bash
export GEMINI_API_KEY=your_gemini_api_key_here
```

Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY = "your_gemini_api_key_here"
```

**Step 5 – Start the web server**
```bash
uvicorn app:app --reload
```

Open http://127.0.0.1:8000 in your browser, paste a medical report and click **Run Diagnosis**.

---

## CLI Usage

```bash
python Main.py
```

Reads `Medical Reports/Medical Rerort - Michael Johnson - Panic Attack Disorder.txt` and writes the result to `Results/final_diagnosis.txt`.

---

## Deploy for Free on Render

1. Go to [render.com](https://render.com) and sign in.
2. Click **New → Web Service**.
3. Connect your GitHub repository (`2025bcacsbharshit22313-hub/nagar`).
4. Render will detect `render.yaml` automatically.  
   If not, set manually:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. In the **Environment** section, add:
   - **Key**: `GEMINI_API_KEY`  **Value**: *(your actual key)*
6. Click **Create Web Service**.
7. After the build finishes, Render provides a public URL:
   `https://<service-name>.onrender.com`

> **Note**: The free Render tier spins down after inactivity and may be slow on first request.

---

## API Reference

### `POST /diagnose`

**Request body** (JSON):
```json
{ "medical_report": "Patient is a 35-year-old male..." }
```

**Response** (JSON):
```json
{
  "cardiologist": "...",
  "psychologist": "...",
  "pulmonologist": "...",
  "final_diagnosis": "..."
}
```

### `GET /`

Returns the HTML web UI.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `KeyError: GEMINI_API_KEY` | Set `GEMINI_API_KEY` env var or create `apikey.env` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port already in use | Change port: `uvicorn app:app --port 8001` |
| Slow response | Gemini API calls take ~10-30 s; wait for the spinner |
| Render deploy fails | Check the Render logs tab for the exact error |

---

## Future Enhancements

- Specialist Expansion: Neurology, Endocrinology, Immunology agents
- Local LLM Support: Llama via Ollama / vLLM
- Vision Capabilities: Radiology image analysis
- Automated Testing: CI with mocked LLM calls

---

## License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
