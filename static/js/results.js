import { api } from '/js/api.js';

const params = new URLSearchParams(location.search);
const attemptId = parseInt(params.get('attempt_id'));
if (!attemptId) location.href = '/';

async function load() {
  const result = await api.getResults(attemptId);

  document.title = `Resultaten ${result.exam_title}`;
  document.getElementById('examTitleEl').textContent = result.exam_title;

  const grade = result.grade;
  const gradeEl = document.getElementById('gradeBig');
  gradeEl.textContent = grade.toFixed(1);
  gradeEl.className = 'grade-big ' + (grade >= 5.5 ? 'grade-pass' : 'grade-fail');
  document.getElementById('scoreLine').textContent =
    `${result.raw_score} van ${result.max_score} punten (${Math.round(result.raw_score / result.max_score * 100)}%)`;

  // Group by topic
  const byTopic = {};
  for (const ans of result.answers) {
    const key = ans.topic_id || '__none__';
    if (!byTopic[key]) byTopic[key] = { name: ans.topic_name || 'Geen onderwerp', level: ans.topic_id?.[0] || '', answers: [] };
    byTopic[key].answers.push(ans);
  }

  const container = document.getElementById('resultsByTopic');
  container.innerHTML = Object.entries(byTopic).map(([topicId, group]) => {
    const earned = group.answers.reduce((s, a) => s + a.earned_points, 0);
    const possible = group.answers.reduce((s, a) => s + a.max_points, 0);
    const pct = possible ? Math.round(earned / possible * 100) : 0;
    const badge = topicId !== '__none__' ? `<span class="badge badge-${group.level}">${topicId}</span>` : '';

    const rows = group.answers.map(a => {
      const correct = a.earned_points === a.max_points;
      const partial = a.earned_points > 0 && a.earned_points < a.max_points;
      const dot = correct ? '✓' : (partial ? '~' : '✗');
      const dotColor = correct ? 'var(--green)' : (partial ? 'var(--orange)' : 'var(--red)');
      return `<tr class="answer-row">
        <td style="font-weight:700;white-space:nowrap">
          <span style="color:${dotColor};margin-right:.3rem">${dot}</span>
          ${a.number}${a.sub_number || ''}
        </td>
        <td>${a.earned_points} / ${a.max_points}</td>
        <td class="student-ans">${escHtml(a.student_answer)}</td>
        <td class="official-ans">${escHtml(a.official_answer)}</td>
        <td class="feedback-cell">${escHtml(a.claude_feedback || '')}</td>
      </tr>`;
    }).join('');

    return `<div class="topic-section">
      <h3>${badge} ${escHtml(group.name)} — ${earned}/${possible} punten (${pct}%)</h3>
      <table>
        <thead><tr><th>Nr</th><th>Score</th><th>Jouw antwoord</th><th>Officieel antwoord</th><th>Feedback</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }).join('');
}

function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
}

load().catch(e => {
  document.getElementById('resultsByTopic').innerHTML = `<div class="flash flash-error">${e.message}</div>`;
});
