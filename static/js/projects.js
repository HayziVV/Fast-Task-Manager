document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('project-modal');
    const btnAbrir = document.getElementById('open-modal-btn');
    const btnFecharX = document.getElementById('close-modal-x');
    const btnFecharCancelar = document.getElementById('close-modal-btn');

    if (!modalOverlay || !btnAbrir) return;

    function showModal() {
        modalOverlay.classList.add('active');
    }

    function hideModal() {
        modalOverlay.classList.remove('active');
    }

    btnAbrir.addEventListener('click', showModal);
    btnFecharX.addEventListener('click', hideModal);
    btnFecharCancelar.addEventListener('click', hideModal);

    window.addEventListener('click', (evento) => {
        if (evento.target === modalOverlay) {
            hideModal();
        }
    });
});

function confirmExclusion(projectId) {
    CustomConfirm(
        "Deseja realmente remover este projeto? Todas as tarefas vinculadas sumirão.",
        function () {
            document.getElementById('form-delete-' + projectId).submit();
        }
    );
}