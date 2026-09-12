const identity = document.querySelector('#identity');
const form = document.querySelector('#quantity-form');
const quantity = document.querySelector('#quantity');
const summary = document.querySelector('#summary');
const feedback = document.querySelector('#feedback');
let current;

const headers = () => ({Authorization: `Bearer demo-${identity.value}`, 'Content-Type': 'application/json'});

async function refresh() {
  const response = await fetch('/api/v1/cart', {headers: headers()});
  current = await response.json();
  summary.textContent = `Quantity: ${current.totalItems} · Total: ${current.totalPrice}`;
}

document.querySelector('#edit').addEventListener('click', () => {
  quantity.value = current.items[0]?.quantity ?? 0;
  form.hidden = false;
  feedback.textContent = '';
  quantity.focus();
});

document.querySelector('#cancel').addEventListener('click', () => {
  form.hidden = true;
  feedback.textContent = 'Edit cancelled';
  document.querySelector('#edit').focus();
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  const response = await fetch('/api/v1/cart/items/1', {
    method: 'PUT', headers: headers(), body: JSON.stringify({quantity: Number(quantity.value)}),
  });
  if (response.ok) {
    await refresh();
    form.hidden = true;
    feedback.textContent = 'Cart updated';
  } else {
    const body = await response.json();
    feedback.textContent = body.error;
  }
});

identity.addEventListener('change', async () => {
  form.hidden = true;
  feedback.textContent = '';
  await refresh();
});

refresh();
