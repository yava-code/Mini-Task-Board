import { createApp, ref, computed, onMounted } from 'vue'

const API = ''
const order = ['todo', 'doing', 'done']
const mountEl = document.getElementById('board-app')
const csrfToken = mountEl?.dataset?.csrfToken || ''

createApp({
  template: document.getElementById('board-template').innerHTML,
  setup() {
    const tasks = ref([])
    const draft = ref('')
    const editDraft = ref('')
    const editId = ref(null)
    const loading = ref(false)
    const busy = ref(false)
    const msg = ref('')
    const msgType = ref('info')

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

    function setMsg(text, type = 'info') {
      msg.value = text
      msgType.value = type
    }

    async function readErr(res) {
      try {
        const body = await res.json()
        if (body?.error) return body.error
      } catch (_) {}
      return `request failed (${res.status})`
    }

    async function send(url, opts = {}) {
      const headers = { ...(opts.headers || {}) }
      const method = (opts.method || 'GET').toUpperCase()
      if (method !== 'GET') {
        headers['X-CSRF-Token'] = csrfToken
      }
      const res = await fetch(url, { ...opts, headers })
      if (!res.ok) {
        throw new Error(await readErr(res))
      }
      return res
    }

    async function load() {
      loading.value = true
      try {
        const res = await send(`${API}/tasks`, { credentials: 'include' })
        tasks.value = await res.json()
      } catch (err) {
        setMsg(err.message || 'failed to load tasks', 'err')
      } finally {
        loading.value = false
      }
    }

    async function addTask() {
      const title = draft.value.trim()
      if (!title || busy.value) return
      busy.value = true
      try {
        await send(`${API}/tasks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ title }),
        })
        draft.value = ''
        setMsg('')
        await load()
      } catch (err) {
        setMsg(err.message || 'failed to add task', 'err')
      } finally {
        busy.value = false
      }
    }

    function startRename(t) {
      editId.value = t.id
      editDraft.value = t.title
    }

    function cancelRename() {
      editId.value = null
      editDraft.value = ''
    }

    async function saveRename(t) {
      const title = editDraft.value.trim()
      if (!title || busy.value) return
      if (title === t.title) {
        cancelRename()
        return
      }
      busy.value = true
      try {
        await send(`${API}/tasks/${t.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ title }),
        })
        cancelRename()
        setMsg('')
        await load()
      } catch (err) {
        setMsg(err.message || 'failed to rename task', 'err')
      } finally {
        busy.value = false
      }
    }

    async function move(t, newStatus) {
      if (busy.value) return
      busy.value = true
      try {
        await send(`${API}/tasks/${t.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ status: newStatus }),
        })
        setMsg('')
        await load()
      } catch (err) {
        setMsg(err.message || 'failed to move task', 'err')
      } finally {
        busy.value = false
      }
    }

    async function remove(t) {
      if (busy.value || !confirm('Delete this task?')) return
      busy.value = true
      try {
        await send(`${API}/tasks/${t.id}`, {
          method: 'DELETE',
          credentials: 'include',
        })
        setMsg('')
        await load()
      } catch (err) {
        setMsg(err.message || 'failed to delete task', 'err')
      } finally {
        busy.value = false
      }
    }

    onMounted(load)

    return {
      columns,
      grouped,
      draft,
      editDraft,
      editId,
      loading,
      busy,
      msg,
      msgType,
      nextStatus,
      addTask,
      startRename,
      saveRename,
      cancelRename,
      move,
      remove,
    }
  },
}).mount('#board-app')
