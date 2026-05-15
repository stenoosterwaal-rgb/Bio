from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import CreateExam, ExamOut, ExamDetailOut, QuestionOut, CreateQuestion, UpdateQuestion

router = APIRouter()


@router.get("/", response_model=list[ExamOut])
def list_exams():
    db = get_db()
    rows = db.execute(
        "SELECT id, title, year, timeframe, max_score, created_at FROM exams ORDER BY year DESC, timeframe"
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/", response_model=ExamOut, status_code=201)
def create_exam(body: CreateExam):
    db = get_db()
    cur = db.execute(
        "INSERT INTO exams (title, year, timeframe, max_score) VALUES (?, ?, ?, ?)",
        (body.title, body.year, body.timeframe, body.max_score),
    )
    db.commit()
    row = db.execute(
        "SELECT id, title, year, timeframe, max_score, created_at FROM exams WHERE id = ?",
        (cur.lastrowid,)
    ).fetchone()
    return dict(row)


@router.get("/{exam_id}", response_model=ExamDetailOut)
def get_exam(exam_id: int):
    db = get_db()
    exam = db.execute(
        "SELECT id, title, year, timeframe, max_score, created_at FROM exams WHERE id = ?",
        (exam_id,)
    ).fetchone()
    if not exam:
        raise HTTPException(404, "Examen niet gevonden")
    questions = db.execute(
        """SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text
           FROM questions WHERE exam_id = ? ORDER BY number, sub_number""",
        (exam_id,)
    ).fetchall()
    result = dict(exam)
    result["questions"] = [dict(q) for q in questions]
    return result


@router.delete("/{exam_id}", status_code=204)
def delete_exam(exam_id: int):
    db = get_db()
    db.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
    db.commit()


@router.get("/{exam_id}/questions", response_model=list[QuestionOut])
def list_questions(exam_id: int):
    db = get_db()
    rows = db.execute(
        """SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text
           FROM questions WHERE exam_id = ? ORDER BY number, sub_number""",
        (exam_id,)
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/{exam_id}/questions", response_model=QuestionOut, status_code=201)
def create_question(exam_id: int, body: CreateQuestion):
    db = get_db()
    exam = db.execute("SELECT id FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if not exam:
        raise HTTPException(404, "Examen niet gevonden")
    cur = db.execute(
        """INSERT INTO questions (exam_id, number, sub_number, max_points, official_answer, topic_id, question_text)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (exam_id, body.number, body.sub_number, body.max_points,
         body.official_answer, body.topic_id, body.question_text),
    )
    db.commit()
    row = db.execute(
        "SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text FROM questions WHERE id = ?",
        (cur.lastrowid,)
    ).fetchone()
    return dict(row)


@router.put("/{exam_id}/questions/{question_id}", response_model=QuestionOut)
def update_question(exam_id: int, question_id: int, body: UpdateQuestion):
    db = get_db()
    q = db.execute("SELECT * FROM questions WHERE id = ? AND exam_id = ?", (question_id, exam_id)).fetchone()
    if not q:
        raise HTTPException(404, "Vraag niet gevonden")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        cols = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE questions SET {cols} WHERE id = ?", (*updates.values(), question_id))
        db.commit()
    row = db.execute(
        "SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text FROM questions WHERE id = ?",
        (question_id,)
    ).fetchone()
    return dict(row)


@router.delete("/{exam_id}/questions/{question_id}", status_code=204)
def delete_question(exam_id: int, question_id: int):
    db = get_db()
    db.execute("DELETE FROM questions WHERE id = ? AND exam_id = ?", (question_id, exam_id))
    db.commit()
