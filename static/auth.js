// Shared login / registration JavaScript.
const form = document.getElementById('authForm');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const mode = form.dataset.mode;
  const body = {email:document.getElementById('email').value, password:document.getElementById('password').value};
  if (mode === 'register') body.name = document.getElementById('name').value;
  const output = document.getElementById('message');
  output.textContent = 'Please wait...';
  try {
    const response = await fetch(`/api/${mode}`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not continue');
    // Keep only local relative routes for the next page.
    const next = new URLSearchParams(location.search).get('next');
    location.href = next && next.startsWith('/') && !next.startsWith('//') ? next : '/';
  } catch (error) { output.textContent = error.message; }
});
