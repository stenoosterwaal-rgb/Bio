import { api } from '/js/api.js';

const params = new URLSearchParams(location.search);
const attemptId = parseInt(params.get('attempt_id'));
if (!attemptId) location.href = '/exams.html';

async function load() {
  const result = await api.getResults(attemptId).catch(() => null);
  if (result) {
    location.href = `/results.html?attempt_id=${attemptId}`;
    return;
  }

  const attempts = await api.listAttempts();
  const attempt = attempts.find(a => a.id === attemptId);
  if (!attempt) { location.href = '/exams.html'; return; }

  const exam = await api.getExam(attempt.exam_id);
  document.getElementById('examTitle').textContent = exam.title;
  document.getElementById('examMeta').textContent = `${exam.questions.length} vragen · maximaal ${exam.max_score} punten`;
  document.title = `${exam.title} — Examen maken`;

  const container = document.getElementById('questionsContainer');
  container.innerHTML = exam.questions.map(q => `
    <div class="question-block">
      <div class="question-header">
        <span class="q-num">Vraag ${q.number}${q.sub_number || ''}</span>
        <span class="q-points">(${q.max_points} punt${q.max_points !== 1 ? 'en' : ''})</span>
        ${q.topic_id ? `<span class="badge badge-${q.topic_id[0]}" style="margin-left:auto">${q.topic_id}</span>` : ''}
      </div>
      ${q.question_text ? `<div class="q-text">${escHtml(q.question_text)}</div>` : ''}
      <textarea name="answer_${q.id}" rows="4" placeholder="Jouw antwoord…" style="width:100%;border:1px solid var(--border);border-radius:6px;padding:.5rem .75rem;font-family:inherit;font-size:.92rem;resize:vertical"></textarea>
    </div>`).join('');
}

document.getElementById('examForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const answers = [];
  for (const [key, val] of fd.entries()) {
    const qId = parseInt(key.replace('answer_', ''));
    answers.push({ question_id: qId, student_answer: val.trim() || '(geen antwoord)' });
  }

  document.getElementById('submitBtn').style.display = 'none';
  document.getElementById('loadingMsg').style.display = '';

  try {
    await api.submitAttempt(attemptId, { answers });
    location.href = `/results.html?attempt_id=${attemptId}`;
  } catch (err) {
    document.getElementById('submitBtn').style.display = '';
    document.getElementById('loadingMsg').style.display = 'none';
    const flash = document.getElementById('flash');
    flash.innerHTML = `<div class="flash flash-error">${err.message}</div>`;
  }
});

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

load().catch(console.error);
