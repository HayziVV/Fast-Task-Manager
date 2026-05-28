const addModal = document.getElementById('modal-add-task');
const manageModal = document.getElementById('modal-manage-task');

document.getElementById('open-add-task-btn').addEventListener('click', () => {
    addModal.classList.add('active');
});

function openManageModal(id, name, status) {
    document.getElementById('manage-task-id').value = id;
    document.getElementById('manage-task-name').value = name;
    document.getElementById('manage-task-status').value = status;
    document.getElementById('clear-note-task-id').value = id;
    document.getElementById('clear-task-id').value = id;

    manageModal.classList.add('active');
}


document.getElementById('close-add-x').addEventListener('click', () => addModal.classList.remove('active'));
document.getElementById('close-add-btn').addEventListener('click', () => addModal.classList.remove('active'));


document.getElementById('close-manage-x').addEventListener('click', () => manageModal.classList.remove('active'));
document.getElementById('close-manage-btn').addEventListener('click', () => manageModal.classList.remove('active'));


window.addEventListener('click', (e) => {
    if (e.target === addModal) addModal.classList.remove('active');
    if (e.target === manageModal) manageModal.classList.remove('active');
});

document.getElementById('clear-note-trigger').addEventListener('click', () => {
    if (confirm("Tem certeza de que deseja apagar permanentemente todas as anotações desta tarefa?")) {
        document.getElementById('form-delete-note').submit();
    }
});

document.getElementById('clear-task-trigger').addEventListener('click', () => {
    if (confirm("Tem certeza de que deseja apagar permanentemente a tarefa?")) {
        document.getElementById('form-delete-task').submit();
    }
});
