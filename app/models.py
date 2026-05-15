from pydantic import BaseModel
from typing import Optional


class TopicOut(BaseModel):
    id: str
    level: str
    name: str
    description: Optional[str]


class CreateExam(BaseModel):
    title: str
    year: int
    timeframe: int
    max_score: int


class ExamOut(BaseModel):
    id: int
    title: str
    year: int
    timeframe: int
    max_score: int
    created_at: str


class CreateQuestion(BaseModel):
    number: int
    sub_number: Optional[str] = None
    max_points: int
    official_answer: str
    topic_id: Optional[str] = None
    question_text: Optional[str] = None


class UpdateQuestion(BaseModel):
    number: Optional[int] = None
    sub_number: Optional[str] = None
    max_points: Optional[int] = None
    official_answer: Optional[str] = None
    topic_id: Optional[str] = None
    question_text: Optional[str] = None


class QuestionOut(BaseModel):
    id: int
    exam_id: int
    number: int
    sub_number: Optional[str]
    max_points: int
    official_answer: str
    topic_id: Optional[str]
    question_text: Optional[str]


class ExamDetailOut(BaseModel):
    id: int
    title: str
    year: int
    timeframe: int
    max_score: int
    created_at: str
    questions: list[QuestionOut]


class StartAttempt(BaseModel):
    exam_id: int


class AnswerInput(BaseModel):
    question_id: int
    student_answer: str


class SubmitAttempt(BaseModel):
    answers: list[AnswerInput]


class GradedAnswer(BaseModel):
    question_id: int
    number: int
    sub_number: Optional[str]
    max_points: int
    earned_points: int
    topic_id: Optional[str]
    topic_name: Optional[str]
    student_answer: str
    official_answer: str
    claude_feedback: Optional[str]


class AttemptResult(BaseModel):
    attempt_id: int
    exam_id: int
    exam_title: str
    raw_score: int
    max_score: int
    grade: float
    answers: list[GradedAnswer]


class AttemptOut(BaseModel):
    id: int
    exam_id: int
    exam_title: str
    started_at: str
    finished_at: Optional[str]
    raw_score: Optional[int]
    grade: Optional[float]


class TopicMastery(BaseModel):
    topic_id: str
    topic_name: str
    level: str
    attempts: int
    earned: int
    possible: int
    pct: Optional[float]
    mastery: str


class DashboardSummary(BaseModel):
    total_attempts: int
    avg_grade: Optional[float]
    best_topic: Optional[str]
    worst_topic: Optional[str]
