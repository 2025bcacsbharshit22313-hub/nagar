"""
FastAPI web server for the AI Medical Diagnostics pipeline.

Run locally:
    uvicorn app:app --reload

Render / production:
    uvicorn app:app --host 0.0.0.0 --port $PORT
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Load API key from apikey.env if present (local development only).
# In production (Render, etc.) set GEMINI_API_KEY as an environment variable.
if os.path.exists("apikey.env"):
    load_dotenv(dotenv_path="apikey.env")

from pipeline import run_pipeline  # noqa: E402 – import after env is loaded

app = FastAPI(title="AI Medical Diagnostics")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class DiagnoseRequest(BaseModel):
    medical_report: str


class DiagnoseResponse(BaseModel):
    cardiologist: str
    psychologist: str
    pulmonologist: str
    final_diagnosis: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    """Minimal HTML UI for the diagnostics pipeline."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Medical Diagnostics</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 16px; }
    h1 { color: #2c3e50; }
    textarea { width: 100%; height: 220px; padding: 8px; font-size: 14px; box-sizing: border-box; }
    button { margin-top: 12px; padding: 10px 24px; background: #2980b9; color: #fff;
             border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
    button:disabled { background: #95a5a6; cursor: not-allowed; }
    .section { margin-top: 20px; }
    .section h3 { color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 4px; }
    .section pre { background: #f4f6f7; padding: 12px; border-radius: 4px;
                   white-space: pre-wrap; word-break: break-word; font-size: 13px; }
    #status { margin-top: 10px; color: #7f8c8d; font-style: italic; }
    #error  { margin-top: 10px; color: #c0392b; }
  </style>
</head>
<body>
  <h1>🏥 AI Medical Diagnostics</h1>
  <p>Paste a patient's medical report below and click <strong>Run Diagnosis</strong>.</p>
  <textarea id="report" placeholder="Paste medical report here..."></textarea>
  <br />
  <button id="btn" onclick="diagnose()">Run Diagnosis</button>
  <div id="status"></div>
  <div id="error"></div>

  <div id="results" style="display:none">
    <div class="section"><h3>❤️ Cardiologist</h3><pre id="cardio"></pre></div>
    <div class="section"><h3>🧠 Psychologist</h3><pre id="psych"></pre></div>
    <div class="section"><h3>🫁 Pulmonologist</h3><pre id="pulmo"></pre></div>
    <div class="section"><h3>📋 Final Diagnosis</h3><pre id="final"></pre></div>
  </div>

  <script>
    async function diagnose() {
      const report = document.getElementById('report').value.trim();
      if (!report) { alert('Please paste a medical report first.'); return; }

      const btn    = document.getElementById('btn');
      const status = document.getElementById('status');
      const errDiv = document.getElementById('error');
      const results = document.getElementById('results');

      btn.disabled = true;
      status.textContent = 'Running agents… this may take 20-60 seconds.';
      errDiv.textContent = '';
      results.style.display = 'none';

      try {
        const resp = await fetch('/diagnose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ medical_report: report })
        });

        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(`Server error ${resp.status}: ${text}`);
        }

        const data = await resp.json();
        document.getElementById('cardio').textContent = data.cardiologist   || '(no response)';
        document.getElementById('psych').textContent  = data.psychologist   || '(no response)';
        document.getElementById('pulmo').textContent  = data.pulmonologist  || '(no response)';
        document.getElementById('final').textContent  = data.final_diagnosis || '(no response)';
        results.style.display = 'block';
        status.textContent = 'Done.';
      } catch (e) {
        errDiv.textContent = 'Error: ' + e.message;
        status.textContent = '';
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest):
    """
    Run the full diagnostic pipeline on the provided medical report.

    Returns specialist outputs and the final multidisciplinary diagnosis.
    """
    result = run_pipeline(request.medical_report)
    return DiagnoseResponse(**result)


# ---------------------------------------------------------------------------
# Entry-point (allows `python app.py` as well as uvicorn)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
