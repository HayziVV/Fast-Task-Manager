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

document.addEventListener('DOMContentLoaded', function () {
    const userTrigger = document.getElementById('userMenuTrigger');
    const userDropdown = document.getElementById('userDropdown');

    if (userTrigger && userDropdown) {
        userTrigger.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
            userTrigger.classList.toggle('active');
        });

        document.addEventListener('click', function (e) {
            if (!userTrigger.contains(e.target) && !userDropdown.contains(e.target)) {
                userDropdown.classList.remove('show');
                userTrigger.classList.remove('active');
            }
        });
    }
});