"""
app.py – FastAPI web application exposing the medical-diagnosis pipeline.

Routes:
  GET  /          → minimal HTML UI (paste a report, view results)
  POST /diagnose  → JSON { "medical_report": "..." } → JSON diagnosis result
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import pipeline

pipeline.load_environment()  # load apikey.env if present (no-op in production)

app = FastAPI(title="AI Medical Diagnostics", version="1.0.0")

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class DiagnoseRequest(BaseModel):
    medical_report: str


class DiagnoseResponse(BaseModel):
    cardiologist: str
    psychologist: str
    pulmonologist: str
    final_diagnosis: str


# ---------------------------------------------------------------------------
# HTML UI (served at GET /)
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Medical Diagnostics</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #f0f4f8;
      margin: 0;
      padding: 24px 16px;
      color: #1a202c;
    }
    .container { max-width: 860px; margin: 0 auto; }
    h1 { font-size: 1.8rem; margin-bottom: 4px; }
    .subtitle { color: #718096; margin-bottom: 24px; font-size: 0.95rem; }
    .disclaimer {
      background: #fff3cd;
      border-left: 4px solid #f6ad55;
      padding: 10px 16px;
      border-radius: 4px;
      margin-bottom: 24px;
      font-size: 0.875rem;
    }
    label { font-weight: 600; display: block; margin-bottom: 6px; }
    textarea {
      width: 100%;
      min-height: 220px;
      padding: 12px;
      border: 1px solid #cbd5e0;
      border-radius: 6px;
      font-size: 0.9rem;
      resize: vertical;
    }
    button {
      margin-top: 12px;
      padding: 10px 28px;
      background: #3182ce;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 1rem;
      cursor: pointer;
    }
    button:disabled { background: #90cdf4; cursor: not-allowed; }
    .results { margin-top: 32px; }
    .card {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 16px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .card h2 { margin: 0 0 10px; font-size: 1.05rem; color: #2b6cb0; }
    .card pre {
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 0.875rem;
      margin: 0;
    }
    #error { color: #c53030; margin-top: 12px; }
    #spinner { display: none; margin-top: 12px; color: #718096; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🩺 AI Medical Diagnostics</h1>
    <p class="subtitle">Powered by Google Gemini — three specialist agents + multidisciplinary team</p>

    <div class="disclaimer">
      ⚠️ <strong>Educational use only.</strong> This tool is not intended for clinical diagnosis or medical advice.
    </div>

    <label for="report">Paste the medical report here:</label>
    <textarea id="report" placeholder="Enter the patient's medical report text..."></textarea>
    <br/>
    <button id="btn" onclick="runDiagnosis()">Run Diagnosis</button>
    <p id="spinner">⏳ Running agents, please wait (this may take ~30 seconds)…</p>
    <p id="error"></p>

    <div id="results" class="results" style="display:none">
      <div class="card">
        <h2>🫀 Cardiologist</h2>
        <pre id="cardio"></pre>
      </div>
      <div class="card">
        <h2>🧠 Psychologist</h2>
        <pre id="psycho"></pre>
      </div>
      <div class="card">
        <h2>🫁 Pulmonologist</h2>
        <pre id="pulmo"></pre>
      </div>
      <div class="card">
        <h2>🏥 Final Diagnosis (Multidisciplinary Team)</h2>
        <pre id="final"></pre>
      </div>
    </div>
  </div>

  <script>
    async function runDiagnosis() {
      const report = document.getElementById('report').value.trim();
      const btn = document.getElementById('btn');
      const spinner = document.getElementById('spinner');
      const errorEl = document.getElementById('error');
      const resultsEl = document.getElementById('results');

      errorEl.textContent = '';
      resultsEl.style.display = 'none';

      if (!report) {
        errorEl.textContent = 'Please paste a medical report before running.';
        return;
      }

      btn.disabled = true;
      spinner.style.display = 'block';

      try {
        const res = await fetch('/diagnose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ medical_report: report })
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || 'Server error');
        }

        const data = await res.json();
        document.getElementById('cardio').textContent = data.cardiologist;
        document.getElementById('psycho').textContent = data.psychologist;
        document.getElementById('pulmo').textContent = data.pulmonologist;
        document.getElementById('final').textContent = data.final_diagnosis;
        resultsEl.style.display = 'block';
      } catch (err) {
        errorEl.textContent = '❌ Error: ' + err.message;
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the minimal HTML diagnosis UI."""
    return _HTML


# ---------------------------------------------------------------------------
# POST /diagnose
# ---------------------------------------------------------------------------

@app.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(request: DiagnoseRequest):
    """
    Run the AI specialist pipeline on the submitted medical report.

    Accepts: JSON { "medical_report": "..." }
    Returns: JSON with cardiologist, psychologist, pulmonologist, final_diagnosis
    """
    report = request.medical_report.strip()
    if not report:
        raise HTTPException(status_code=400, detail="medical_report must not be empty.")

    try:
        result = pipeline.run_full_diagnosis(report)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Diagnosis pipeline failed: {exc}",
        ) from exc

    return DiagnoseResponse(**result)


# ---------------------------------------------------------------------------
# Entry point for local development
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
