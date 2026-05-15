import { api } from '/js/api.js';

async function load() {
  const [summary, mastery, history, attempts] = await Promise.all([
    api.getDashboard(),
    api.getTopicMastery(),
    api.getGradeHistory(),
    api.listAttempts(),
  ]);

  document.getElementById('totalAttempts').textContent = summary.total_attempts;
  document.getElementById('avgGrade').textContent = summary.avg_grade ?? '—';
  document.getElementById('bestTopic').textContent = summary.best_topic ?? '—';
  document.getElementById('worstTopic').textContent = summary.worst_topic ?? '—';

  renderChart(history);
  renderHeatmap(mastery);
  renderAttempts(attempts);
}

function renderChart(history) {
  const canvas = document.getElementById('gradeChart');
  const noHistory = document.getElementById('noHistory');
  if (!history.length) { canvas.style.display = 'none'; noHistory.style.display = ''; return; }

  const ctx = canvas.getContext('2d');
  const W = canvas.offsetWidth || 800;
  canvas.width = W;
  const H = 180;
  const pad = { top: 20, right: 20, bottom: 40, left: 40 };
  const grades = history.map(h => h.grade);
  const minG = Math.max(1, Math.min(...grades) - 1);
  const maxG = Math.min(10, Math.max(...grades) + 1);

  const toX = (i) => pad.left + (i / (history.length - 1 || 1)) * (W - pad.left - pad.right);
  const toY = (g) => pad.top + (1 - (g - minG) / (maxG - minG)) * (H - pad.top - pad.bottom);

  ctx.clearRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = '#e0e0e0'; ctx.lineWidth = 1;
  for (let g = Math.ceil(minG); g <= Math.floor(maxG); g++) {
    const y = toY(g);
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
    ctx.fillStyle = '#9E9E9E'; ctx.font = '11px Arial'; ctx.textAlign = 'right';
    ctx.fillText(g, pad.left - 5, y + 4);
  }

  // Pass/fail line at 5.5
  if (minG <= 5.5 && maxG >= 5.5) {
    ctx.strokeStyle = '#ffcccc'; ctx.lineWidth = 1.5; ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.moveTo(pad.left, toY(5.5)); ctx.lineTo(W - pad.right, toY(5.5)); ctx.stroke();
    ctx.setLineDash([]);
  }

  // Line
  ctx.strokeStyle = '#1565C0'; ctx.lineWidth = 2.5; ctx.lineJoin = 'round';
  ctx.beginPath();
  history.forEach((h, i) => {
    i === 0 ? ctx.moveTo(toX(i), toY(h.grade)) : ctx.lineTo(toX(i), toY(h.grade));
  });
  ctx.stroke();

  // Dots + labels
  history.forEach((h, i) => {
    const x = toX(i), y = toY(h.grade);
    ctx.fillStyle = h.grade >= 5.5 ? '#4CAF50' : '#f44336';
    ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#212121'; ctx.font = 'bold 11px Arial'; ctx.textAlign = 'center';
    ctx.fillText(h.grade.toFixed(1), x, y - 9);
  });

  // X labels (exam titles, truncated)
  history.forEach((h, i) => {
    const x = toX(i);
    ctx.fillStyle = '#757575'; ctx.font = '10px Arial'; ctx.textAlign = 'center';
    const label = h.exam_title.length > 18 ? h.exam_title.slice(0, 16) + '…' : h.exam_title;
    ctx.fillText(label, x, H - 6);
  });
}

function renderHeatmap(mastery) {
  const el = document.getElementById('heatmap');
  el.innerHTML = mastery.map(t => {
    const pctText = t.pct !== null ? Math.round(t.pct * 100) + '%' : '—';
    return `<div class="heatmap-cell cell-${t.mastery}" title="${t.topic_name}&#10;Gescoord: ${t.earned}/${t.possible}">
      <div class="code">${t.topic_id}</div>
      <div style="font-size:.85rem;margin:.1rem 0">${t.topic_name}</div>
      <div class="pct">${pctText}</div>
    </div>`;
  }).join('');
}

function renderAttempts(attempts) {
  const tbody = document.getElementById('attemptsBody');
  const noAttempts = document.getElementById('noAttempts');
  const finished = attempts.filter(a => a.finished_at);
  if (!finished.length) { noAttempts.style.display = ''; return; }
  tbody.innerHTML = finished.slice(0, 10).map(a => {
    const date = new Date(a.finished_at).toLocaleDateString('nl-NL');
    const gradeClass = (a.grade ?? 0) >= 5.5 ? 'grade-pass' : 'grade-fail';
    return `<tr>
      <td>${a.exam_title}</td>
      <td>${date}</td>
      <td>${a.raw_score ?? '—'}</td>
      <td class="${gradeClass}" style="font-weight:700">${a.grade?.toFixed(1) ?? '—'}</td>
      <td><a href="/results.html?attempt_id=${a.id}" class="btn btn-sm btn-secondary">Bekijken</a></td>
    </tr>`;
  }).join('');
}

load().catch(console.error);
