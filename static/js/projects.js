document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('project-modal');
    const btnAbrir = document.getElementById('open-modal-btn');
    const btnFecharX = document.getElementById('close-modal-x');
    const btnFecharCancelar = document.getElementById('close-modal-btn');

    if (modalOverlay && btnAbrir) {
        function showModal() {
            modalOverlay.classList.add('active');
        }

        function hideModal() {
            modalOverlay.classList.remove('active');
        }

        btnAbrir.addEventListener('click', showModal);
        if (btnFecharX) btnFecharX.addEventListener('click', hideModal);
        if (btnFecharCancelar) btnFecharCancelar.addEventListener('click', hideModal);

        window.addEventListener('click', (evento) => {
            if (evento.target === modalOverlay) {
                hideModal();
            }
        });
    }

    const editModalOverlay = document.getElementById('project-edit-modal');
    const editBtnFecharX = document.getElementById('close-edit-modal-x');
    const editBtnFecharCancelar = document.getElementById('close-edit-modal-btn');

    if (editModalOverlay) {
        function hideEditModal() {
            editModalOverlay.classList.remove('active');
        }

        if (editBtnFecharX) editBtnFecharX.addEventListener('click', hideEditModal);
        if (editBtnFecharCancelar) editBtnFecharCancelar.addEventListener('click', hideEditModal);

        window.addEventListener('click', (evento) => {
            if (evento.target === editModalOverlay) {
                hideEditModal();
            }
        });
    }
});

function openEditProjectModal(id, name, description) {
    const editModal = document.getElementById('project-edit-modal');
    const idInput = document.getElementById('edit-project-id');
    const nameInput = document.getElementById('edit-projectName');
    const descInput = document.getElementById('edit-projectDescription');

    if (idInput) idInput.value = id;
    if (nameInput) nameInput.value = name;
    if (descInput) descInput.value = description;

    if (editModal) {
        editModal.classList.add('active');
    }
}

function confirmExclusion(projectId) {
    CustomConfirm(
        "Deseja realmente remover este projeto? Todas as tarefas vinculadas sumirão.",
        function () {
            document.getElementById('form-delete-' + projectId).submit();
        }
    );
}
