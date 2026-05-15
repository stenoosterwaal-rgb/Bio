import { api } from '/js/api.js';

const params = new URLSearchParams(location.search);
const examId = parseInt(params.get('exam_id'));
if (!examId) location.href = '/exams.html';

let topics = [];

async function load() {
  const [exam, allTopics] = await Promise.all([api.getExam(examId), api.getTopics()]);
  topics = allTopics;

  document.getElementById('examTitle').textContent = exam.title;
  document.title = `${exam.title} — VWO Biologie Tracker`;

  const sel = document.getElementById('topicSelect');
  const levels = [...new Set(allTopics.map(t => t.level))].sort();
  levels.forEach(lvl => {
    const grp = document.createElement('optgroup');
    grp.label = lvl === 'M' ? 'Molecuul/cel' : lvl === 'O' ? 'Orgaan/organisme' : lvl === 'P' ? 'Populatie/ecosysteem' : 'Vaardigheden';
    allTopics.filter(t => t.level === lvl).forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = `${t.id} — ${t.name}`;
      grp.appendChild(opt);
    });
    sel.appendChild(grp);
  });

  renderQuestions(exam.questions);
}

function renderQuestions(questions) {
  const tbody = document.getElementById('questionsBody');
  const noQ = document.getElementById('noQuestions');
  if (!questions.length) { noQ.style.display = ''; return; }
  noQ.style.display = 'none';
  const topicMap = Object.fromEntries(topics.map(t => [t.id, t]));
  tbody.innerHTML = questions.map(q => {
    const t = q.topic_id ? topicMap[q.topic_id] : null;
    const badge = t ? `<span class="badge badge-${t.level}">${t.id}</span>` : '—';
    const ans = q.official_answer.length > 60 ? q.official_answer.slice(0, 58) + '…' : q.official_answer;
    return `<tr>
      <td>${q.number}</td>
      <td>${q.sub_number || '—'}</td>
      <td>${q.max_points}</td>
      <td>${badge}</td>
      <td title="${q.official_answer}" style="font-size:.82rem">${ans}</td>
      <td><button class="btn btn-danger" onclick="deleteQ(${q.id})">×</button></td>
    </tr>`;
  }).join('');
}

document.getElementById('addQuestionForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.createQuestion(examId, {
      number: parseInt(fd.get('number')),
      sub_number: fd.get('sub_number') || null,
      max_points: parseInt(fd.get('max_points')),
      official_answer: fd.get('official_answer'),
      topic_id: fd.get('topic_id') || null,
      question_text: fd.get('question_text') || null,
    });
    e.target.reset();
    flash('Vraag toegevoegd.', 'success');
    const exam = await api.getExam(examId);
    renderQuestions(exam.questions);
  } catch (err) {
    flash(err.message, 'error');
  }
});

window.deleteQ = async (qId) => {
  if (!confirm('Vraag verwijderen?')) return;
  await api.deleteQuestion(examId, qId);
  const exam = await api.getExam(examId);
  renderQuestions(exam.questions);
};

document.getElementById('startBtn').addEventListener('click', async () => {
  try {
    const { attempt_id } = await api.startAttempt(examId);
    location.href = `/attempt.html?attempt_id=${attempt_id}`;
  } catch (err) {
    flash(err.message, 'error');
  }
});

function flash(msg, type) {
  const el = document.getElementById('flash');
  el.innerHTML = `<div class="flash flash-${type}">${msg}</div>`;
  setTimeout(() => el.innerHTML = '', 3000);
}

load().catch(console.error);
