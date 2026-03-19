"""
Shared pipeline logic for the medical diagnostics agents.
Can be used by both app.py (web server) and Main.py (CLI).
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from Utils.Agents import Cardiologist, Psychologist, Pulmonologist, MultidisciplinaryTeam


def _run_agent(agent_name: str, agent) -> tuple:
    """Run a single agent and return (name, response)."""
    response = agent.run()
    return agent_name, response


def run_specialists(medical_report: str) -> dict:
    """
    Run the three specialist agents concurrently.

    Returns a dict with keys: 'Cardiologist', 'Psychologist', 'Pulmonologist'.
    """
    agents = {
        "Cardiologist": Cardiologist(medical_report),
        "Psychologist": Psychologist(medical_report),
        "Pulmonologist": Pulmonologist(medical_report),
    }

    responses = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_run_agent, name, agent): name
            for name, agent in agents.items()
        }
        for future in as_completed(futures):
            agent_name, response = future.result()
            responses[agent_name] = response

    return responses


def run_team(specialist_responses: dict) -> str:
    """
    Run the MultidisciplinaryTeam agent given the specialist responses.

    Returns the final diagnosis string.
    """
    team_agent = MultidisciplinaryTeam(
        cardiologist_report=specialist_responses.get("Cardiologist", ""),
        psychologist_report=specialist_responses.get("Psychologist", ""),
        pulmonologist_report=specialist_responses.get("Pulmonologist", ""),
    )
    return team_agent.run()


def run_pipeline(medical_report: str) -> dict:
    """
    Run the full diagnostic pipeline.

    Returns a dict with keys:
      cardiologist, psychologist, pulmonologist, final_diagnosis
    """
    specialist_responses = run_specialists(medical_report)
    final_diagnosis = run_team(specialist_responses)
    return {
        "cardiologist": specialist_responses.get("Cardiologist", ""),
        "psychologist": specialist_responses.get("Psychologist", ""),
        "pulmonologist": specialist_responses.get("Pulmonologist", ""),
        "final_diagnosis": final_diagnosis or "",
    }
