# Importing the needed modules
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from pathlib import Path
import pipeline  # loads apikey.env and GEMINI_API_KEY via module-level side-effect
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Read the medical report
report_path = (
    Path(__file__).parent
    / "Medical Reports"
    / "Medical Rerort - Michael Johnson - Panic Attack Disorder.txt"
)
with open(report_path, "r") as file:
    medical_report = file.read()

# Run the full diagnosis pipeline
result = pipeline.run_full_diagnosis(medical_report)

# Build output text
final_diagnosis_text = (
    "### Cardiologist:\n\n"
    + result["cardiologist"]
    + "\n\n### Psychologist:\n\n"
    + result["psychologist"]
    + "\n\n### Pulmonologist:\n\n"
    + result["pulmonologist"]
    + "\n\n### Final Diagnosis:\n\n"
    + result["final_diagnosis"]
)

# Save to Results/final_diagnosis.txt (pathlib, cross-platform)
txt_output_path = Path(__file__).parent / "Results" / "final_diagnosis.txt"
txt_output_path.parent.mkdir(parents=True, exist_ok=True)

with open(txt_output_path, "w") as txt_file:
    txt_file.write(final_diagnosis_text)

print(f"Final diagnosis has been saved to {txt_output_path}")


