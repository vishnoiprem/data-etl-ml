// AIForBiz landing page — handles email signup
// In production, this would POST to your ConvertKit/EmailOctopus API.
// For prototype, we save to localStorage and show a success message.

const form = document.getElementById('signup-form');
const msg = document.getElementById('form-msg');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('email').value.trim();

  if (!email) return;
  if (!email.includes('@')) {
    msg.textContent = '❌ Please enter a valid email.';
    msg.style.color = '#FFD700';
    return;
  }

  // Save to localStorage (prototype only)
  const signups = JSON.parse(localStorage.getItem('signups') || '[]');
  signups.push({ email, timestamp: new Date().toISOString() });
  localStorage.setItem('signups', JSON.stringify(signups));

  // In production, replace with:
  // await fetch('https://api.convertkit.com/v3/forms/.../subscribe', {
  //   method: 'POST',
  //   body: JSON.stringify({ email, api_key: 'YOUR_KEY' })
  // });

  msg.textContent = '✅ Check your email in the next 5 minutes!';
  msg.style.color = '#90EE90';
  form.reset();

  console.log('New signup:', email);
  console.log('Total signups:', signups.length);
});

// Smooth scroll for nav links
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    e.preventDefault();
    const target = document.querySelector(a.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// Console welcome
console.log('%c AIForBiz ', 'background: #3498DB; color: white; font-size: 20px; padding: 8px;');
console.log('Landing page loaded. Edit prototypes/landing-page/* to customize.');
