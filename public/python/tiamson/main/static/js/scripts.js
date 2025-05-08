// main/static/js/scripts.js
document.addEventListener('DOMContentLoaded', () => {
    const loginModal = document.getElementById('loginModal');
    const signupModal = document.getElementById('signupModal');
    const closeButtons = document.querySelectorAll('.close');

    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            loginModal.style.display = 'none';
            signupModal.style.display = 'none';
        });
    });

    document.querySelectorAll('[data-toggle="modal"]').forEach(button => {
        button.addEventListener('click', event => {
            const targetModal = document.getElementById(event.target.dataset.target.slice(1));
            targetModal.style.display = 'block';
        });
    });
});
