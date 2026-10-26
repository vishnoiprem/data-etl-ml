// AIForBiz Course Platform - Frontend
let currentUser = null;
let course = null;

// Load saved user from localStorage
const saved = localStorage.getItem('courseUser');
if (saved) {
  currentUser = JSON.parse(saved);
  document.getElementById('signup-section').style.display = 'none';
  document.getElementById('user-info').textContent = `Welcome back, ${currentUser.name}!`;
  loadProgress();
}

// Load course on startup
loadCourse();
loadStats();
loadLeaderboard();

// Signup form
document.getElementById('signup-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();

  try {
    const res = await fetch('/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail);
    }
    const data = await res.json();
    currentUser = data.user;
    localStorage.setItem('courseUser', JSON.stringify(currentUser));
    document.getElementById('signup-section').style.display = 'none';
    document.getElementById('user-info').textContent = `Welcome, ${currentUser.name}!`;
    document.getElementById('signup-msg').textContent = '';
    loadProgress();
  } catch (err) {
    document.getElementById('signup-msg').style.color = '#E74C3C';
    document.getElementById('signup-msg').textContent = `❌ ${err.message}`;
  }
});

async function loadCourse() {
  const res = await fetch('/api/course');
  course = await res.json();
  renderCourse();
}

async function loadStats() {
  const res = await fetch('/api/course/stats');
  const stats = await res.json();
  document.getElementById('stat-modules').textContent = stats.modules;
  document.getElementById('stat-lessons').textContent = stats.lessons;
  document.getElementById('stat-hours').textContent = stats.total_hours;
}

async function loadLeaderboard() {
  const res = await fetch('/api/leaderboard');
  const board = await res.json();
  const ol = document.getElementById('leaderboard');
  ol.innerHTML = board.map(u => `
    <li>
      ${u.name} - ${u.completion}%
      <span class="completion-bar"><span class="completion-fill" style="width: ${u.completion}%"></span></span>
      <small style="color: var(--muted); margin-left: 8px">${u.completed_lessons} lessons</small>
    </li>
  `).join('') || '<li>No students yet. Be the first!</li>';
}

async function loadProgress() {
  if (!currentUser) return;
  const res = await fetch(`/api/progress/${currentUser.email}`);
  const progress = await res.json();
  Object.entries(progress).forEach(([lessonId, data]) => {
    if (data.completed) {
      const cb = document.querySelector(`input[data-lesson="${lessonId}"]`);
      if (cb) {
        cb.checked = true;
        cb.closest('.lesson').classList.add('completed');
      }
    }
  });
  updateProgressDisplay(progress);
}

function updateProgressDisplay(progress) {
  if (!course) return;
  const total = course.modules.reduce((sum, m) => sum + m.lessons.length, 0);
  const done = Object.values(progress).filter(p => p.completed).length;
  const pct = total ? Math.round((done / total) * 100) : 0;
  document.getElementById('stat-progress').textContent = `${pct}%`;
}

function renderCourse() {
  const container = document.getElementById('course');
  container.innerHTML = course.modules.map(m => `
    <div class="module">
      <h3>Module ${m.id}: ${m.title}</h3>
      ${m.lessons.map(l => `
        <div class="lesson">
          <input type="checkbox" data-lesson="${l.id}" ${currentUser ? '' : 'disabled'} />
          <div class="lesson-info">
            <strong>${l.id}: ${l.title}</strong>
            <span>${l.duration} minutes</span>
          </div>
          <a href="${l.video}" target="_blank" class="video-link">Watch</a>
        </div>
      `).join('')}
    </div>
  `).join('');

  // Wire up checkboxes
  container.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', async (e) => {
      if (!currentUser) return;
      const lessonId = cb.dataset.lesson;
      cb.closest('.lesson').classList.toggle('completed', cb.checked);
      const res = await fetch('/api/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: currentUser.email,
          lesson_id: lessonId,
          completed: cb.checked
        })
      });
      const data = await res.json();
      document.getElementById('stat-progress').textContent = `${data.completion_pct}%`;
      loadLeaderboard(); // refresh after each completion
    });
  });
}
