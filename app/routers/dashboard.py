from fastapi import APIRouter
from app.database import get_db
from app.models import DashboardSummary, TopicMastery

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM attempts WHERE finished_at IS NOT NULL").fetchone()[0]
    avg_row = db.execute("SELECT AVG(grade) FROM attempts WHERE finished_at IS NOT NULL").fetchone()
    avg_grade = round(avg_row[0], 1) if avg_row[0] else None

    mastery_rows = db.execute(
        """SELECT t.name,
                  CAST(SUM(ans.earned_points) AS REAL) / NULLIF(SUM(q.max_points), 0) AS pct
           FROM topics t
           JOIN questions q ON q.topic_id = t.id
           JOIN answers ans ON ans.question_id = q.id
           JOIN attempts a ON ans.attempt_id = a.id AND a.finished_at IS NOT NULL
           GROUP BY t.id, t.name
           HAVING SUM(q.max_points) > 0"""
    ).fetchall()

    best = None
    worst = None
    if mastery_rows:
        best_row = max(mastery_rows, key=lambda r: r["pct"] or 0)
        worst_row = min(mastery_rows, key=lambda r: r["pct"] or 0)
        best = best_row["name"]
        worst = worst_row["name"]

    return DashboardSummary(
        total_attempts=total,
        avg_grade=avg_grade,
        best_topic=best,
        worst_topic=worst,
    )


@router.get("/topic_mastery", response_model=list[TopicMastery])
def topic_mastery():
    db = get_db()
    rows = db.execute(
        """SELECT t.id AS topic_id, t.name AS topic_name, t.level,
                  COUNT(DISTINCT a.id) AS attempts,
                  COALESCE(SUM(ans.earned_points), 0) AS earned,
                  COALESCE(SUM(q.max_points), 0) AS possible
           FROM topics t
           LEFT JOIN questions q ON q.topic_id = t.id
           LEFT JOIN answers ans ON ans.question_id = q.id
           LEFT JOIN attempts a ON ans.attempt_id = a.id AND a.finished_at IS NOT NULL
           GROUP BY t.id, t.name, t.level
           ORDER BY t.level, t.id"""
    ).fetchall()

    result = []
    for r in rows:
        attempts = r["attempts"]
        earned = r["earned"]
        possible = r["possible"]
        pct = (earned / possible) if possible > 0 else None

        if pct is None or attempts == 0:
            mastery = "niet_gemaakt"
        elif pct >= 0.80:
            mastery = "beheerst"
        elif pct >= 0.55:
            mastery = "in_ontwikkeling"
        else:
            mastery = "aandacht_nodig"

        result.append(TopicMastery(
            topic_id=r["topic_id"],
            topic_name=r["topic_name"],
            level=r["level"],
            attempts=attempts,
            earned=earned,
            possible=possible,
            pct=round(pct, 3) if pct is not None else None,
            mastery=mastery,
        ))

    return result


@router.get("/grade_history")
def grade_history():
    db = get_db()
    rows = db.execute(
        """SELECT a.id AS attempt_id, e.title AS exam_title, a.finished_at AS date,
                  a.grade, a.raw_score, e.max_score
           FROM attempts a JOIN exams e ON e.id = a.exam_id
           WHERE a.finished_at IS NOT NULL
           ORDER BY a.finished_at"""
    ).fetchall()
    return [dict(r) for r in rows]
