import json
import httpx
from app.config import ANTHROPIC_API_KEY

API_URL = "https://api.anthropic.com/v1/messages"


def grade_answer(number: int, sub_number: str | None, max_points: int,
                 official_answer: str, student_answer: str) -> tuple[int, str]:
    sub = sub_number or ""
    prompt = f"""Jij bent een VWO Biologie corrector.

Vraag {number}{sub}: maximaal {max_points} punt(en)

Officieel antwoord:
{official_answer}

Antwoord van de leerling:
{student_answer}

Beoordeel als corrector:
1. Hoeveel punten krijgt de leerling? (0 t/m {max_points}, geheel getal)
2. Korte uitleg in het Nederlands (max 2 zinnen)

Antwoord uitsluitend in dit JSON-formaat:
{{"punten": <int>, "feedback": "<string>"}}"""

    try:
        resp = httpx.post(
            API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 256,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        punten = max(0, min(max_points, int(data["punten"])))
        feedback = str(data.get("feedback", ""))
        return punten, feedback
    except Exception:
        return 0, "Kon niet automatisch corrigeren."
