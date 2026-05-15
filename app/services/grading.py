import json
import anthropic
from app.config import ANTHROPIC_API_KEY


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
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # Strip possible markdown code fences
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
