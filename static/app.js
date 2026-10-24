document.querySelectorAll('[data-print]').forEach(button=>button.addEventListener('click',()=>window.print()));
document.querySelectorAll('.sidebar nav a').forEach(a=>{if(location.pathname.startsWith(a.getAttribute('href')))a.classList.add('active')});
