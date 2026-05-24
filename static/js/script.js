function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('collapsed');
}

function toggleCheck(el) {
    el.classList.toggle('done');
    event.stopPropagation();
}

const now = new Date();
document.getElementById('pageDate').textContent = now.toLocaleDateString('pt-BR', {
    weekday: 'short', day: '2-digit', month: 'short', year: 'numeric'
});

const formPanel = document.getElementById('form-adicionar-tarefa');
const btnAbrir = document.getElementById('open-task-form-btn');
const btnCancelar = document.getElementById('close-task-form-btn');

btnAbrir.addEventListener('click', () => formPanel.removeAttribute('hidden'));
btnCancelar.addEventListener('click', () => formPanel.setAttribute('hidden', ''));