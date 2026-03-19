"""
pipeline.py – Reusable diagnosis pipeline used by both app.py (web) and Main.py (CLI).
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    """
    Load environment variables for local development.
    If apikey.env exists next to this file, load it.
    In production (Render), GEMINI_API_KEY is set directly as an env var.
    """
    env_path = Path(__file__).parent / "apikey.env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


# Auto-load when the module is imported so CLI usage (Main.py) works out of the box.
load_environment()

from Utils.Agents import Cardiologist, Psychologist, Pulmonologist, MultidisciplinaryTeam


def _run_agent(agent_name: str, agent) -> tuple[str, str]:
    """Run a single agent and return (agent_name, response_text)."""
    response = agent.run()
    return agent_name, response or ""


def run_specialists(medical_report: str) -> dict:
    """Run the three specialist agents concurrently and return their responses."""
    agents = {
        "Cardiologist": Cardiologist(medical_report),
        "Psychologist": Psychologist(medical_report),
        "Pulmonologist": Pulmonologist(medical_report),
    }

    responses: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_run_agent, name, agent): name
            for name, agent in agents.items()
        }
        for future in as_completed(futures):
            agent_name, response = future.result()
            responses[agent_name] = response

    return responses


def run_team(responses: dict) -> str:
    """Run the MultidisciplinaryTeam agent and return the final diagnosis text."""
    team_agent = MultidisciplinaryTeam(
        cardiologist_report=responses.get("Cardiologist", ""),
        psychologist_report=responses.get("Psychologist", ""),
        pulmonologist_report=responses.get("Pulmonologist", ""),
    )
    return team_agent.run()


def run_full_diagnosis(medical_report: str) -> dict:
    """
    Run the complete pipeline and return a dict with all outputs.

    Returns:
        {
            "cardiologist": str,
            "psychologist": str,
            "pulmonologist": str,
            "final_diagnosis": str,
        }
    """
    responses = run_specialists(medical_report)
    final_diagnosis = run_team(responses)

    return {
        "cardiologist": responses.get("Cardiologist") or "",
        "psychologist": responses.get("Psychologist") or "",
        "pulmonologist": responses.get("Pulmonologist") or "",
        "final_diagnosis": final_diagnosis or "",
    }
