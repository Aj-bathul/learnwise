

document.addEventListener('DOMContentLoaded', function() {


    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const email = document.getElementById('email');
            const password = document.getElementById('password');

            let errorMessages = [];

            if (!email || !email.value.trim()) {
                errorMessages.push('Email is required');
            } else if (!isValidEmail(email.value)) {
                errorMessages.push('Please enter a valid email address');
            }

            if (!password || !password.value) {
                errorMessages.push('Password is required');
            }

            if (errorMessages.length > 0) {
                e.preventDefault();
                alert('⚠️ Error:\n\n' + errorMessages.join('\n'));
                return;
            }

            // If valid, form submits normally
        });
    }


    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const fullName = document.getElementById('full_name');
            const email = document.getElementById('email');
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');

            let errorMessages = [];

            if (!fullName || !fullName.value.trim()) {
                errorMessages.push('Full name is required');
            }

            if (!email || !email.value.trim()) {
                errorMessages.push('Email is required');
            } else if (!isValidEmail(email.value)) {
                errorMessages.push('Please enter a valid email address');
            }

            if (!password || !password.value) {
                errorMessages.push('Password is required');
            } else if (password.value.length < 8) {
                errorMessages.push('Password must be at least 8 characters');
            } else if (!/[A-Z]/.test(password.value)) {
                errorMessages.push('Password must contain at least one uppercase letter');
            } else if (!/[a-z]/.test(password.value)) {
                errorMessages.push('Password must contain at least one lowercase letter');
            } else if (!/[0-9]/.test(password.value)) {
                errorMessages.push('Password must contain at least one number');
            }

            if (password && confirmPassword && password.value !== confirmPassword.value) {
                errorMessages.push('Passwords do not match');
            }

            if (errorMessages.length > 0) {
                e.preventDefault();
                alert('⚠️ Error:\n\n' + errorMessages.join('\n'));
                return;
            }
        });
    }



    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

});