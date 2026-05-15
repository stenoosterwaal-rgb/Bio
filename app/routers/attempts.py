from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import StartAttempt, SubmitAttempt, AttemptResult, AttemptOut, GradedAnswer
from app.services.grading import grade_answer
from app.services.scoring import calculate_grade

router = APIRouter()


@router.post("/", status_code=201)
def start_attempt(body: StartAttempt):
    db = get_db()
    exam = db.execute("SELECT id FROM exams WHERE id = ?", (body.exam_id,)).fetchone()
    if not exam:
        raise HTTPException(404, "Examen niet gevonden")
    cur = db.execute("INSERT INTO attempts (exam_id) VALUES (?)", (body.exam_id,))
    db.commit()
    return {"attempt_id": cur.lastrowid}


@router.get("/", response_model=list[AttemptOut])
def list_attempts():
    db = get_db()
    rows = db.execute(
        """SELECT a.id, a.exam_id, e.title AS exam_title, a.started_at, a.finished_at, a.raw_score, a.grade
           FROM attempts a JOIN exams e ON e.id = a.exam_id
           ORDER BY a.started_at DESC"""
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/{attempt_id}/submit", response_model=AttemptResult)
def submit_attempt(attempt_id: int, body: SubmitAttempt):
    db = get_db()
    attempt = db.execute(
        "SELECT a.id, a.exam_id, a.finished_at, e.title, e.max_score FROM attempts a JOIN exams e ON e.id = a.exam_id WHERE a.id = ?",
        (attempt_id,)
    ).fetchone()
    if not attempt:
        raise HTTPException(404, "Poging niet gevonden")
    if attempt["finished_at"]:
        raise HTTPException(400, "Poging is al ingeleverd")

    questions = db.execute(
        """SELECT id, number, sub_number, max_points, official_answer, topic_id
           FROM questions WHERE exam_id = ?""",
        (attempt["exam_id"],)
    ).fetchall()
    q_map = {q["id"]: dict(q) for q in questions}

    topics = {t["id"]: t["name"] for t in db.execute("SELECT id, name FROM topics").fetchall()}

    graded = []
    total_earned = 0

    for ans_input in body.answers:
        q = q_map.get(ans_input.question_id)
        if not q:
            continue
        earned, feedback = grade_answer(
            q["number"], q["sub_number"], q["max_points"],
            q["official_answer"], ans_input.student_answer,
        )
        total_earned += earned
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            """INSERT INTO answers (attempt_id, question_id, student_answer, earned_points, claude_feedback, graded_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(attempt_id, question_id) DO UPDATE SET
                 student_answer=excluded.student_answer,
                 earned_points=excluded.earned_points,
                 claude_feedback=excluded.claude_feedback,
                 graded_at=excluded.graded_at""",
            (attempt_id, ans_input.question_id, ans_input.student_answer, earned, feedback, now),
        )
        graded.append(GradedAnswer(
            question_id=ans_input.question_id,
            number=q["number"],
            sub_number=q["sub_number"],
            max_points=q["max_points"],
            earned_points=earned,
            topic_id=q["topic_id"],
            topic_name=topics.get(q["topic_id"]) if q["topic_id"] else None,
            student_answer=ans_input.student_answer,
            official_answer=q["official_answer"],
            claude_feedback=feedback,
        ))

    grade = calculate_grade(total_earned, attempt["max_score"])
    db.execute(
        "UPDATE attempts SET finished_at = CURRENT_TIMESTAMP, raw_score = ?, grade = ? WHERE id = ?",
        (total_earned, grade, attempt_id),
    )
    db.commit()

    graded.sort(key=lambda x: (x.number, x.sub_number or ""))

    return AttemptResult(
        attempt_id=attempt_id,
        exam_id=attempt["exam_id"],
        exam_title=attempt["title"],
        raw_score=total_earned,
        max_score=attempt["max_score"],
        grade=grade,
        answers=graded,
    )


@router.get("/{attempt_id}/results", response_model=AttemptResult)
def get_results(attempt_id: int):
    db = get_db()
    attempt = db.execute(
        "SELECT a.id, a.exam_id, a.finished_at, a.raw_score, a.grade, e.title, e.max_score FROM attempts a JOIN exams e ON e.id = a.exam_id WHERE a.id = ?",
        (attempt_id,)
    ).fetchone()
    if not attempt:
        raise HTTPException(404, "Poging niet gevonden")
    if not attempt["finished_at"]:
        raise HTTPException(400, "Poging is nog niet ingeleverd")

    rows = db.execute(
        """SELECT ans.question_id, ans.student_answer, ans.earned_points, ans.claude_feedback,
                  q.number, q.sub_number, q.max_points, q.official_answer, q.topic_id,
                  t.name AS topic_name
           FROM answers ans
           JOIN questions q ON q.id = ans.question_id
           LEFT JOIN topics t ON t.id = q.topic_id
           WHERE ans.attempt_id = ?
           ORDER BY q.number, q.sub_number""",
        (attempt_id,)
    ).fetchall()

    answers = [
        GradedAnswer(
            question_id=r["question_id"],
            number=r["number"],
            sub_number=r["sub_number"],
            max_points=r["max_points"],
            earned_points=r["earned_points"] or 0,
            topic_id=r["topic_id"],
            topic_name=r["topic_name"],
            student_answer=r["student_answer"],
            official_answer=r["official_answer"],
            claude_feedback=r["claude_feedback"],
        )
        for r in rows
    ]

    return AttemptResult(
        attempt_id=attempt_id,
        exam_id=attempt["exam_id"],
        exam_title=attempt["title"],
        raw_score=attempt["raw_score"] or 0,
        max_score=attempt["max_score"],
        grade=attempt["grade"] or 1.0,
        answers=answers,
    )
