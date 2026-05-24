document.addEventListener('DOMContentLoaded', () => {

    const registerForm = document.querySelector('.sign-up-container form');

    registerForm.addEventListener('submit', (event) => {

        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

        let errorContainer = registerForm.querySelector('.error-alert');

        // Password too short
        if (password.length < 6) {
            event.preventDefault();

            if (!errorContainer) {
                errorContainer = document.createElement('div');
                errorContainer.className = 'error-alert';
                const submitBtn = registerForm.querySelector('button');
                registerForm.insertBefore(errorContainer, submitBtn);
            }
            errorContainer.textContent = 'A senha deve conter pelo menos 6 caracteres.';
            return;
        }

        // Passwords doesn't match
        if (password !== confirmPassword) {
            event.preventDefault();

            if (!errorContainer) {
                errorContainer = document.createElement('div');
                errorContainer.className = 'error-alert';
                const submitBtn = registerForm.querySelector('button');
                registerForm.insertBefore(errorContainer, submitBtn);
            }
            errorContainer.textContent = 'As senhas digitadas não coincidem.';
            return;
        }
    });
});