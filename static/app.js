const API = ''

const order = ['todo', 'doing', 'done']

function esc(s) {
  const d = document.createElement('div')
  d.textContent = s
  return d.innerHTML
}

<<<<<<< HEAD
async function loadTasks() {
  const res = await fetch(`${API}/tasks`, { credentials: 'include' })
  if (!res.ok) return
=======
async function checkAuth() {
  const res = await fetch(`${API}/auth/me`, { credentials: 'include' })
  const authPanel = document.getElementById('auth-panel')
  const userBar = document.getElementById('user-bar')
  const boardWrap = document.getElementById('board-wrap')
  const emailSpan = document.getElementById('user-email')

  if (res.ok) {
    const data = await res.json()
    if (authPanel) authPanel.style.display = 'none'
    if (userBar) userBar.style.display = 'flex'
    if (boardWrap) boardWrap.style.display = 'block'
    if (emailSpan) emailSpan.textContent = data.email
    loadTasks()
  } else {
    if (authPanel) authPanel.style.display = 'flex'
    if (userBar) userBar.style.display = 'none'
    if (boardWrap) boardWrap.style.display = 'none'
  }
}

async function register() {
  const email = document.getElementById('email').value.trim()
  const password = document.getElementById('password').value
  const res = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  })
  if (res.ok) {
    checkAuth()
    return
  }
  const j = await res.json().catch(() => ({}))
  alert(j.error || 'register failed')
}

async function login() {
  const email = document.getElementById('email').value.trim()
  const password = document.getElementById('password').value
  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  })
  if (res.ok) {
    checkAuth()
    return
  }
  const j = await res.json().catch(() => ({}))
  alert(j.error || 'login failed')
}

async function logout() {
  await fetch(`${API}/auth/logout`, { method: 'POST', credentials: 'include' })
  checkAuth()
}

async function loadTasks() {
  const res = await fetch(`${API}/tasks`, { credentials: 'include' })
  if (!res.ok) return

>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
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
    <span>${esc(task.title)}</span>
<<<<<<< HEAD
    ${nextStatus ? `<button type="button" class="move-btn" data-move>→</button>` : ''}
    <button type="button" data-del>✕</button>
=======
    ${nextStatus ? `<button type="button" class="move-btn" data-move data-id="${task.id}" data-next="${nextStatus}">→</button>` : ''}
    <button type="button" data-del data-id="${task.id}">✕</button>
>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
  `

  const moveBtn = card.querySelector('[data-move]')
  if (moveBtn) {
    moveBtn.addEventListener('click', () => moveTask(task.id, nextStatus))
  }
  const delBtn = card.querySelector('[data-del]')
  if (delBtn) {
    delBtn.addEventListener('click', () => deleteTask(task.id))
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

<<<<<<< HEAD
loadTasks()
=======
checkAuth()
>>>>>>> b4c50dfdc5fd813fc94ac55865b3fe473fef2dd4
