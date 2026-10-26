// AIForBiz Landing — Apple-style smooth interactions
const form = document.getElementById('signup-form');
const msg = document.getElementById('form-msg');
const emailInput = document.getElementById('email');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = emailInput.value.trim();

  if (!email || !email.includes('@')) {
    msg.textContent = 'Please enter a valid email address.';
    msg.style.color = '#FF6B6B';
    return;
  }

  const btn = form.querySelector('button');
  btn.textContent = 'Sending...';
  btn.disabled = true;

  // Save locally (replace with ConvertKit/EmailOctopus in production)
  const signups = JSON.parse(localStorage.getItem('aiforbiz_signups') || '[]');
  signups.push({ email, timestamp: new Date().toISOString() });
  localStorage.setItem('aiforbiz_signups', JSON.stringify(signups));

  // Simulate network delay
  await new Promise(r => setTimeout(r, 800));

  msg.textContent = '✓ Check your email in the next 5 minutes!';
  msg.style.color = '#5AC8FA';
  form.reset();
  btn.innerHTML = 'Sent! <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>';
  btn.disabled = false;

  setTimeout(() => {
    btn.innerHTML = 'Send Me the Course Link <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14m-7-7l7 7-7 7"/></svg>';
    msg.textContent = '';
  }, 4000);

  console.log('New signup:', email, 'Total:', signups.length);
});

// Smooth scroll for nav (Safari fix)
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    const href = a.getAttribute('href');
    if (href === '#') return;
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});

// Intersection Observer — fade in elements on scroll
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in-view');
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -100px 0px' });

document.querySelectorAll('.section, .problem-card, .solution-card, .timeline-item, .testimonial-card, .price-card').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  observer.observe(el);
});

const style = document.createElement('style');
style.textContent = '.in-view { opacity: 1 !important; transform: translateY(0) !important; }';
document.head.appendChild(style);

// Console message
console.log('%c AIForBiz ', 'background: #0071E3; color: white; font-size: 24px; padding: 12px; border-radius: 8px; font-weight: bold;');
console.log('%cLanding page loaded. Edit /prototypes/landing-page/* to customize.', 'color: #86868B; font-size: 14px;');
