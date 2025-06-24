// Function to send email confirmation
async function enviarEmailConfirmacion(reserva_id, email, restaurant_id) {
    if (!reserva_id || !email || !restaurant_id) {
        console.error('[ERROR] Missing required parameters for email confirmation');
        return false;
    }

    const emailKey = `sent_email_${reserva_id}`;
    
    // Check if email was already sent successfully
    const emailStatus = window.sessionStorage.getItem(emailKey);
    if (emailStatus === 'sent') {
        console.log('[DEBUG] Email already sent successfully for this reservation');
        return true;
    }

    // Mark that we're attempting to send
    window.sessionStorage.setItem(emailKey, 'sending');

    try {
        displayBotResponse('Procesando envío de email de confirmación...');
        const response = await makeApiCall('/api/reservas/enviar-confirmacion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                reserva_id,
                email,
                restaurante_id: restaurant_id
            })
        });

        if (response.success) {
            // Mark this email as successfully sent
            window.sessionStorage.setItem(emailKey, 'sent');
            return true;
        } else {
            // Clear the sending status if failed
            window.sessionStorage.removeItem(emailKey);
            console.error('[ERROR] Failed to send confirmation email:', response);
            return false;
        }
    } catch (error) {
        // Clear the sending status if failed
        window.sessionStorage.removeItem(emailKey);
        console.error('[ERROR] Error al enviar email de confirmación:', error);
        return false;
    }
}
