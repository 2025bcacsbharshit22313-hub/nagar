# Importing the needed modules
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import os
from dotenv import load_dotenv
from pathlib import Path
from pipeline import run_pipeline
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Loading API key from apikey.env for local development.
# In production, set GEMINI_API_KEY as an environment variable.
if os.path.exists("apikey.env"):
    load_dotenv(dotenv_path="apikey.env")

# Read the medical report
report_path = Path("Medical Reports") / "Medical Rerort - Michael Johnson - Panic Attack Disorder.txt"
with open(report_path, "r") as file:
    medical_report = file.read()

# Run the full diagnostic pipeline
result = run_pipeline(medical_report)

# Build output text
output_lines = [
    "### Cardiologist Report:\n",
    result["cardiologist"] or "",
    "\n\n### Psychologist Report:\n",
    result["psychologist"] or "",
    "\n\n### Pulmonologist Report:\n",
    result["pulmonologist"] or "",
    "\n\n### Final Diagnosis:\n",
    result["final_diagnosis"] or "",
]
final_diagnosis_text = "".join(output_lines)

# Save results to file
txt_output_path = Path("Results") / "final_diagnosis.txt"
txt_output_path.parent.mkdir(parents=True, exist_ok=True)
with open(txt_output_path, "w") as txt_file:
    txt_file.write(final_diagnosis_text)

print(f"Final diagnosis has been saved to {txt_output_path}")


