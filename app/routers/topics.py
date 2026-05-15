from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import TopicOut

router = APIRouter()


@router.get("/", response_model=list[TopicOut])
def list_topics():
    db = get_db()
    rows = db.execute("SELECT id, level, name, description FROM topics ORDER BY level, id").fetchall()
    return [dict(r) for r in rows]


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(topic_id: str):
    db = get_db()
    row = db.execute("SELECT id, level, name, description FROM topics WHERE id = ?", (topic_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Topic niet gevonden")
    return dict(row)
