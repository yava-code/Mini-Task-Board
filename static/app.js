const API = ''

const order = ['todo', 'doing', 'done']

function esc(s) {
  const d = document.createElement('div')
  d.textContent = s
  return d.innerHTML
}

async function loadTasks() {
  const res = await fetch(`${API}/tasks`, { credentials: 'include' })
  if (!res.ok) return
  const tasks = await res.json()

  document.querySelectorAll('.cards').forEach((c) => {
    c.innerHTML = ''
  })

  tasks.forEach((t) => renderCard(t))
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
    <span class="title">${esc(task.title)}</span>
    <button type="button" class="rename-btn" title="Rename">✎</button>
    ${nextStatus ? `<button type="button" class="move-btn" data-move>→</button>` : ''}
    <button type="button" data-del>✕</button>
  `

  card.querySelector('.rename-btn').addEventListener('click', () => {
    const next = prompt('New title:', task.title)
    if (next === null) return
    const t = next.trim()
    if (!t || t === task.title) return
    renameTask(task.id, t)
  })

  const moveBtn = card.querySelector('[data-move]')
  if (moveBtn) {
    moveBtn.addEventListener('click', () => moveTask(task.id, nextStatus))
  }
  const delBtn = card.querySelector('[data-del]')
  if (delBtn) {
    delBtn.addEventListener('click', () => {
      if (confirm('Delete this task?')) {
        deleteTask(task.id)
      }
    })
  }

  col.appendChild(card)
}

async function addTask(colId) {
  const input = document.querySelector(`#${colId} input`)
  const title = input.value.trim()
  if (!title) return

  await fetch(`${API}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ title, status: colId }),
  })

  input.value = ''
  loadTasks()
}

async function renameTask(id, title) {
  await fetch(`${API}/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ title }),
  })
  loadTasks()
}

async function moveTask(id, newStatus) {
  await fetch(`${API}/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ status: newStatus }),
  })
  loadTasks()
}

async function deleteTask(id) {
  await fetch(`${API}/tasks/${id}`, { method: 'DELETE', credentials: 'include' })
  loadTasks()
}

loadTasks()
