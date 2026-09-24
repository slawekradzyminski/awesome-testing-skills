const el = id => document.getElementById(id);
const headers = {'Content-Type': 'application/json', 'X-Test-User': 'alice'};
let selected = 'A100';
let generation = 0;
async function readOrder(id) {
  const token = ++generation;
  selected = id;
  el('loading').textContent = 'Loading order…';
  ['save', 'express', 'standard'].forEach(id => el(id).disabled = true);
  el('feedback').textContent = '';
  const response = await fetch('/api/orders/' + id, {headers});
  const row = await response.json();
  if (token !== generation) return;
  if (!response.ok) { el('loading').textContent = row.error; return; }
  el('heading').textContent = 'Order ' + row.id;
  el('address').textContent = row.address;
  el('note').value = row.note;
  el('service').textContent = row.service;
  el('loading').textContent = '';
  ['save', 'express', 'standard'].forEach(id => el(id).disabled = false);
}
el('order').addEventListener('change', event => readOrder(event.target.value));
el('save').addEventListener('click', async () => {
  const id = selected;
  el('save').disabled = true;
  const response = await fetch('/api/orders/' + id + '/note', {
    method: 'POST', headers, body: JSON.stringify({note: el('note').value})});
  const row = await response.json();
  if (id !== selected) return;
  if (!response.ok) {
    el('feedback').textContent = row.error;
    el('save').disabled = false;
    return;
  }
  el('feedback').textContent = 'Delivery instruction saved';
  el('save').disabled = false;
});
async function setService(service) {
  const id = selected;
  const response = await fetch('/api/services', {method: 'POST', headers,
    body: JSON.stringify({ids: [id], service})});
  const body = await response.json();
  if (id !== selected) return;
  el('feedback').textContent = response.ok ? 'Delivery service saved' : body.error;
  if (response.ok) el('service').textContent = service;
}
el('express').addEventListener('click', () => setService('express'));
el('standard').addEventListener('click', () => setService('standard'));
readOrder(selected);
