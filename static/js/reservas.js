// ... existing code ...

document.addEventListener('DOMContentLoaded', function() {
    const reservaForm = document.getElementById('reserva-form');
    
    if (reservaForm) {
        reservaForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Obtener valores del formulario
            const nombre = document.getElementById('nombre').value;
            const email = document.getElementById('email').value;
            const telefono = document.getElementById('telefono').value;
            const fecha = document.getElementById('fecha').value;
            const hora = document.getElementById('hora').value;
            const personas = parseInt(document.getElementById('personas').value);
            const comentarios = document.getElementById('comentarios').value;
            
            // Validar fecha (no pasada)
            const fechaPartes = fecha.split('/');
            const fechaObj = new Date(fechaPartes[2], fechaPartes[1] - 1, fechaPartes[0]);
            const hoy = new Date();
            hoy.setHours(0, 0, 0, 0);
            
            if (fechaObj < hoy) {
                mostrarMensaje('No se pueden hacer reservas para fechas pasadas', 'error');
                return;
            }
            
            // Validar número de personas
            if (personas <= 0) {
                mostrarMensaje('El número de personas debe ser mayor a 0', 'error');
                return;
            }
            
            if (personas > 100) {
                mostrarMensaje('No podemos acomodar grupos de más de 100 personas en una sola reserva', 'error');
                return;
            }
            
            // Enviar datos al servidor
            try {
                const response = await fetch('/reservas', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        nombre,
                        email,
                        telefono,
                        fecha,
                        hora,
                        personas,
                        comentarios
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    mostrarMensaje(result.message, 'success');
                    reservaForm.reset();
                } else {
                    mostrarMensaje(result.message, 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                mostrarMensaje('Error al procesar la reserva. Por favor, intente nuevamente.', 'error');
            }
        });
    }
    
    // Función para mostrar mensajes
    function mostrarMensaje(mensaje, tipo) {
        const mensajeDiv = document.getElementById('mensaje');
        if (mensajeDiv) {
            mensajeDiv.textContent = mensaje;
            mensajeDiv.className = `mensaje ${tipo}`;
            mensajeDiv.style.display = 'block';
            
            // Ocultar mensaje después de 5 segundos
            setTimeout(() => {
                mensajeDiv.style.display = 'none';
            }, 5000);
        } else {
            alert(mensaje);
        }
    }
    
    // Definir la función cambiarEstado en el ámbito global para que sea accesible desde el HTML
    window.cambiarEstado = function(id, estado) {
        console.log(`Función cambiarEstado llamada: ID=${id}, Estado=${estado}`);
        
        if (confirm(`¿Estás seguro de que deseas cambiar el estado de la reserva a "${estado}"?`)) {
            fetch('/api/reservas/estado', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    id: id,
                    estado: estado
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Estado actualizado correctamente');
                    location.reload();
                } else {
                    alert('Error al actualizar el estado: ' + (data.error || 'Error desconocido'));
                    console.error('Error en respuesta:', data);
                }
            })
            .catch(error => {
                console.error('Error en fetch:', error);
                alert('Error al procesar la solicitud');
            });
        }
    };
    
    // Eliminar el código de event listeners que podría estar interfiriendo
    // con la función cambiarEstado definida en el HTML
});

// Función para editar una reserva
function editarReserva(id) {
    // Obtener los datos del formulario de edición
    const form = document.getElementById('form-editar-reserva');
    const formData = new FormData(form);
    
    // Convertir FormData a objeto JSON
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    // Asegurarse de que el ID esté incluido
    data.id = id;
    
    // Enviar solicitud al servidor
    fetch('/api/reservas/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Reserva actualizada correctamente');
            // Recargar la página para mostrar los cambios
            window.location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al procesar la solicitud');
    });
}

// Función para actualizar el estado de una reserva
function actualizarEstadoReserva(id, nuevoEstado) {
    // Mostrar mensaje de confirmación
    if (!confirm(`¿Estás seguro de cambiar el estado de la reserva a "${nuevoEstado}"?`)) {
        return; // El usuario canceló la acción
    }
    
    // Enviar solicitud al servidor
    fetch('/api/reservas/estado', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: id,
            estado: nuevoEstado
        }),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Estado de reserva actualizado correctamente');
            // Recargar la página para mostrar los cambios
            window.location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al procesar la solicitud: ' + error.message);
    });
}

// Agregar event listeners cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    // Event listener para el formulario de edición
    const formEditar = document.getElementById('form-editar-reserva');
    if (formEditar) {
        formEditar.addEventListener('submit', function(e) {
            e.preventDefault();
            const reservaId = this.getAttribute('data-id');
            editarReserva(reservaId);
        });
    }
    
    // Event listeners para los botones de editar
    const botonesEditar = document.querySelectorAll('.btn-editar');
    botonesEditar.forEach(boton => {
        boton.addEventListener('click', function() {
            const reservaId = this.getAttribute('data-id');
            // Aquí puedes cargar los datos de la reserva en el formulario
            cargarDatosReserva(reservaId);
        });
    });
});

// Función para cargar los datos de una reserva en el formulario
function cargarDatosReserva(id) {
    fetch(`/api/reservas/${id}`, {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const reserva = data.reserva;
            const form = document.getElementById('form-editar-reserva');
            
            // Establecer el ID de la reserva en el formulario
            form.setAttribute('data-id', reserva.id);
            
            // Llenar los campos del formulario con los datos de la reserva
            form.elements['nombre'].value = reserva.nombre || '';
            form.elements['email'].value = reserva.email || '';
            form.elements['telefono'].value = reserva.telefono || '';
            form.elements['fecha'].value = reserva.fecha || '';
            form.elements['hora'].value = reserva.hora || '';
            form.elements['comensales'].value = reserva.comensales || '';
            form.elements['comentarios'].value = reserva.comentarios || '';
            
            // Mostrar el modal de edición
            const modal = document.getElementById('modal-editar-reserva');
            modal.style.display = 'block';
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al cargar los datos de la reserva');
    });
}