// AI Daily — interactive logic

// State
let completed = JSON.parse(localStorage.getItem('ai-daily-completed') || '{}');
let currentFilter = 'all';

function saveState() {
  localStorage.setItem('ai-daily-completed', JSON.stringify(completed));
  updateCounter();
}

function getCompletedCount() {
  return Object.values(completed).filter(Boolean).length;
}

function updateCounter() {
  const done = getCompletedCount();
  const total = 180;
  const pct = done / total;

  document.getElementById('counter-day').textContent = done;

  const ring = document.getElementById('ring-progress');
  const circumference = 2 * Math.PI * 90;
  const offset = circumference * (1 - pct);
  ring.style.strokeDashoffset = offset;
}

function incrementDay() {
  const next = getCompletedCount() + 1;
  if (next > 180) return;
  completed[next] = true;
  saveState();
  renderCalendar();
  // Flash the next incomplete day
  const nextCell = document.querySelector(`[data-day="${next + 1}"]`);
  if (nextCell) nextCell.classList.add('pulse');
  setTimeout(() => nextCell?.classList.remove('pulse'), 1000);
}

function resetDay() {
  if (confirm('Reset all 180 days? This will mark everything as incomplete.')) {
    completed = {};
    saveState();
    renderCalendar();
  }
}

function renderCalendar() {
  const grid = document.getElementById('calendar-grid');
  grid.innerHTML = '';

  DAYS.forEach(day => {
    const cell = document.createElement('div');
    cell.className = `day-cell month-${day.m}`;
    cell.dataset.day = day.d;
    if (day.weekend) cell.classList.add('weekend');
    if (day.capstone) cell.classList.add('capstone');
    if (currentFilter !== 'all' && String(day.m) !== currentFilter) cell.classList.add('hidden');
    if (completed[day.d]) cell.classList.add('completed');

    cell.textContent = day.d;
    cell.title = `Day ${day.d}: ${day.title} (${day.time} min)`;
    cell.addEventListener('click', () => openDayModal(day));

    grid.appendChild(cell);
  });
}

function openDayModal(day) {
  const modal = document.getElementById('day-modal');
  const body = document.getElementById('modal-body');
  const monthInfo = MONTH_INFO[day.m];

  body.innerHTML = `
    <p style="color: ${monthInfo.color}; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
      ${monthInfo.icon} Month ${day.m} · ${monthInfo.name}
    </p>
    <h2>Day ${day.d}: ${day.title}</h2>
    <p class="day-meta">
      <strong>${day.time} min</strong> ·
      <strong>${day.diff}</strong> ·
      Tags: ${day.tags.join(', ')}
    </p>

    <div style="background: linear-gradient(135deg, #E3F2FD, #F3E5F5); padding: 20px; border-radius: 16px; margin: 24px 0;">
      <h4 style="margin: 0 0 8px 0;">💡 Concept</h4>
      <p style="margin: 0; color: #424245; line-height: 1.6;">${day.concept}</p>
    </div>

    <h4>🛠️ What you'll build</h4>
    <p style="color: var(--gray-600); line-height: 1.6; margin: 8px 0 20px;">
      A working AI application that connects to <strong>${monthInfo.name.toLowerCase()}</strong>.
      You'll write real code, test it with real data, and deploy it to production.
    </p>

    <h4>⏱️ Time breakdown</h4>
    <ul style="margin: 8px 0 20px; padding-left: 20px; color: var(--gray-600); line-height: 1.8;">
      <li>5 min: Read the concept</li>
      <li>${day.time - 20} min: Build the project</li>
      <li>10 min: Test + push to GitHub</li>
      <li>5 min: Reflect + post in Discord</li>
    </ul>

    <h4>🎯 By the end you have</h4>
    <ul style="margin: 8px 0 20px; padding-left: 20px; color: var(--gray-600); line-height: 1.8;">
      <li>A working AI application deployed to production</li>
      <li>A new repo on your GitHub portfolio</li>
      <li>1 more day toward your 180-day streak</li>
    </ul>

    <div style="display: flex; gap: 12px; margin-top: 32px; flex-wrap: wrap;">
      <button class="btn btn-primary" onclick="markComplete(${day.d})" style="flex: 1; min-width: 200px;">
        ${completed[day.d] ? '✓ Completed (undo)' : '✓ Mark Day ' + day.d + ' complete'}
      </button>
      <button class="btn btn-secondary" onclick="closeModal()" style="flex: 0 0 auto;">Close</button>
    </div>
  `;

  modal.classList.add('open');
}

function closeModal() {
  document.getElementById('day-modal').classList.remove('open');
}

function markComplete(d) {
  completed[d] = !completed[d];
  if (!completed[d]) delete completed[d];
  saveState();
  renderCalendar();
  openDayModal(DAYS.find(day => day.d === d));
}

// Filter handlers
document.querySelectorAll('.filter-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    currentFilter = chip.dataset.month;
    renderCalendar();
  });
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = a.getAttribute('href');
    if (target === '#') return;
    e.preventDefault();
    document.querySelector(target)?.scrollIntoView({ behavior: 'smooth' });
  });
});

// Init
renderCalendar();
updateCounter();

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
  if (e.key === ' ' && e.target === document.body) {
    e.preventDefault();
    incrementDay();
  }
});
