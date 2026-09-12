const form = document.querySelector('#profile');
const nameInput = document.querySelector('#name');
const status = document.querySelector('#status');

form.addEventListener('submit', async event => {
  event.preventDefault();
  try {
    const response = await fetch('/api/profile', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({displayName: nameInput.value}),
    });
    const result = await response.json();
    status.textContent = response.ok ? 'Saved' : result.error;
  } catch {
    status.textContent = 'Save outcome unknown. Reload to check the stored name.';
  }
});
document.querySelector('#cancel').addEventListener('click', () => {
  status.textContent = 'Cancelled';
});

async function load() {
  try {
    const response = await fetch('/api/profile');
    if (!response.ok) throw new Error('Load failed');
    nameInput.value = (await response.json()).displayName;
    for (const element of form.elements) element.disabled = false;
    status.textContent = 'Ready';
  } catch {
    status.textContent = 'Could not load the profile. Reload to retry.';
  }
}
load();
