import '../css/main.css'
import Variable from './variable'
import Utils from './utils.js';

document.addEventListener("DOMContentLoaded", async () => {
    document.addEventListener('contextmenu', (event) => event.preventDefault());

    const authForm = document.getElementById("auth-form");
    const authButton = document.getElementById("auth-button");
    const toggleLink = document.getElementById("toggle-auth");
    const registerFields = document.getElementById("register-fields");
    const confirmPasswordField = document.getElementById("confirm-password-field");

    let isLoginMode = true;

    await checkAuth();

    async function checkAuth() {
        if (!Variable.getToken()) {
            Utils.redirectToAuth();
            return;
        }

        try {
            const response = await fetch(`${Variable.apiUrl}/auth/protected`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${Variable.getToken()}`,
                },
            });

            if (!response.ok) throw new Error("Invalid token");

            Utils.loadGamePage();
        } catch (err) {
            if (Variable.getRefreshToken()) {
                await refreshAccessToken();
            } else {
                Utils.redirectToAuth();
            }
        }
    }

    async function handleLogin(event) {
        event.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        if (!isLoginMode) {
            const username = document.getElementById("username").value;
            const confirmPassword = document.getElementById("confirm-password").value;

            if (password !== confirmPassword) {
                Utils.createToast('Пароли не совпадают.');
                return;
            }

            // Register user
            try {
                const response = await fetch(`${Variable.apiUrl}/auth/register`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({username, email, password}),
                });

                if (response.ok) {
                    Utils.createToast('Вы успешно зарегистрированы. Авторизуйтесь.')
                    isLoginMode = true;
                    toggleLink.click();
                } else {
                    const error = await response.json();
                    alert(error.detail);
                }
            } catch (error) {
                console.error(error);
                Utils.createToast('Произошла ошибка при регистрации.')
            }
        } else {
            try {
                const response = await fetch(`${Variable.apiUrl}/auth/login`, {
                    method: "POST",
                    headers: {"Content-Type": "application/x-www-form-urlencoded"},
                    body: new URLSearchParams({username: email, password}),
                });

                if (!response.ok) throw new Error("Login failed");

                const data = await response.json();

                localStorage.setItem("jwt", data.access_token);
                localStorage.setItem("refresh_token", data.refresh_token); // Save refresh token
                Utils.loadGamePage();
            } catch (err) {
                Utils.createToast("Не удалось войти. Проверьте свои данные." + err);
            }
        }
    }

    if (authForm) {
        authForm.addEventListener("submit", handleLogin);
        toggleLink.addEventListener("click", (e) => {
            e.preventDefault();
            isLoginMode = !isLoginMode;

            if (isLoginMode) {
                authButton.textContent = "Войти";
                toggleLink.textContent = "Нет учетной записи? Зарегистрироваться";
                registerFields.style.display = "none";
                confirmPasswordField.style.display = "none";
            } else {
                authButton.textContent = "Зарегистрироваться";
                toggleLink.textContent = "Уже есть учетная запись? Войти";
                registerFields.style.display = "block";
                confirmPasswordField.style.display = "block";
            }
        });
    }
});

export async function refreshAccessToken() {
    try {
        let refresh_token = Variable.getRefreshToken();
        const response = await fetch(`${Variable.apiUrl}/auth/refresh`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({refresh_token}),
        });

        if (!response.ok) throw new Error("Refresh token expired");

        const data = await response.json();
        Variable.setToken(data.access_token);
        localStorage.setItem("jwt", data.access_token); // Update access token
        Utils.loadGamePage();
    } catch (err) {
        Utils.createToast("Не удалось обновить токен.");
        Utils.redirectToAuth();
    }
}
