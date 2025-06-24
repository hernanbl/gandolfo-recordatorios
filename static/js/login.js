document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Evitar el envío tradicional del formulario
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            console.log("Intentando login con email:", email);
            
            // Realizar la solicitud POST a la API
            fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    email: email,
                    password: password 
                }),
                credentials: 'same-origin' // Importante para las cookies de sesión
            })
            .then(response => {
                console.log("Status code:", response.status);
                
                // Clone the response so we can log it for debugging
                const responseClone = response.clone();
                responseClone.text().then(text => {
                    try {
                        const data = JSON.parse(text);
                        console.log("Response body:", data);
                    } catch (e) {
                        console.log("Raw response:", text);
                    }
                });
                
                return response.json().then(data => {
                    if (!response.ok) {
                        console.error("Error details:", data);
                        throw new Error(data.error || 'Error en la autenticación');
                    }
                    return data;
                });
            })
            .then(data => {
                console.log("Login successful:", data);
                if (data.success) {
                    // Redirigir a la página de reservas
                    console.log("Redirecting to /reservas");
                    window.location.href = '/reservas';
                } else {
                    alert('Error de autenticación. Por favor, intenta nuevamente.');
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                alert('Error: ' + error.message);
            });
        });
    } else {
        console.error("No se encontró el formulario de login");
    }
});