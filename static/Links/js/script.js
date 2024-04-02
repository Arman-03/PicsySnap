const userAuth = document.querySelector('.user-auth');
const loginLink = document.querySelector('.login-link');
const registerLink = document.querySelector('.register-link');
const btnPop = document.querySelector('.login-btn');
const iconClose = document.querySelector('.icon-close');

registerLink.addEventListener('click', () => {
  userAuth.classList.add('register');
});

loginLink.addEventListener('click', () => {
    userAuth.classList.remove('register');
});

btnPop.addEventListener('click', () => {
    userAuth.classList.add('register-btn');
});

iconClose.addEventListener('click', () => {
    userAuth.classList.remove('register-btn');
});