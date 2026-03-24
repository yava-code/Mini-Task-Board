import { createApp, ref, computed, onMounted } from 'vue'

const API = ''
const order = ['todo', 'doing', 'done']

createApp({
  template: document.getElementById('board-template').innerHTML,
  setup() {
    const tasks = ref([])
    const draft = ref('')

    const columns = [
      { id: 'todo', title: 'To Do', canAdd: true },
      { id: 'doing', title: 'In Progress', canAdd: false },
      { id: 'done', title: 'Done', canAdd: false },
    ]

    const grouped = computed(() => {
      const o = { todo: [], doing: [], done: [] }
      for (const t of tasks.value) {
        if (o[t.status]) o[t.status].push(t)
      }
      return o
    })

    function nextStatus(st) {
      const i = order.indexOf(st)
      if (i < 0 || i >= order.length - 1) return null
      return order[i + 1]
    }

    async function load() {
      const res = await fetch(`${API}/tasks`, { credentials: 'include' })
      if (!res.ok) return
      tasks.value = await res.json()
    }

    async function addTask() {
      const title = draft.value.trim()
      if (!title) return
      await fetch(`${API}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title, status: 'todo' }),
      })
      draft.value = ''
      await load()
    }

    async function rename(t) {
      const next = prompt('New title:', t.title)
      if (next === null) return
      const title = next.trim()
      if (!title || title === t.title) return
      await fetch(`${API}/tasks/${t.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title }),
      })
      await load()
    }

    async function move(t, newStatus) {
      await fetch(`${API}/tasks/${t.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status: newStatus }),
      })
      await load()
    }

    async function remove(t) {
      if (!confirm('Delete this task?')) return
      await fetch(`${API}/tasks/${t.id}`, {
        method: 'DELETE',
        credentials: 'include',
      })
      await load()
    }

    onMounted(load)

    return {
      columns,
      grouped,
      draft,
      nextStatus,
      addTask,
      rename,
      move,
      remove,
    }
  },
}).mount('#board-app')
