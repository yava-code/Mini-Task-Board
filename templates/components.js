const header = `
<header>
  <nav>
    <span class="logo">TaskBoard</span>
    <ul>
      <li><a href="index.html">Главная</a></li>
      <li><a href="about.html">Информация</a></li>
      <li><a href="contact.html">Связь</a></li>
    </ul>
  </nav>
</header>
`

const footer = `
<footer>
  <p>TaskBoard © 2025 — сделано с нуля</p>
</footer>
`

document.getElementById('header').innerHTML = header
document.getElementById('footer').innerHTML = footer