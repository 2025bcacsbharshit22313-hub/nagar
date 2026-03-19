"""
FastAPI web server for the AI Medical Diagnostics pipeline.

Supported upload formats: .txt, .pdf

Run locally:
    uvicorn app:app --reload

Render / production:
    uvicorn app:app --host 0.0.0.0 --port $PORT
"""
import io
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Load API key from apikey.env if present (local development only).
# In production (Render, etc.) set GEMINI_API_KEY as an environment variable.
if os.path.exists("apikey.env"):
    load_dotenv(dotenv_path="apikey.env")

from pipeline import run_pipeline  # noqa: E402 – import after env is loaded

app = FastAPI(title="AI Medical Diagnostics")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text_from_upload(filename: str, data: bytes) -> str:
    """Return plain text from an uploaded .txt or .pdf file."""
    # Use only the basename and extract extension to avoid path traversal issues.
    safe_name = os.path.basename(filename or "upload")
    ext = os.path.splitext(safe_name)[1].lower()
    if ext == ".pdf":
        try:
            import pypdf  # lazy import; only needed for PDF uploads

            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
        except Exception as exc:
            raise HTTPException(
                status_code=422, detail=f"Could not read PDF: {exc}"
            ) from exc
    elif ext == ".txt":
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
    else:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Please upload a .txt or .pdf file.",
        )

    if not text.strip():
        raise HTTPException(status_code=422, detail="The uploaded file appears to be empty.")
    return text


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
# HTML UI
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Medical Diagnostics</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f0f4f8;
      color: #2d3748;
      min-height: 100vh;
      padding: 32px 16px;
    }
    .container { max-width: 900px; margin: 0 auto; }

    /* Header */
    header { text-align: center; margin-bottom: 32px; }
    header h1 { font-size: 2rem; color: #1a365d; }
    header p  { margin-top: 6px; color: #4a5568; font-size: 1rem; }

    /* Card */
    .card {
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,.08);
      padding: 28px 32px;
      margin-bottom: 24px;
    }
    .card h2 { font-size: 1.1rem; color: #2b6cb0; margin-bottom: 16px; }

    /* Upload zone */
    #drop-zone {
      border: 2px dashed #90cdf4;
      border-radius: 8px;
      padding: 36px 20px;
      text-align: center;
      cursor: pointer;
      transition: background .2s, border-color .2s;
    }
    #drop-zone.dragover { background: #ebf8ff; border-color: #3182ce; }
    #drop-zone p { color: #718096; font-size: .95rem; }
    #drop-zone .icon { font-size: 2.4rem; margin-bottom: 8px; }
    #file-input { display: none; }
    #file-name  { margin-top: 10px; font-size: .9rem; color: #2b6cb0; font-weight: 600; }

    /* OR divider */
    .divider {
      display: flex; align-items: center; gap: 12px;
      margin: 18px 0; color: #a0aec0; font-size: .85rem;
    }
    .divider::before, .divider::after {
      content: ''; flex: 1; height: 1px; background: #e2e8f0;
    }

    /* Textarea */
    textarea {
      width: 100%; height: 180px; padding: 10px 12px;
      font-size: .9rem; border: 1px solid #cbd5e0;
      border-radius: 8px; resize: vertical; outline: none;
      transition: border-color .2s;
    }
    textarea:focus { border-color: #3182ce; }

    /* Button */
    .btn {
      display: block; width: 100%; margin-top: 18px;
      padding: 13px; font-size: 1rem; font-weight: 600;
      background: #2b6cb0; color: #fff; border: none;
      border-radius: 8px; cursor: pointer; transition: background .2s;
    }
    .btn:hover:not(:disabled) { background: #2c5282; }
    .btn:disabled { background: #a0aec0; cursor: not-allowed; }

    /* Status / error */
    #status { margin-top: 12px; text-align: center; color: #718096; font-style: italic; font-size: .9rem; }
    #error  { margin-top: 12px; text-align: center; color: #c53030; font-size: .9rem; }

    /* Spinner */
    .spinner {
      display: inline-block; width: 18px; height: 18px;
      border: 3px solid #bee3f8; border-top-color: #2b6cb0;
      border-radius: 50%; animation: spin .7s linear infinite;
      vertical-align: middle; margin-right: 6px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Results */
    #results { display: none; }
    .result-card {
      background: #fff; border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,.08);
      padding: 22px 28px; margin-bottom: 20px;
    }
    .result-card h3 {
      font-size: 1rem; margin-bottom: 10px;
      display: flex; align-items: center; gap: 8px;
    }
    .result-card pre {
      background: #f7fafc; border: 1px solid #e2e8f0;
      border-radius: 6px; padding: 14px; font-size: .85rem;
      white-space: pre-wrap; word-break: break-word; line-height: 1.55;
    }
    .badge {
      display: inline-block; font-size: .7rem; font-weight: 700;
      padding: 2px 8px; border-radius: 20px; color: #fff;
    }
    .badge-cardio { background: #e53e3e; }
    .badge-psych  { background: #805ad5; }
    .badge-pulmo  { background: #319795; }
    .badge-final  { background: #2b6cb0; }

    .result-card.final { border-left: 4px solid #2b6cb0; }
  </style>
</head>
<body>
<div class="container">

  <header>
    <h1>🏥 AI Medical Diagnostics</h1>
    <p>Upload a patient report (.txt or .pdf) — or paste the text — to get a full AI diagnosis.</p>
  </header>

  <!-- Input card -->
  <div class="card">
    <h2>📄 Patient Report</h2>

    <!-- Drop zone -->
    <div id="drop-zone" onclick="document.getElementById('file-input').click()">
      <div class="icon">📂</div>
      <p><strong>Click to choose a file</strong> or drag &amp; drop it here</p>
      <p style="font-size:.8rem;margin-top:4px">Supported: .txt, .pdf</p>
      <div id="file-name"></div>
    </div>
    <input type="file" id="file-input" accept=".txt,.pdf" onchange="onFileChosen(event)" />

    <div class="divider">OR paste report text below</div>

    <textarea id="report" placeholder="Paste the full medical report here..."></textarea>

    <button class="btn" id="btn" onclick="submit()">🔬 Run Diagnosis</button>
    <div id="status"></div>
    <div id="error"></div>
  </div>

  <!-- Results -->
  <div id="results">
    <div class="result-card">
      <h3><span class="badge badge-cardio">❤️ Cardiologist</span></h3>
      <pre id="cardio"></pre>
    </div>
    <div class="result-card">
      <h3><span class="badge badge-psych">🧠 Psychologist</span></h3>
      <pre id="psych"></pre>
    </div>
    <div class="result-card">
      <h3><span class="badge badge-pulmo">🫁 Pulmonologist</span></h3>
      <pre id="pulmo"></pre>
    </div>
    <div class="result-card final">
      <h3><span class="badge badge-final">📋 Final Diagnosis</span></h3>
      <pre id="final"></pre>
    </div>
  </div>

</div><!-- /.container -->

<script>
  let chosenFile = null;

  // ── drag & drop ──────────────────────────────────────────────
  const zone = document.getElementById('drop-zone');
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  });

  function onFileChosen(e) {
    const f = e.target.files[0];
    if (f) setFile(f);
  }

  function setFile(f) {
    chosenFile = f;
    document.getElementById('file-name').textContent = '✅ ' + f.name;
    document.getElementById('report').value = '';
  }

  // ── submit ────────────────────────────────────────────────────
  async function submit() {
    const btn    = document.getElementById('btn');
    const status = document.getElementById('status');
    const errDiv = document.getElementById('error');
    const results = document.getElementById('results');

    btn.disabled = true;
    errDiv.textContent = '';
    results.style.display = 'none';
    status.innerHTML = '<span class="spinner"></span>Running agents — this may take 20–60 seconds…';

    try {
      let resp;

      if (chosenFile) {
        // ── file upload path ──
        const fd = new FormData();
        fd.append('file', chosenFile);
        resp = await fetch('/upload', { method: 'POST', body: fd });
      } else {
        // ── paste text path ──
        const text = document.getElementById('report').value.trim();
        if (!text) {
          alert('Please upload a file or paste a medical report.');
          btn.disabled = false;
          status.innerHTML = '';
          return;
        }
        resp = await fetch('/diagnose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ medical_report: text })
        });
      }

      if (!resp.ok) {
        const body = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(body.detail || resp.statusText);
      }

      const data = await resp.json();
      document.getElementById('cardio').textContent = data.cardiologist    || '(no response)';
      document.getElementById('psych').textContent  = data.psychologist    || '(no response)';
      document.getElementById('pulmo').textContent  = data.pulmonologist   || '(no response)';
      document.getElementById('final').textContent  = data.final_diagnosis || '(no response)';
      results.style.display = 'block';
      status.textContent = '✅ Done! Scroll down to view the diagnosis.';
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (e) {
      errDiv.textContent = '⚠️ Error: ' + e.message;
      status.textContent = '';
    } finally {
      btn.disabled = false;
    }
  }
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the web UI."""
    return HTMLResponse(content=_HTML)


@app.post("/upload", response_model=DiagnoseResponse)
async def upload(file: UploadFile = File(...)):
    """
    Accept a .txt or .pdf patient report file and run the diagnostic pipeline.

    Returns specialist outputs and the final multidisciplinary diagnosis.
    """
    data = await file.read()
    medical_report = _extract_text_from_upload(file.filename or "", data)
    result = run_pipeline(medical_report)
    return DiagnoseResponse(**result)


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest):
    """
    Accept a plain-text medical report as JSON and run the diagnostic pipeline.

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
