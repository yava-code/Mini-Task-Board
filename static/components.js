const header = `
<header>
  <nav>
    <span class="logo">TaskBoard</span>
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/info">About</a></li>
      <li><a href="/contact">Contact</a></li>
    </ul>
  </nav>
</header>
`

const footer = `
<footer>
  <p>TaskBoard © 2025</p>
</footer>
`

const h = document.getElementById('header')
const f = document.getElementById('footer')
if (h) h.innerHTML = header
if (f) f.innerHTML = footer
