import { api } from '/js/api.js';

async function loadExams() {
  const [exams] = await Promise.all([api.getExams()]);
  const tbody = document.getElementById('examsBody');
  const noExams = document.getElementById('noExams');
  if (!exams.length) { noExams.style.display = ''; return; }
  noExams.style.display = 'none';
  tbody.innerHTML = exams.map(e => `
    <tr>
      <td><a href="/exam_detail.html?exam_id=${e.id}">${e.title}</a></td>
      <td>${e.year}</td>
      <td>Tijdvak ${e.timeframe}</td>
      <td>${e.max_score}</td>
      <td><a href="/exam_detail.html?exam_id=${e.id}" class="btn btn-sm btn-secondary">Beheren</a></td>
      <td><button class="btn btn-danger" onclick="deleteExam(${e.id})">Verwijder</button></td>
    </tr>`).join('');
}

document.getElementById('addExamForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.createExam({
      title: fd.get('title'),
      year: parseInt(fd.get('year')),
      timeframe: parseInt(fd.get('timeframe')),
      max_score: parseInt(fd.get('max_score')),
    });
    e.target.reset();
    flash('Examen toegevoegd.', 'success');
    loadExams();
  } catch (err) {
    flash(err.message, 'error');
  }
});

window.deleteExam = async (id) => {
  if (!confirm('Examen en alle bijbehorende gegevens verwijderen?')) return;
  await api.deleteExam(id);
  loadExams();
};

function flash(msg, type) {
  const el = document.getElementById('flash');
  el.innerHTML = `<div class="flash flash-${type}">${msg}</div>`;
  setTimeout(() => el.innerHTML = '', 3000);
}

loadExams().catch(console.error);
