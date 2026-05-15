import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from app.database import init_db, get_db
from app.services.grading import grade_answer
from app.services.scoring import calculate_grade

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = str(BASE_DIR / "static")

app = Flask(__name__)


def row_to_dict(row):
    return dict(row) if row else None


# ── Static files ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    full = BASE_DIR / "static" / path
    if full.exists() and full.is_file():
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


# ── Topics ────────────────────────────────────────────────────────────────────

@app.get("/api/topics/")
def list_topics():
    rows = get_db().execute(
        "SELECT id, level, name, description FROM topics ORDER BY level, id"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/topics/<topic_id>")
def get_topic(topic_id):
    row = get_db().execute(
        "SELECT id, level, name, description FROM topics WHERE id = ?", (topic_id,)
    ).fetchone()
    if not row:
        return jsonify({"detail": "Topic niet gevonden"}), 404
    return jsonify(dict(row))


# ── Exams ─────────────────────────────────────────────────────────────────────

@app.get("/api/exams/")
def list_exams():
    rows = get_db().execute(
        "SELECT id, title, year, timeframe, max_score, created_at FROM exams ORDER BY year DESC, timeframe"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/exams/")
def create_exam():
    b = request.get_json()
    db = get_db()
    cur = db.execute(
        "INSERT INTO exams (title, year, timeframe, max_score) VALUES (?, ?, ?, ?)",
        (b["title"], int(b["year"]), int(b["timeframe"]), int(b["max_score"])),
    )
    db.commit()
    row = db.execute(
        "SELECT id, title, year, timeframe, max_score, created_at FROM exams WHERE id = ?",
        (cur.lastrowid,)
    ).fetchone()
    return jsonify(dict(row)), 201


@app.get("/api/exams/<int:exam_id>")
def get_exam(exam_id):
    db = get_db()
    exam = db.execute(
        "SELECT id, title, year, timeframe, max_score, created_at FROM exams WHERE id = ?",
        (exam_id,)
    ).fetchone()
    if not exam:
        return jsonify({"detail": "Examen niet gevonden"}), 404
    questions = db.execute(
        """SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text
           FROM questions WHERE exam_id = ? ORDER BY number, sub_number""",
        (exam_id,)
    ).fetchall()
    result = dict(exam)
    result["questions"] = [dict(q) for q in questions]
    return jsonify(result)


@app.delete("/api/exams/<int:exam_id>")
def delete_exam(exam_id):
    db = get_db()
    db.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
    db.commit()
    return "", 204


@app.get("/api/exams/<int:exam_id>/questions")
def list_questions(exam_id):
    rows = get_db().execute(
        """SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text
           FROM questions WHERE exam_id = ? ORDER BY number, sub_number""",
        (exam_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/exams/<int:exam_id>/questions")
def create_question(exam_id):
    b = request.get_json()
    db = get_db()
    if not db.execute("SELECT id FROM exams WHERE id = ?", (exam_id,)).fetchone():
        return jsonify({"detail": "Examen niet gevonden"}), 404
    cur = db.execute(
        """INSERT INTO questions (exam_id, number, sub_number, max_points, official_answer, topic_id, question_text)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (exam_id, int(b["number"]), b.get("sub_number"), int(b["max_points"]),
         b["official_answer"], b.get("topic_id"), b.get("question_text")),
    )
    db.commit()
    row = db.execute(
        "SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text FROM questions WHERE id = ?",
        (cur.lastrowid,)
    ).fetchone()
    return jsonify(dict(row)), 201


@app.put("/api/exams/<int:exam_id>/questions/<int:question_id>")
def update_question(exam_id, question_id):
    b = request.get_json()
    db = get_db()
    if not db.execute("SELECT id FROM questions WHERE id = ? AND exam_id = ?", (question_id, exam_id)).fetchone():
        return jsonify({"detail": "Vraag niet gevonden"}), 404
    fields = ["number", "sub_number", "max_points", "official_answer", "topic_id", "question_text"]
    updates = {k: b[k] for k in fields if k in b and b[k] is not None}
    if updates:
        cols = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE questions SET {cols} WHERE id = ?", (*updates.values(), question_id))
        db.commit()
    row = db.execute(
        "SELECT id, exam_id, number, sub_number, max_points, official_answer, topic_id, question_text FROM questions WHERE id = ?",
        (question_id,)
    ).fetchone()
    return jsonify(dict(row))


@app.delete("/api/exams/<int:exam_id>/questions/<int:question_id>")
def delete_question(exam_id, question_id):
    db = get_db()
    db.execute("DELETE FROM questions WHERE id = ? AND exam_id = ?", (question_id, exam_id))
    db.commit()
    return "", 204


# ── Attempts ──────────────────────────────────────────────────────────────────

@app.post("/api/attempts/")
def start_attempt():
    b = request.get_json()
    db = get_db()
    if not db.execute("SELECT id FROM exams WHERE id = ?", (b["exam_id"],)).fetchone():
        return jsonify({"detail": "Examen niet gevonden"}), 404
    cur = db.execute("INSERT INTO attempts (exam_id) VALUES (?)", (b["exam_id"],))
    db.commit()
    return jsonify({"attempt_id": cur.lastrowid}), 201


@app.get("/api/attempts/")
def list_attempts():
    rows = get_db().execute(
        """SELECT a.id, a.exam_id, e.title AS exam_title, a.started_at, a.finished_at, a.raw_score, a.grade
           FROM attempts a JOIN exams e ON e.id = a.exam_id
           ORDER BY a.started_at DESC"""
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/attempts/<int:attempt_id>/submit")
def submit_attempt(attempt_id):
    db = get_db()
    attempt = db.execute(
        "SELECT a.id, a.exam_id, a.finished_at, e.title, e.max_score FROM attempts a JOIN exams e ON e.id = a.exam_id WHERE a.id = ?",
        (attempt_id,)
    ).fetchone()
    if not attempt:
        return jsonify({"detail": "Poging niet gevonden"}), 404
    if attempt["finished_at"]:
        return jsonify({"detail": "Poging is al ingeleverd"}), 400

    questions = db.execute(
        "SELECT id, number, sub_number, max_points, official_answer, topic_id FROM questions WHERE exam_id = ?",
        (attempt["exam_id"],)
    ).fetchall()
    q_map = {q["id"]: dict(q) for q in questions}
    topics = {t["id"]: t["name"] for t in db.execute("SELECT id, name FROM topics").fetchall()}

    b = request.get_json()
    graded = []
    total_earned = 0

    for ans_input in b["answers"]:
        q = q_map.get(ans_input["question_id"])
        if not q:
            continue
        earned, feedback = grade_answer(
            q["number"], q["sub_number"], q["max_points"],
            q["official_answer"], ans_input["student_answer"],
        )
        total_earned += earned
        db.execute(
            """INSERT INTO answers (attempt_id, question_id, student_answer, earned_points, claude_feedback, graded_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(attempt_id, question_id) DO UPDATE SET
                 student_answer=excluded.student_answer,
                 earned_points=excluded.earned_points,
                 claude_feedback=excluded.claude_feedback,
                 graded_at=excluded.graded_at""",
            (attempt_id, ans_input["question_id"], ans_input["student_answer"], earned, feedback),
        )
        graded.append({
            "question_id": ans_input["question_id"],
            "number": q["number"],
            "sub_number": q["sub_number"],
            "max_points": q["max_points"],
            "earned_points": earned,
            "topic_id": q["topic_id"],
            "topic_name": topics.get(q["topic_id"]) if q["topic_id"] else None,
            "student_answer": ans_input["student_answer"],
            "official_answer": q["official_answer"],
            "claude_feedback": feedback,
        })

    grade = calculate_grade(total_earned, attempt["max_score"])
    db.execute(
        "UPDATE attempts SET finished_at = CURRENT_TIMESTAMP, raw_score = ?, grade = ? WHERE id = ?",
        (total_earned, grade, attempt_id),
    )
    db.commit()
    graded.sort(key=lambda x: (x["number"], x["sub_number"] or ""))
    return jsonify({
        "attempt_id": attempt_id,
        "exam_id": attempt["exam_id"],
        "exam_title": attempt["title"],
        "raw_score": total_earned,
        "max_score": attempt["max_score"],
        "grade": grade,
        "answers": graded,
    })


@app.get("/api/attempts/<int:attempt_id>/results")
def get_results(attempt_id):
    db = get_db()
    attempt = db.execute(
        "SELECT a.id, a.exam_id, a.finished_at, a.raw_score, a.grade, e.title, e.max_score FROM attempts a JOIN exams e ON e.id = a.exam_id WHERE a.id = ?",
        (attempt_id,)
    ).fetchone()
    if not attempt:
        return jsonify({"detail": "Poging niet gevonden"}), 404
    if not attempt["finished_at"]:
        return jsonify({"detail": "Poging is nog niet ingeleverd"}), 400

    rows = db.execute(
        """SELECT ans.question_id, ans.student_answer, ans.earned_points, ans.claude_feedback,
                  q.number, q.sub_number, q.max_points, q.official_answer, q.topic_id, t.name AS topic_name
           FROM answers ans
           JOIN questions q ON q.id = ans.question_id
           LEFT JOIN topics t ON t.id = q.topic_id
           WHERE ans.attempt_id = ?
           ORDER BY q.number, q.sub_number""",
        (attempt_id,)
    ).fetchall()

    return jsonify({
        "attempt_id": attempt_id,
        "exam_id": attempt["exam_id"],
        "exam_title": attempt["title"],
        "raw_score": attempt["raw_score"] or 0,
        "max_score": attempt["max_score"],
        "grade": attempt["grade"] or 1.0,
        "answers": [dict(r) for r in rows],
    })


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/api/dashboard/summary")
def dashboard_summary():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM attempts WHERE finished_at IS NOT NULL").fetchone()[0]
    avg_row = db.execute("SELECT AVG(grade) FROM attempts WHERE finished_at IS NOT NULL").fetchone()
    avg_grade = round(avg_row[0], 1) if avg_row[0] else None

    mastery_rows = db.execute(
        """SELECT t.name, CAST(SUM(ans.earned_points) AS REAL) / NULLIF(SUM(q.max_points), 0) AS pct
           FROM topics t JOIN questions q ON q.topic_id = t.id
           JOIN answers ans ON ans.question_id = q.id
           JOIN attempts a ON ans.attempt_id = a.id AND a.finished_at IS NOT NULL
           GROUP BY t.id, t.name HAVING SUM(q.max_points) > 0"""
    ).fetchall()

    best = max(mastery_rows, key=lambda r: r["pct"] or 0)["name"] if mastery_rows else None
    worst = min(mastery_rows, key=lambda r: r["pct"] or 0)["name"] if mastery_rows else None

    return jsonify({"total_attempts": total, "avg_grade": avg_grade, "best_topic": best, "worst_topic": worst})


@app.get("/api/dashboard/topic_mastery")
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
           GROUP BY t.id, t.name, t.level ORDER BY t.level, t.id"""
    ).fetchall()

    result = []
    for r in rows:
        earned, possible, attempts = r["earned"], r["possible"], r["attempts"]
        pct = (earned / possible) if possible > 0 else None
        if pct is None or attempts == 0:
            mastery = "niet_gemaakt"
        elif pct >= 0.80:
            mastery = "beheerst"
        elif pct >= 0.55:
            mastery = "in_ontwikkeling"
        else:
            mastery = "aandacht_nodig"
        result.append({**dict(r), "pct": round(pct, 3) if pct is not None else None, "mastery": mastery})

    return jsonify(result)


@app.get("/api/dashboard/grade_history")
def grade_history():
    rows = get_db().execute(
        """SELECT a.id AS attempt_id, e.title AS exam_title, a.finished_at AS date, a.grade, a.raw_score, e.max_score
           FROM attempts a JOIN exams e ON e.id = a.exam_id
           WHERE a.finished_at IS NOT NULL ORDER BY a.finished_at"""
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=False)
