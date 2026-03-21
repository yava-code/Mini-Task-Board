const API = 'http://localhost:5000'

const order = ['todo', 'doing', 'done']

async function loadTasks() {
  const res = await fetch(`${API}/tasks`)
  const tasks = await res.json()

  // чистим колонки
  document.querySelectorAll('.cards').forEach(c => c.innerHTML = '')

  tasks.forEach(t => renderCard(t))
}

function renderCard(task) {
  const col = document.querySelector(`#${task.status} .cards`)
  if (!col) return

  const card = document.createElement('div')
  card.className = 'card'
  card.dataset.id = task.id

  const idx = order.indexOf(task.status)
  const nextStatus = order[idx + 1] || null

  card.innerHTML = `
    <span>${task.title}</span>
    ${nextStatus ? `<button class="move-btn" onclick="moveTask(${task.id}, '${nextStatus}')">→</button>` : ''}
    <button onclick="deleteTask(${task.id})">✕</button>
  `

  col.appendChild(card)
}

async function addTask(colId) {
  const input = document.querySelector(`#${colId} input`)
  const title = input.value.trim()
  if (!title) return

  await fetch(`${API}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, status: colId })
  })

  input.value = ''
  loadTasks()
}

async function moveTask(id, newStatus) {
  await fetch(`${API}/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: newStatus })
  })
  loadTasks()
}

async function deleteTask(id) {
  await fetch(`${API}/tasks/${id}`, { method: 'DELETE' })
  loadTasks()
}

loadTasks()