const BASE = '/api';

async function apiFetch(path, options = {}) {
  const resp = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

export const api = {
  getTopics:       ()           => apiFetch('/topics/'),
  getTopic:        (id)         => apiFetch(`/topics/${id}`),

  getExams:        ()           => apiFetch('/exams/'),
  createExam:      (body)       => apiFetch('/exams/', { method: 'POST', body: JSON.stringify(body) }),
  getExam:         (id)         => apiFetch(`/exams/${id}`),
  deleteExam:      (id)         => apiFetch(`/exams/${id}`, { method: 'DELETE' }),

  getQuestions:    (examId)     => apiFetch(`/exams/${examId}/questions`),
  createQuestion:  (examId, b)  => apiFetch(`/exams/${examId}/questions`, { method: 'POST', body: JSON.stringify(b) }),
  updateQuestion:  (examId, qId, b) => apiFetch(`/exams/${examId}/questions/${qId}`, { method: 'PUT', body: JSON.stringify(b) }),
  deleteQuestion:  (examId, qId)    => apiFetch(`/exams/${examId}/questions/${qId}`, { method: 'DELETE' }),

  startAttempt:    (examId)     => apiFetch('/attempts/', { method: 'POST', body: JSON.stringify({ exam_id: examId }) }),
  listAttempts:    ()           => apiFetch('/attempts/'),
  submitAttempt:   (id, body)   => apiFetch(`/attempts/${id}/submit`, { method: 'POST', body: JSON.stringify(body) }),
  getResults:      (id)         => apiFetch(`/attempts/${id}/results`),

  getDashboard:    ()           => apiFetch('/dashboard/summary'),
  getTopicMastery: ()           => apiFetch('/dashboard/topic_mastery'),
  getGradeHistory: ()           => apiFetch('/dashboard/grade_history'),
};
