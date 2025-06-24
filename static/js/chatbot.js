// Global variables for Chatbot
window.chatbotState = {
    datosReservaVacio: {
        nombre: '',
        fecha: '',
        hora: '',
        personas: '',
        telefono: '',
        email: '',
        comentarios: ''
    },
    restaurantInfo: null,
    menuInfo: null,
    openingHours: null,
    chatbotInitializedSuccessfully: false,
    saludoInicialRealizado: false,
    reservaEnProceso: false,
    datosReserva: null,
    pasoActual: '',
    primerNombre: ''
};

// Initialize chatbot state
window.chatbotState.datosReserva = { ...window.chatbotState.datosReservaVacio };

// ADDED: Function to remove the typing indicator
function removeTypingIndicator(typingIndicator) {
    console.log('[CHATBOT_DEBUG] removeTypingIndicator CALLED. Indicator received:', typingIndicator ? typingIndicator.id : typingIndicator); // DEBUG
    if (typingIndicator && typingIndicator.parentNode) {
        try {
            typingIndicator.parentNode.removeChild(typingIndicator);
            console.log('[CHATBOT_INFO] Typing indicator REMOVED successfully. ID:', typingIndicator.id); // INFO
        } catch (e) {
            console.error('[CHATBOT_ERROR] removeTypingIndicator: Error during removeChild:', e, 'Indicator ID:', typingIndicator.id, 'Parent:', typingIndicator.parentNode); // ERROR
        }
    } else {
        if (!typingIndicator) {
            console.warn('[CHATBOT_WARN] removeTypingIndicator: typingIndicator argument is NULL or UNDEFINED. Cannot remove.'); // WARN
        } else if (!typingIndicator.parentNode) {
            console.warn('[CHATBOT_WARN] removeTypingIndicator: typingIndicator (ID: ' + typingIndicator.id + ') has NO parentNode. It might have been already removed or never attached properly.'); // WARN
        }
    }
}

// Function to add a typing indicator
function addTypingIndicator(chatMessagesElement) {
    console.log('[CHATBOT_DEBUG] addTypingIndicator CALLED for chatMessagesElement:', chatMessagesElement); // DEBUG
    if (!chatMessagesElement) {
        console.error('[CHATBOT_ERROR] addTypingIndicator: chatMessagesElement is NULL or UNDEFINED. Cannot add indicator.'); // ERROR
        return null;
    }
    if (typeof chatMessagesElement.appendChild !== 'function') {
        console.error('[CHATBOT_ERROR] addTypingIndicator: chatMessagesElement is not a valid DOM element with appendChild method.', chatMessagesElement); // ERROR
        return null;
    }
    const typingIndicatorDiv = document.createElement('div');
    typingIndicatorDiv.id = 'typing-indicator-' + Date.now(); 
    typingIndicatorDiv.className = 'bot-message typing-indicator-container'; 
    typingIndicatorDiv.innerHTML = `
        <div style="display: flex; align-items: center; padding: 0.75rem; background-color: #f0f0f0; border-radius: 0.5rem; border-top-left-radius: 0; max-width: fit-content; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
            <span style="margin-left: 8px; font-size: 0.85em; color: #555;">El asistente está escribiendo...</span>
        </div>
    `;
    try {
        chatMessagesElement.appendChild(typingIndicatorDiv);
        chatMessagesElement.scrollTop = chatMessagesElement.scrollHeight;
        console.log('[CHATBOT_INFO] addTypingIndicator: Typing indicator DIV APPENDED successfully. Element ID:', typingIndicatorDiv.id); // INFO
        return typingIndicatorDiv; 
    } catch (e) {
        console.error('[CHATBOT_ERROR] addTypingIndicator: Error APPENDING typing indicator to chatMessagesElement:', e, 'chatMessagesElement:', chatMessagesElement); // ERROR
        return null; 
    }
}


// Helper function to parse date strings (including "hoy", "mañana", "DD de MMMM")
function parsearFechaInput(textoFecha) {
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0); // Normalize to start of day

    const manana = new Date(hoy);
    manana.setDate(hoy.getDate() + 1);

    // Normalize input text
    textoFecha = textoFecha.toLowerCase().trim();
    console.log('[DEBUG] parsearFechaInput input:', textoFecha);

    // Handle special cases
    if (textoFecha === "hoy") {
        console.log('[DEBUG] parsearFechaInput - using today:', hoy.toISOString().split('T')[0]);
        return hoy.toISOString().split('T')[0];
    }
    if (textoFecha === "mañana") {
        console.log('[DEBUG] parsearFechaInput - using tomorrow:', manana.toISOString().split('T')[0]);
        return manana.toISOString().split('T')[0];
    }

    // Try parsing "DD de MMMM" (e.g., "15 de mayo")
    const meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
    const matchMes = textoFecha.match(/(\d{1,2})\s+de\s+([a-záéíóúñ]+)/i);
    if (matchMes) {
        const dia = parseInt(matchMes[1], 10);
        const nombreMes = matchMes[2].toLowerCase();
        const mesIndex = meses.findIndex(m => m.startsWith(nombreMes));
        if (mesIndex !== -1 && dia > 0 && dia <= 31) {
            const fechaIntentada = new Date(hoy.getFullYear(), mesIndex, dia);
            if (fechaIntentada >= hoy) { // Only allow today or future dates
                return fechaIntentada.toISOString().split('T')[0];
            } else { // If date is in the past for the current year, assume next year
                const fechaProximoAnio = new Date(hoy.getFullYear() + 1, mesIndex, dia);
                return fechaProximoAnio.toISOString().split('T')[0];
            }
        }
    }

    // Try parsing "DD/MM" or "DD/MM/YYYY"
    const matchBarra = textoFecha.match(/(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?/);
    if (matchBarra) {
        const dia = parseInt(matchBarra[1], 10);
        const mes = parseInt(matchBarra[2], 10) - 1; // Month is 0-indexed
        let anio = matchBarra[3] ? parseInt(matchBarra[3], 10) : hoy.getFullYear();
        if (matchBarra[3] && matchBarra[3].length === 2) { // Handle YY format
            anio = 2000 + anio; // Assume 20xx
        }

        if (dia > 0 && dia <= 31 && mes >= 0 && mes <= 11) {
            const fechaIntentada = new Date(anio, mes, dia);
            if (fechaIntentada.getFullYear() === anio && fechaIntentada.getMonth() === mes && fechaIntentada.getDate() === dia) { // Check if date is valid
                if (fechaIntentada >= hoy) {
                    return fechaIntentada.toISOString().split('T')[0];
                } else if (anio === hoy.getFullYear() && !matchBarra[3]) { // If no year specified and date is in past, assume next year
                    const fechaProximoAnio = new Date(hoy.getFullYear() + 1, mes, dia);
                    if (fechaProximoAnio.getMonth() === mes && fechaProximoAnio.getDate() === dia) {
                        return fechaProximoAnio.toISOString().split('T')[0]; // Corrected this line
                    }
                }
            }
        }
    }
    
    // Try parsing YYYY-MM-DD
    const matchISO = textoFecha.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (matchISO) {
        const anio = parseInt(matchISO[1], 10);
        const mes = parseInt(matchISO[2], 10) - 1;
        const dia = parseInt(matchISO[3], 10);
        const fechaIntentada = new Date(anio, mes, dia);
        if (fechaIntentada.getFullYear() === anio && fechaIntentada.getMonth() === mes && fechaIntentada.getDate() === dia && fechaIntentada >= hoy) {
            return textoFecha; // Already in correct format
        }
    }

    return null; // Could not parse
}

// Función para validar y formatear fechas
function validarYFormatearFecha(fechaStr) {
    try {
        // Si ya está en formato YYYY-MM-DD
        if (fechaStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
            const [year, month, day] = fechaStr.split('-').map(Number);
            if (validarComponentesFecha(year, month, day)) {
                return fechaStr; // Ya está en el formato correcto
            }
            throw new Error('Fecha inválida');
        }
        
        window.chatbotState.restaurantInfo = {
            restaurantId: window.chatbotConfig.restaurantId || '',
            restaurantName: window.chatbotConfig.restaurantName || 'Restaurante',
            address: window.chatbotConfig.address || '',
            contactPhone: window.chatbotConfig.contactPhone || '',
            contactWhatsapp: window.chatbotConfig.contactWhatsapp || '',
            openingHours: window.chatbotConfig.openingHours || {}
        };
        window.chatbotState.menuInfo = window.chatbotConfig.menuData || {};
        window.chatbotState.openingHours = window.chatbotConfig.openingHours || {
            lunes: { open: "12:00", close: "23:00" },
            martes: { open: "12:00", close: "23:00" },
            miercoles: { open: "12:00", close: "23:00" },
            jueves: { open: "12:00", close: "23:00" },
            viernes: { open: "12:00", close: "23:00" },
            sabado: { open: "12:00", close: "23:00" },
            domingo: { open: "12:00", close: "23:00" }
        };
        window.chatbotState.reservaEnProceso = false;
        window.chatbotState.datosReserva = { ...window.chatbotState.datosReservaVacio };
        window.chatbotState.pasoActual = '';
        window.chatbotState.primerNombre = '';
        window.chatbotState.chatbotInitializedSuccessfully = true;
        window.chatbotState.saludoInicialRealizado = false;
        console.log('[CHATBOT_DEBUG] Información del restaurante inicializada:', window.chatbotState.restaurantInfo);
        console.log('[CHATBOT_DEBUG] Información del menú inicializada:', window.chatbotState.menuInfo);
        console.log('[CHATBOT_DEBUG] Horarios inicializados:', window.chatbotState.openingHours);
        return true;
    } catch (error) {
        console.error('[CHATBOT_ERROR] Error al inicializar datos:', error);
        return false;
    }
}

// Helper function to convert the new opening hours format to the old format
function convertOpeningHours(dayConfig) {
    if (!dayConfig) {
        return { open: "12:00", close: "23:00", is_closed: true };
    }
    
    if (dayConfig.is_closed) {
        return { is_closed: true };
    }
    
    // Get the first slot if available, otherwise use default hours
    const slot = dayConfig.slots?.[0] || { open: "12:00", close: "23:00" };
    return {
        open: slot.open,
        close: slot.close,
        is_closed: false,
        nota: dayConfig.note
    };
}

// Palabras clave para verificar relevancia de preguntas
const palabrasClave = ['hola','y el de mañana','el de mañana','cómo llego','como llego','listo gracias','hello','gracias','listo, chau','chau','vegetariano','vegetarianas','cómo va?','cómo va','que acelga','buenas','hay alguien','buen','que tal','como va?','Hola?','menu', 'menú', 'comida', 'plato', 'restaurante', 'gandolfo', 'reserva', 
                      'horario', 'ubicación', 'ubicados', 'dirección', 'donde', 'dónde', 'lugar', 'precio', 'costo', 'vegetariano', 
                      'vegano', 'sin gluten', 'tacc', 'estacionamiento', 'parking', 'delivery','tartas','empanadas', 'facturas','tortas','eventos','fideos','omelets','parrilla','sushi','hamburguesas',
                      'pedido', 'llevar', 'bebida', 'vino', 'no gracia', 'No gracias', 'cerveza', 'postre', 'mesa', 
                      'evento', 'cumpleaños', 'celebración', 'pago', 'MercadoPago', 'tarjeta', 'efectivo',
                      'wifi', 'baño', 'accesibilidad', 'promoción', 'descuento', 'especial', 'día', 'hoy'];

// Función para verificar si un mensaje es relevante para el contexto del restaurante
function esConsultaRelevante(mensaje) {
    return palabrasClave.some(palabra => 
        mensaje.toLowerCase().includes(palabra)
    );
}

// Función para obtener el menú del día
function getMenuDelDia(dia = null, turno = null) {
    console.log(`[getMenuDelDia] Solicitado: dia='${dia}', turno='${turno}'`);

    if (!window.chatbotState.menuInfo || (typeof window.chatbotState.menuInfo === 'object' && Object.keys(window.chatbotState.menuInfo).length === 0)) {
        console.warn("[getMenuDelDia] menuInfo no disponible o vacío.");
        return "Lo siento, no tengo disponible la información del menú en este momento.";
    }
    
    const originalDiaQuery = dia; // Keep track if a specific day was asked for

    const hoy = new Date();
    // Usar el mismo orden que en Python: lunes=0, martes=1, etc.
    const diasSemana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'];
    // Convertir JavaScript getDay() (domingo=0) a formato Python weekday() (lunes=0)
    const dayIndex = hoy.getDay() === 0 ? 6 : hoy.getDay() - 1; // domingo=6, lunes=0, etc.
    const diaDeHoyString = diasSemana[dayIndex];

    if (!dia) {
        dia = diaDeHoyString;
        console.log(`[getMenuDelDia] Día no especificado, usando hoy: ${dia}`);
    }
    
    if (!turno) {
        const hora = new Date().getHours();
        turno = (hora >= 11 && hora < 16) ? 'almuerzo' : 'cena';
        console.log(`[getMenuDelDia] Turno no especificado, usando actual: ${turno} (hora: ${hora})`);
    }
    
    console.log(`[getMenuDelDia] Procesando para: dia='${dia}', turno='${turno}'`);
    console.log(`[getMenuDelDia] menuInfo completo:`, window.chatbotState.menuInfo);

    let menuTurnoSeleccionado = null;

    if (dia.toLowerCase() === diaDeHoyString) {
        console.log(`[getMenuDelDia] Buscando menú para hoy (${diaDeHoyString}), turno: ${turno}`);
        if (turno === 'almuerzo') {
            menuTurnoSeleccionado = window.chatbotState.menuInfo.almuerzo_hoy;
            console.log(`[getMenuDelDia] almuerzo_hoy:`, menuTurnoSeleccionado);
        } else if (turno === 'cena') {
            menuTurnoSeleccionado = window.chatbotState.menuInfo.cena_hoy;
            console.log(`[getMenuDelDia] cena_hoy:`, menuTurnoSeleccionado);
        }

        if (!menuTurnoSeleccionado) {
            console.warn(`[getMenuDelDia] No se encontró menú para ${turno} de hoy (${diaDeHoyString}) en menuInfo.almuerzo_hoy o menuInfo.cena_hoy.`);
            console.warn(`[getMenuDelDia] Claves disponibles en menuInfo:`, Object.keys(window.chatbotState.menuInfo));
            return `Lo siento, no tengo disponible el menú de ${turno} para hoy.`;
        }
    } else {
        console.warn(`[getMenuDelDia] Solicitud para un día (${dia}) que no es hoy (${diaDeHoyString}). Solo se proporciona el menú de hoy.`);
        return `Lo siento, por el momento solo puedo mostrarte el menú de hoy. ¿Te gustaría ver el menú de hoy?`;
    }
    
    if (!Array.isArray(menuTurnoSeleccionado) || menuTurnoSeleccionado.length === 0) {
        console.warn(`[getMenuDelDia] menuTurnoSeleccionado para hoy (${turno}) no es un array o está vacío.`);
        return `No encontré platos específicos para el ${turno} de hoy.`;
    }
    
    let mensaje = `<strong>El menú de ${turno} para hoy (${dia}) es:</strong><br><br>`;
    
    menuTurnoSeleccionado.forEach(plato => {
        mensaje += `• <strong>${plato.name || 'Plato sin nombre'}:</strong> ${plato.price ? `$${plato.price}` : 'Precio no disponible'}<br>`;
    });
    
    mensaje += "<br>Adicionalmente, contamos con opciones para dietas especiales. ¿Necesitas información sobre menú sin TACC, vegetariano o vegano?";
    console.log("[getMenuDelDia] Mensaje final:", mensaje);
    return mensaje;
}

// Función para obtener información de contacto y ubicación
function getInfoContacto() {
    if (!window.chatbotState.restaurantInfo || Object.keys(window.chatbotState.restaurantInfo).length === 0) {
        return "Por el momento no puedo brindarte la información de contacto. Por favor, intenta más tarde.";
    }
    
    let restaurantDisplayName = (window.chatbotState.restaurantInfo.restaurantName) ? `de \"${window.chatbotState.restaurantInfo.restaurantName}\"` : "del restaurante";
    let mensaje = `Información de contacto y ubicación ${restaurantDisplayName}:<br><br>`;
    
    if (window.chatbotState.restaurantInfo.address) {
        mensaje += `📍 <strong>Dirección:</strong> ${window.chatbotState.restaurantInfo.address}<br><br>`;
    }
    
    if (window.chatbotState.restaurantInfo.contactPhone) {
        mensaje += `📞 <strong>Teléfono:</strong> ${window.chatbotState.restaurantInfo.contactPhone}<br>`;
    }
    if (window.chatbotState.restaurantInfo.contactEmail) {
         mensaje += `📧 <strong>Email:</strong> ${window.chatbotState.restaurantInfo.contactEmail}<br>`;
    }
    if (window.chatbotState.restaurantInfo.contactWhatsapp && window.chatbotState.restaurantInfo.contactWhatsapp !== "WhatsApp no disponible") {
        mensaje += `📱 <strong>WhatsApp:</strong> ${window.chatbotState.restaurantInfo.contactWhatsapp}<br>`;
    }
    
    return mensaje;
}

// Nueva función específica para obtener horarios
function getHorarios() {
    let mensaje = "⏰ <strong>Horarios de atención:</strong><br>";
    
    const dias = {
        lunes: "Lunes",
        martes: "Martes",
        miercoles: "Miércoles",
        jueves: "Jueves",
        viernes: "Viernes",
        sabado: "Sábado",
        domingo: "Domingo"
    };
        
    if (!window.chatbotState.openingHours || Object.keys(window.chatbotState.openingHours).length === 0) {
        return mensaje + "No tengo información de horarios disponible en este momento.";
    }

    for (const [diaKey, horarioData] of Object.entries(window.chatbotState.openingHours)) {
        if (dias.hasOwnProperty(diaKey) && horarioData && horarioData.open && horarioData.close) {
            const nombreDia = dias[diaKey];
            let horarioStr = `- ${nombreDia}: ${horarioData.open} a ${horarioData.close}`;
            if (horarioData.is_closed) {
                horarioStr = `- ${nombreDia}: Cerrado`;
            } else if (horarioData.nota) {
                horarioStr += ` (${horarioData.nota})`;
            }
            mensaje += horarioStr + "<br>";
        } else if (dias.hasOwnProperty(diaKey) && horarioData && horarioData.is_closed === true) {
            const nombreDia = dias[diaKey];
            mensaje += `- ${nombreDia}: Cerrado<br>`;
        }
    }
    
    return mensaje;
}

// Función para obtener direcciones sobre cómo llegar
function getComoLlegar() {
    if (!window.chatbotState.restaurantInfo) { 
        return "Por el momento no puedo brindarte instrucciones sobre cómo llegar. Por favor, intenta más tarde.";
    }

    let mensaje = "🚶‍♂️🗺️ <strong>Cómo llegar:</strong><br><br>";
    let infoProporcionada = false;

    if (window.chatbotState.restaurantInfo.address) {
        mensaje += `Nuestra dirección es: <strong>${window.chatbotState.restaurantInfo.address}</strong>.<br><br>`;
        infoProporcionada = true;
    }

    // El google_maps_link podría estar en el objeto principal o en un subobjeto location
    const googleMapsLink = window.chatbotState.restaurantInfo.google_maps_link || (window.chatbotState.restaurantInfo.location && window.chatbotState.restaurantInfo.location.google_maps_link);
    if (googleMapsLink) {
        mensaje += `Puedes encontrarnos en Google Maps aquí: <a href="${googleMapsLink}" target="_blank">Ver en Google Maps</a>.<br><br>`;
        infoProporcionada = true;
    }

    // Las instrucciones podrían estar en directions_description o en una propiedad similar
    const directions = window.chatbotState.restaurantInfo.directions_description || 
                      (window.chatbotState.restaurantInfo.location && window.chatbotState.restaurantInfo.location.directions_description);
    if (directions) {
        mensaje += `${directions}<br><br>`;
        infoProporcionada = true;
    }

    if (!infoProporcionada) {
        return "No tengo instrucciones detalladas sobre cómo llegar en este momento, pero nuestra dirección y detalles de contacto están disponibles. Pregunta por 'contacto'.";
    }
    
    return mensaje;
}

// Función para obtener información de menú especial (sin TACC/vegetariano/vegano)
function getMenuEspecial(tipo) {
    console.log('[DEBUG] getMenuEspecial called with tipo:', tipo);
    console.log('[DEBUG] menuInfo:', window.chatbotState.menuInfo);

    if (!window.chatbotState.menuInfo) {
        console.warn('[WARN] menuInfo no está disponible');
        return "Por el momento no puedo brindarte información sobre menús especiales. Por favor, intenta más tarde.";
    }

    let menuSolicitado = null;
    let nombreMenu = "";

    if (tipo.includes('tacc') || tipo.includes('celiac') || tipo.includes('gluten')) {
        console.log('[DEBUG] Verificando menú sin TACC:', {
            menu_sin_tacc: window.chatbotState.menuInfo.menu_sin_tacc
        });

        if (!window.chatbotState.menuInfo.menu_sin_tacc) {
            console.warn('[WARN] menu_sin_tacc no existe en menuInfo');
            return "Lo siento, en este momento no tengo información sobre el menú sin TACC. Por favor, consulta directamente con nuestro personal.";
        }

        menuSolicitado = window.chatbotState.menuInfo.menu_sin_tacc;
        if (!menuSolicitado) {
            console.warn('[WARN] El menú celíaco es null o undefined:', menuSolicitado);
            return "Lo siento, en este momento no tengo información sobre el menú sin TACC. Por favor, consulta directamente con nuestro personal.";
        }

        console.log('[DEBUG] Menú celíaco encontrado:', menuSolicitado);
        nombreMenu = "Sin TACC / Celíaco";
    } else if (tipo.includes('vegetarian')) {
        menuSolicitado = window.chatbotState.menuInfo.menu_especial.vegetariano;
    } else if (tipo.includes('vegan')) {
        menuSolicitado = window.chatbotState.menuInfo.menu_especial.vegano;
        nombreMenu = "Vegano";
    }

    if (!menuSolicitado) {
        console.warn('[WARN] No se pudo determinar el tipo de menú especial solicitado');
        return "No estoy seguro de qué tipo de menú especial necesitas. ¿Podrías especificar si es para celíacos (sin TACC), vegetariano o vegano?";
    }

    console.log('[DEBUG] Menú solicitado encontrado:', menuSolicitado);
    let mensaje = `<strong>Menú Especial: ${nombreMenu}</strong><br><br>`;
    let infoEncontrada = false;

    if (menuSolicitado.descripcion_general) {
        mensaje += `${menuSolicitado.descripcion_general}<br><br>`;
    }

    if (menuSolicitado.platos_principales && Array.isArray(menuSolicitado.platos_principales) && menuSolicitado.platos_principales.length > 0) {
        console.log('[DEBUG] Procesando platos principales:', menuSolicitado.platos_principales);
        mensaje += "<strong>Platos Principales:</strong><br>";
        menuSolicitado.platos_principales.forEach(plato => {
            console.log('[DEBUG] Procesando plato:', plato);
            if (typeof plato === 'string') {
                mensaje += `• ${plato}<br>`;
            } else if (typeof plato === 'object' && plato.name) {
                mensaje += `• ${plato.name}${plato.price ? ` - $${plato.price}` : ''}<br>`;
            }
        });
        mensaje += "<br>";
        infoEncontrada = true;
    }

    if (menuSolicitado.postres && menuSolicitado.postres.length > 0) {
        mensaje += "<strong>Postres:</strong><br>";
        menuSolicitado.postres.forEach(postre => {
            if (typeof postre === 'string') {
                mensaje += `• ${postre}<br>`;
            } else if (typeof postre === 'object' && postre.name) {
                mensaje += `• ${postre.name}${postre.price ? ` - $${postre.price}` : ''}<br>`;
            }
        });
        mensaje += "<br>";
        infoEncontrada = true;
    }
    
    if (menuSolicitado.panificados && menuSolicitado.panificados.length > 0) {
        mensaje += "<strong>Panificados:</strong><br>";
        menuSolicitado.panificados.forEach(pan => {
             mensaje += `• ${pan}<br>`;
        });
        mensaje += "<br>";
        infoEncontrada = true;
    }
    
    if (menuSolicitado.bebidas && menuSolicitado.bebidas.length > 0) {
        mensaje += "<strong>Bebidas:</strong><br>";
        menuSolicitado.bebidas.forEach(bebida => {
             mensaje += `• ${bebida}<br>`;
        });
        mensaje += "<br>";
        infoEncontrada = true;
    }

    if (!infoEncontrada) {
        return `No tengo detalles específicos para el menú ${nombreMenu} en este momento, pero puedes consultar con nuestro personal.`;
    }

    return mensaje;
}

// Función para procesar la respuesta de la reserva
async function procesarRespuestaReserva(mensaje) {
    let respuestaBot = '';
    const state = window.chatbotState;
    console.log('[procesarRespuestaReserva] Processing:', mensaje, 'Current step:', state.pasoActual);

    try {
        switch (state.pasoActual) {
            case 'nombre':
                state.datosReserva.nombre = mensaje;
                state.primerNombre = mensaje.split(' ')[0];
                
                // Check if we already have fecha and personas from availability check
                if (state.datosReserva.fecha && state.datosReserva.personas) {
                    // Skip fecha and personas, go directly to hora
                    state.pasoActual = 'hora';
                    const [year, month, day] = state.datosReserva.fecha.split('-');
                    const fechaFormateada = `${day}/${month}/${year}`;
                    respuestaBot = `Gracias, ${state.primerNombre}. Veo que es para ${state.datosReserva.personas} ${state.datosReserva.personas == 1 ? 'persona' : 'personas'} el ${fechaFormateada}.
                    <br><br>¿A qué hora te gustaría la reserva? (Ej: 13:00, 20:00, 21:30)`;
                } else {
                    // Standard flow - ask for fecha
                    state.pasoActual = 'fecha';
                    respuestaBot = `Gracias, ${state.primerNombre}. ¿Para qué fecha te gustaría la reserva? (Ej: "15/05/2025", "hoy", "mañana")`;
                }
                break;

            case 'fecha':
                const fechaParseada = parsearFechaInput(mensaje);
                if (fechaParseada) {
                    state.datosReserva.fecha = fechaParseada;
                    state.pasoActual = 'hora';
                    const [year, month, day] = fechaParseada.split('-');
                    const fechaFormateada = `${day}/${month}/${year}`;
                    respuestaBot = `Entendido, ${state.primerNombre}. ¿A qué hora sería la reserva para el ${fechaFormateada}? (Ej: 13:00, 21:30)`;
                } else {
                    respuestaBot = `Lo siento, ${state.primerNombre}, no entendí la fecha. Por favor, usa un formato como "DD/MM/YYYY" (ej: 15/05/2025), o escribe "hoy" o "mañana".`;
                }
                break;

            case 'hora':
                state.datosReserva.hora = mensaje;
                
                // Check if we already have personas from availability check
                if (state.datosReserva.personas) {
                    // Skip personas, go directly to telefono
                    state.pasoActual = 'telefono';
                    respuestaBot = `Perfecto, ${state.primerNombre}. ¿Podrías proporcionarme un número de teléfono de contacto? El día anterior te enviaremos un recordatorio de tu reserva.`;
                } else {
                    // Standard flow - ask for personas
                    state.pasoActual = 'personas';
                    respuestaBot = `Perfecto. ¿Para cuántas personas sería la reserva?`;
                }
                break;

            case 'personas':
                state.datosReserva.personas = mensaje;
                state.pasoActual = 'telefono';
                respuestaBot = `Muy bien, ${state.primerNombre}. ¿Podrías proporcionarme un número de teléfono de contacto? El día anterior te enviaremos un recordatorio de tu reserva.`;
                break;

            case 'telefono':
                state.datosReserva.telefono = mensaje;
                state.pasoActual = 'email';
                respuestaBot = `Gracias. Por favor, proporciona tu dirección de correo electrónico para enviarte la confirmación.`;
                break;

            case 'email':
                if (mensaje && mensaje.includes('@') && mensaje.includes('.')) {
                    state.datosReserva.email = mensaje;
                    state.pasoActual = 'comentarios';
                    respuestaBot = `Perfecto, ${state.primerNombre}. ¿Algún comentario o pedido especial para tu reserva? (Opcional, puedes decir "ninguno")`;
                } else {
                    respuestaBot = `Por favor, ingresa una dirección de correo electrónico válida.`;
                }
                break;

            case 'comentarios':
                if (mensaje.toLowerCase() !== 'ninguno' && mensaje.toLowerCase() !== 'no') {
                    state.datosReserva.comentarios = mensaje;
                }

                let idFromChatbotConfig = window.chatbotConfig?.restaurantId;
                let idFromRestaurantInfo = window.chatbotState.restaurantInfo?.restaurantId;
                const restaurantId = idFromRestaurantInfo || idFromChatbotConfig;

                if (!restaurantId) {
                    respuestaBot = `Lo siento, ${state.primerNombre}, no pude identificar el restaurante para verificar la disponibilidad.`;
                    break;
                }

                try {
                    const disponibilidadResponse = await fetch('/api/reservas/validar_disponibilidad', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            restaurante_id: restaurantId,
                            fecha: state.datosReserva.fecha,
                            hora: state.datosReserva.hora,
                            personas: parseInt(state.datosReserva.personas, 10) || state.datosReserva.personas
                        }),
                    });

                    const disponibilidadResult = await disponibilidadResponse.json();
                    
                    if (disponibilidadResponse.ok && disponibilidadResult.available) {
                        state.pasoActual = 'confirmacion';
                        const [year, month, day] = state.datosReserva.fecha.split('-');
                        const fechaFormateada = `${day}/${month}/${year}`;
                        respuestaBot = `Excelente. Por favor, revisa los datos de tu reserva:
                            <br>Nombre: ${state.datosReserva.nombre}
                            <br>Fecha: ${fechaFormateada}
                            <br>Hora: ${state.datosReserva.hora}
                            <br>Personas: ${state.datosReserva.personas}
                            <br>Teléfono: ${state.datosReserva.telefono}
                            <br>Email: ${state.datosReserva.email}
                            ${state.datosReserva.comentarios ? `<br>Comentarios: ${state.datosReserva.comentarios}` : ''}
                            <br><br>¿Ves todo correcto ${state.datosReserva.nombre}? (Sí/No)`;
                    } else {
                        const errorMsg = disponibilidadResult.message || 'No hay disponibilidad para esa fecha y hora.';
                        respuestaBot = `Lo siento, ${state.primerNombre}, ${errorMsg} ¿Quieres intentar con otra fecha u hora?`;
                        state.pasoActual = 'fecha';
                    }
                } catch (error) {
                    console.error("Error al verificar disponibilidad:", error);
                    respuestaBot = `Lo siento, ${state.primerNombre}, ocurrió un error al verificar la disponibilidad. Por favor, intenta más tarde.`;
                    state.reservaEnProceso = false;
                    state.pasoActual = '';
                }
                break;

            case 'confirmacion':
                if (mensaje.toLowerCase().startsWith('s')) {
                    try {
                        // Obtener ID del restaurante de forma más robusta
                        let restaurante_id = window.chatbotConfig?.restaurantId;
                        if (!restaurante_id) {
                            restaurante_id = window.chatbotState?.restaurantInfo?.restaurantId;
                        }

                        if (!restaurante_id) {
                            throw new Error('No se pudo identificar el ID del restaurante');
                        }

                        // Validar formato del ID
                        if (typeof restaurante_id !== 'string' || !restaurante_id.match(/^[0-9a-f-]+$/)) {
                            throw new Error('ID de restaurante no válido');
                        }
                        
                        const reservaPayload = {
                            restaurante_id: restaurante_id,  // Usar solo restaurante_id para consistencia
                            nombre: state.datosReserva.nombre,
                            // Convert fecha from DD/MM/YYYY to YYYY-MM-DD if needed
                            fecha: (() => {
                                try {
                                    const fecha = state.datosReserva.fecha;
                                    // If date is already in YYYY-MM-DD format, validate and return
                                    if (fecha.match(/^\d{4}-\d{2}-\d{2}$/)) {
                                        // Validate date parts
                                        const [year, month, day] = fecha.split('-').map(Number);
                                        if (isNaN(year) || isNaN(month) || isNaN(day)) {
                                            throw new Error('Invalid date parts');
                                        }
                                        // Create date object to validate the date
                                        const d = new Date(year, month - 1, day);
                                        if (d.getFullYear() !== year || d.getMonth() + 1 !== month || d.getDate() !== day) {
                                            throw new Error('Invalid date');
                                        }
                                        return fecha;
                                    }
                                    
                                    // Otherwise, convert from DD/MM/YYYY to YYYY-MM-DD
                                    const [day, month, year] = fecha.split('/').map(part => part.trim());
                                    // Validate all parts exist and are numbers
                                    if (!day || !month || !year || isNaN(Number(day)) || isNaN(Number(month)) || isNaN(Number(year))) {
                                        throw new Error('Invalid date format');
                                    }
                                    // Validate date using Date object
                                    const d = new Date(Number(year), Number(month) - 1, Number(day));
                                    if (d.getFullYear() !== Number(year) || d.getMonth() + 1 !== Number(month) || d.getDate() !== Number(day)) {
                                        throw new Error('Invalid date');
                                    }
                                    return `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
                                } catch(e) {
                                    console.error('Error converting date format:', e);
                                    throw e; // Re-throw to prevent invalid dates from being sent
                                }
                            })(),
                            hora: state.datosReserva.hora,
                            personas: parseInt(state.datosReserva.personas, 10),
                            telefono: state.datosReserva.telefono.replace(/\s+/g, ''),
                            email: state.datosReserva.email,
                            comentarios: state.datosReserva.comentarios || '',
                            estado: "confirmada",
                            origen: "chatbot"
                        };

                        console.log('[DEBUG] Enviando reserva a API:', JSON.stringify(reservaPayload));

                        const responseData = await makeApiCall('/api/reservas', {
                            method: 'POST',
                            headers: { 
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify(reservaPayload),
                        });

                        console.log('[DEBUG] Respuesta de API:', responseData);

                        if (responseData.success) {
                            // Only attempt to send confirmation email if reservation was successful
                            if (responseData.id) {
                                try {
                                    const emailResult = await enviarEmailConfirmacion(responseData.id, state.datosReserva.email, restaurante_id);
                                    respuestaBot = `¡Perfecto ${state.primerNombre}! Tu reserva ha sido confirmada${emailResult ? ' y hemos enviado un email de confirmación a ' + state.datosReserva.email : ''}. ¿Hay algo más en lo que pueda ayudarte?`;
                                } catch (emailError) {
                                    console.error('[ERROR] Error sending confirmation email:', emailError);
                                    respuestaBot = `¡Reserva confirmada ${state.primerNombre}! Sin embargo, hubo un problema al enviar el email de confirmación. No te preocupes, tu reserva está guardada. Por favor, contacta al restaurante si necesitas los detalles.`;
                                }
                            } else {
                                respuestaBot = `¡Reserva confirmada ${state.primerNombre}! ¿Hay algo más en lo que pueda ayudarte?`;
                            }
                        } else {
                            throw new Error(responseData.error || 'Error al confirmar la reserva');
                        }
                    } catch (error) {
                        console.error("[ERROR] Error al guardar la reserva:", error);
                        respuestaBot = `Lo siento, ${state.primerNombre}, hubo un problema al guardar tu reserva. Por favor, contacta al restaurante directamente.`;
                    } finally {
                        state.reservaEnProceso = false;
                        state.pasoActual = '';
                        state.datosReserva = { ...window.chatbotState.datosReservaVacio };
                    }
                } else {
                    respuestaBot = `Entiendo. Reserva cancelada. ¿Hay algo más en lo que pueda ayudarte?`;
                    state.reservaEnProceso = false;
                    state.pasoActual = '';
                    state.datosReserva = { ...window.chatbotState.datosReservaVacio };
                }
                break;

            case 'correccion':
                if (mensaje.toLowerCase() === 'cancelar reserva') {
                    respuestaBot = `Reserva cancelada. Si necesitas ayuda con otra cosa, no dudes en preguntar.`;
                    state.reservaEnProceso = false;
                    state.pasoActual = '';
                    state.datosReserva = { ...window.chatbotState.datosReservaVacio };
                } else {
                    respuestaBot = `Lo siento, ${state.primerNombre}, no entendí qué quieres corregir. Por favor, especifica qué dato quieres modificar (nombre, fecha, hora, personas, teléfono, email) o di "cancelar reserva".`;
                }
                break;

            default:
                console.warn(`[DEBUG] Paso no reconocido: ${state.pasoActual}`);
                respuestaBot = `Lo siento, ${state.primerNombre}, hubo un problema con el proceso de reserva. Por favor, intenta nuevamente.`;
                state.reservaEnProceso = false;
                state.pasoActual = '';
                break;
        }
    } catch (error) {
        console.error('[ERROR] Error en procesarRespuestaReserva:', error);
        respuestaBot = `Lo siento, ${state.primerNombre}, ocurrió un error inesperado. Por favor, intenta nuevamente.`;
        state.reservaEnProceso = false;
        state.pasoActual = '';
    }

    return respuestaBot;
}

// Función para procesar consultas generales (no relacionadas con reservas)
async function procesarConsultaGeneral(mensaje, action = null) {
    console.log('[procesarConsultaGeneral] Processing:', mensaje, 'Action:', action);
    let respuesta = '';

    try {
        // Handle direct actions first
        if (action) {
            switch (action) {
                case 'ver_menu':
                    respuesta = getMenuDelDia();
                    break;
                case 'ver_horarios':
                    respuesta = getHorarios();
                    break;
                case 'ver_ubicacion':
                    respuesta = getComoLlegar();
                    break;
                case 'ver_menu_especial':
                    respuesta = getMenuEspecial(mensaje.toLowerCase());
                    break;
            }
        }

        // If no action provided or action didn't produce a response, process based on message content
        if (!respuesta) {
            const msgLower = mensaje.toLowerCase();

            // Saludos y despedidas
            if (msgLower.includes('hola') || msgLower.includes('buen') || msgLower.includes('buenas')) {
                respuesta = window.chatbotState.primerNombre ? 
                    `¡Hola de nuevo, ${window.chatbotState.primerNombre}! ¿En qué puedo ayudarte?` :
                    '¡Hola! ¿En qué puedo ayudarte?';
            } 
            else if (msgLower.includes('chau') || msgLower.includes('gracias')) {
                respuesta = window.chatbotState.primerNombre ? 
                    `De nada, ${window.chatbotState.primerNombre}. ¡Que tengas un buen día!` :
                    'De nada. ¡Que tengas un buen día!';
            }
            // Menú del día
            else if (msgLower.includes('menu') || msgLower.includes('menú') || msgLower.includes('plato') || msgLower.includes('comida')) {
                let dia = msgLower.includes('mañana') ? 'mañana' : null;
                let turno = msgLower.includes('almuerzo') ? 'almuerzo' : 
                           msgLower.includes('cena') ? 'cena' : null;
                respuesta = getMenuDelDia(dia, turno);
            }
            // Horarios
            else if (msgLower.includes('horario')) {
                respuesta = getHorarios();
            }
            // Ubicación y cómo llegar
            else if (msgLower.includes('ubicación') || msgLower.includes('ubicados') || 
                    msgLower.includes('dirección') || msgLower.includes('donde') || 
                    msgLower.includes('dónde') || msgLower.includes('llego')) {
                respuesta = msgLower.includes('llego') ? getComoLlegar() : getInfoContacto();
            }
            // Contacto
            else if (msgLower.includes('contacto') || msgLower.includes('teléfono') || 
                    msgLower.includes('email') || msgLower.includes('whatsapp')) {
                respuesta = getInfoContacto();
            }
            // Menú especial
            else if (msgLower.includes('tacc') || msgLower.includes('gluten') || 
                    msgLower.includes('celiaco') || msgLower.includes('celíaco') || 
                    msgLower.includes('vegetariano') || msgLower.includes('vegano')) {
                respuesta = getMenuEspecial(msgLower);
            }
            // Pagos
            else if (msgLower.includes('pago') || msgLower.includes('tarjeta') || 
                    msgLower.includes('efectivo') || msgLower.includes('mercadopago')) {
                respuesta = 'Aceptamos las siguientes formas de pago:<br>' +
                         '- Efectivo<br>' +
                         '- Tarjetas de débito y crédito<br>' +
                         '- MercadoPago';
            }
            // Consulta de disponibilidad para reservas
            else if (esConsultaDisponibilidad(msgLower)) {
                respuesta = await procesarConsultaDisponibilidad(msgLower);
            }
            // Otras consultas comunes
            else if (msgLower.includes('precio') || msgLower.includes('costo')) {
                respuesta = 'Los precios están detallados en nuestro menú del día. ¿Te gustaría ver el menú?';
            }
            else if (msgLower.includes('delivery') || msgLower.includes('llevar') || 
                    msgLower.includes('pedido')) {
                respuesta = window.chatbotState.restaurantInfo?.contactPhone ?
                    `Sí, ofrecemos servicio de delivery y pedidos para llevar. Puedes hacer tu pedido llamando al ${window.chatbotState.restaurantInfo.contactPhone}.` :
                    'Sí, ofrecemos servicio de delivery y pedidos para llevar. Puedes consultar nuestros datos de contacto para realizar tu pedido.';
            }
            // Fallback para consultas no reconocidas
            else if (esConsultaRelevante(mensaje)) {
                respuesta = 'Disculpa, aún estoy aprendiendo. Por ahora puedo ayudarte con información sobre:<br>' +
                         '- Nuestro menú del día<br>' +
                         '- Horarios de atención<br>' +
                         '- Ubicación y contacto<br>' +
                         '- Reservas<br>' +
                         '- Opciones de menú especial (sin TACC, vegetariano, vegano)';
            } else {
                respuesta = 'Lo siento, no pude entender tu consulta. ¿Podrías reformularla? Puedo ayudarte con información sobre el menú, horarios, ubicación o hacer una reserva.';
            }
        }

        if (!respuesta) {
            respuesta = 'Lo siento, no pude procesar tu consulta en este momento. ¿Podrías intentarlo de otra manera?';
        }

        return respuesta;
        
    } catch (error) {
        console.error('[ERROR] Error en procesarConsultaGeneral:', error);
        return 'Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta nuevamente.';
    }
}

// Helper function to detect availability queries
function esConsultaDisponibilidad(mensaje) {
    const palabrasClaveDisponibilidad = [
        'tenes mesa', 'tienes mesa', 'hay mesa', 'tienen mesa', 'tenés mesa',
        'mesa disponible', 'disponibilidad', 'libre para', 'lugar para',
        'mesa para', 'reservar para', 'disponible para', 'libres para',
        'hay lugar', 'hay lugar para', 'lugar disponible'
    ];
    
    // También buscar patrones de fecha
    const tieneFecha = mensaje.includes('mañana') || 
                      mensaje.includes('hoy') || 
                      /\d{1,2}\/\d{1,2}/.test(mensaje) || 
                      /\d{1,2}\s+de\s+[a-záéíóúñ]+/i.test(mensaje);
    
    return palabrasClaveDisponibilidad.some(palabra => mensaje.includes(palabra)) && tieneFecha;
}

// Function to process availability queries
async function procesarConsultaDisponibilidad(mensaje) {
    console.log('[procesarConsultaDisponibilidad] Processing availability query:', mensaje);
    
    try {
        // Extract date from message
        let fechaStr = null;
        let personasStr = null;
        
        // Parse date
        if (mensaje.includes('mañana')) {
            fechaStr = parsearFechaInput('mañana');
        } else if (mensaje.includes('hoy')) {
            fechaStr = parsearFechaInput('hoy');
        } else {
            // Try to find date patterns
            const fechaMatch = mensaje.match(/(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)/);
            if (fechaMatch) {
                fechaStr = parsearFechaInput(fechaMatch[1]);
            } else {
                // Try "DD de MMMM" pattern
                const fechaMesMatch = mensaje.match(/(\d{1,2})\s+de\s+([a-záéíóúñ]+)/i);
                if (fechaMesMatch) {
                    fechaStr = parsearFechaInput(fechaMesMatch[0]);
                }
            }
        }
        
        // Extract number of people
        const personasMatch = mensaje.match(/(\d+)\s*personas?/i) || 
                             mensaje.match(/para\s+(\d+)/i) ||
                             mensaje.match(/(\d+)\s*pax/i);
        if (personasMatch) {
            personasStr = personasMatch[1];
        } else {
            // Default to 2 people if not specified
            personasStr = '2';
        }
        
        if (!fechaStr) {
            return 'Para verificar la disponibilidad necesito saber la fecha. ¿Para qué día te gustaría la mesa? Puedes decir "hoy", "mañana", o una fecha específica como "25/12" o "15 de mayo".';
        }
        
        // Get restaurant ID
        const restaurantId = window.chatbotState.restaurantInfo?.restaurantId || window.chatbotConfig?.restaurantId;
        if (!restaurantId) {
            return 'Lo siento, no pude identificar el restaurante para verificar la disponibilidad.';
        }
        
        // Format date for display
        const [year, month, day] = fechaStr.split('-');
        const fechaFormateada = `${day}/${month}/${year}`;
        
        // For availability check, we need a time - use default dinner time
        const horaConsulta = '20:00';
        
        // Call availability API
        const response = await fetch('/api/reservas/validar_disponibilidad', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                restaurante_id: restaurantId,
                fecha: fechaStr,
                hora: horaConsulta,
                personas: parseInt(personasStr)
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.available) {
            // Store availability context for potential follow-up
            window.chatbotState.lastAvailabilityCheck = {
                fecha: fechaStr,
                personas: parseInt(personasStr),
                fechaFormateada: fechaFormateada
            };
            
            let respuesta = `¡Sí! Tenemos disponibilidad para ${personasStr} ${personasStr == '1' ? 'persona' : 'personas'} el ${fechaFormateada}.`;
            respuesta += '<br><br>¿Te gustaría hacer una reserva? Responde <strong>"sí"</strong> para comenzar</strong>.';
            return respuesta;
        } else {
            const mensaje = result.message || 'No hay disponibilidad para esa fecha y horario.';
            let respuesta = `Lo siento, ${mensaje}`;
            respuesta += '<br><br>¿Te gustaría intentar con otra fecha? También puedes hacer una reserva para ver más opciones de horarios disponibles.';
            return respuesta;
        }
        
    } catch (error) {
        console.error('[ERROR] Error al procesar consulta de disponibilidad:', error);
        return 'Lo siento, hubo un error al verificar la disponibilidad. ¿Te gustaría hacer una reserva directamente?';
    }
}

// --- ADDED CODE STARTS HERE ---

// Function to add a message to the chat interface
function addMessage(sender, text, isHTML = false) {
    console.log(`[CHATBOT_DEBUG] addMessage called by ${sender} with text: ${text ? text.substring(0,100) : ''}`);
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) {
        console.error('Chat messages container #chatMessages not found!');
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    
    // Create an inner div for the actual message content
    const contentDiv = document.createElement('div');
    if (isHTML) {
        contentDiv.innerHTML = text;
    } else {
        contentDiv.textContent = text;
    }
    
    messageElement.appendChild(contentDiv);
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    console.log('[CHATBOT_DEBUG] Message appended, scrolltop updated.');
}

// Función para mostrar mensajes del bot con efecto de máquina de escribir
function displayBotMessageWithTypewriter(messageText, speed = 30) {
    console.log("[CHATBOT_DEBUG] displayBotMessageWithTypewriter CALLED with message:", messageText);

    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error("[CHATBOT_ERROR] chatMessages element not found");
        return;
    }

    // Remove any existing typing indicator
    const existingIndicator = document.getElementById('typingIndicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }

    // Create message container
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'bot-message-bubble';
    bubbleDiv.style.cssText = 'background-color: #E8F5E9; color: #2E7D32; padding: 12px; border-radius: 12px; border-bottom-left-radius: 2px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); opacity: 0; transition: opacity 0.3s ease-in-out;';

    const currentMessageP = document.createElement('p');
    currentMessageP.style.margin = '0';
    currentMessageP.className = 'bot-message-text';

    bubbleDiv.appendChild(currentMessageP);
    messageDiv.appendChild(bubbleDiv);
    chatMessages.appendChild(messageDiv);

    // Show the message container
    setTimeout(() => {
        bubbleDiv.style.opacity = '1';
    }, 100);

    let currentChar = 0;
    const textContent = messageText;
    
    function typeNextChar() {
        if (currentChar < textContent.length) {
            const char = textContent[currentChar];
            if (char === '<') {
                // Find the closing '>' and add the entire HTML tag at once
                const tagEnd = textContent.indexOf('>', currentChar);
                if (tagEnd !== -1) {
                    currentMessageP.innerHTML = textContent.substring(0, tagEnd + 1);
                    currentChar = tagEnd + 1;
                }
            } else {
                currentMessageP.innerHTML = textContent.substring(0, currentChar + 1);
                currentChar++;
            }
            
            chatMessages.scrollTop = chatMessages.scrollHeight;
            setTimeout(typeNextChar, speed);
        }
    }

    // Start typing effect
    typeNextChar();
}

// MODIFICACIÓN SUGERIDA:
// Debes encontrar en tu código existente dónde se muestran los mensajes del bot.
// Por ejemplo, si tienes una función como displayMessage(text, sender) o addMessage(text, senderClass),
// o si lo haces directamente en el .then() de un fetch, deberás cambiarlo.

// EJEMPLO DE INTEGRACIÓN:
// Si antes hacías algo como:
// displayMessage(data.response, 'bot-message');
// O directamente:
// const botMessageDiv = document.createElement('div'); /* ... creación del div ... */
// botMessageDiv.querySelector('p').textContent = data.response;
// chatMessages.appendChild(botMessageDiv);

// Ahora deberías llamar a la nueva función así:
// displayBotMessageWithTypewriter(data.response);

// Asegúrate de que los mensajes del usuario sigan apareciendo instantáneamente.
// Si tienes una función genérica para añadir mensajes, podrías hacerla así:

function addMessageToChat(text, senderClass) {
    if (senderClass === 'bot-message') {
        // Primero, elimina el indicador de "escribiendo..." si existe
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        displayBotMessageWithTypewriter(text);
    } else { // user-message
        const chatMessages = document.getElementById('chatMessages');
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', senderClass, 'flex', 'justify-end', 'mb-4');

        const contentDiv = document.createElement('div');
        // Estilos para el mensaje del usuario (ej. Tailwind)
        contentDiv.classList.add('max-w-[80%]', 'user-message-bubble');
        contentDiv.style.cssText = 'background-color: #E3F2FD; color: #1565C0; padding: 12px; border-radius: 12px; border-bottom-right-radius: 2px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);';
        
        const p = document.createElement('p');
        p.style.cssText = 'margin: 0; font-weight: 500;';
        p.textContent = text;
        contentDiv.appendChild(p);
        messageContainer.appendChild(contentDiv);
        chatMessages.appendChild(messageContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Helper function to display bot responses with proper formatting
function displayBotResponse(message, isHTML = false) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error('Chat messages container not found');
        return;
    }

    // Remove any existing typing indicator first
    const existingIndicator = document.querySelector('.typing-indicator-container');
    if (existingIndicator) {
        existingIndicator.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'bot-message flex justify-start mb-4';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'max-w-[80%] bg-green-50 p-3 rounded-lg rounded-tl-none shadow-sm border border-green-100';
    
    if (isHTML) {
        contentDiv.innerHTML = message;
    } else {
        const p = document.createElement('p');
        p.className = 'text-gray-700';
        p.textContent = message;
        contentDiv.appendChild(p);
    }

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Función para mostrar el indicador de "escribiendo..."
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error('Chat messages container not found');
        return;
    }

    // Remove any existing typing indicator first
    const existingIndicator = document.querySelector('.typing-indicator-container');
    if (existingIndicator) {
        existingIndicator.remove();
    }

    const typingDiv = document.createElement('div');
    typingDiv.className = 'bot-message typing-indicator-container';
    typingDiv.innerHTML = `
        <div class="flex items-center p-3 bg-green-50 rounded-lg rounded-tl-none shadow-sm border border-green-100 max-w-fit">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
            <span class="ml-2 text-sm text-gray-600">El asistente está escribiendo...</span>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingDiv;
}

// CSS para los puntos de "escribiendo..." (añadir esto en tu <style> en index.html o en un archivo CSS)
/*
.typing-dot {
    animation: blink 1.4s infinite both;
    font-size: 1.5em;
}
.typing-dot:nth-child(2) {
    animation-delay: 0.2s;
}
.typing-dot:nth-child(3) {
    animation-delay: 0.4s;
}
@keyframes blink {
    0% { opacity: 0.2; }
    20% { opacity: 1; }
    100% { opacity: 0.2; }
}
*/

// Helper function to check for reservation intent in a message
function quiereHacerReserva(mensaje) {
    const msgLower = mensaje.toLowerCase();
    
    // Check for direct affirmative responses after availability check
    if (window.chatbotState.lastAvailabilityCheck) {
        const respuestasAfirmativas = [
            'si', 'sí', 'yes', 'ok', 'dale', 'bueno', 'claro', 'perfecto',
            'genial', 'excelente', 'vamos', 'hagamos', 'quiero', 'me gustaría'
        ];
        if (respuestasAfirmativas.some(palabra => msgLower === palabra || msgLower.includes(palabra))) {
            return true;
        }
    }
    
    // Keywords that might indicate a desire to make a reservation
    const palabrasClaveReserva = [
        'reserva', 'reservar', 'anotame', 'anotar', 'guardar una mesa', 
        'reservacion', 'quisiera una mesa', 'necesito una mesa', 'reservo',
        'hacer una reserva', 'reservar mesa'
    ];
    return palabrasClaveReserva.some(palabra => msgLower.includes(palabra));
}

// Function to handle sending messages and getting bot responses
async function sendMessage(userMessage, action = null) {
    console.log(`[sendMessage] User: "${userMessage}"${action ? ', Action: "' + action + '"' : ''}`);
    const typingIndicator = showTypingIndicator(); // Show "Bot is typing..."

    let botResponse;

    try {
        if (window.chatbotState.reservaEnProceso) {
            // If currently in a reservation process, all input goes to procesarRespuestaReserva
            botResponse = await procesarRespuestaReserva(userMessage);
        } else {
            // Not in a reservation process
            if (action === 'iniciar_reserva' || (!action && quiereHacerReserva(userMessage))) {
                console.log("[CHATBOT_DEBUG] sendMessage: Detectada intención de reserva o acción 'iniciar_reserva'.");
                window.chatbotState.reservaEnProceso = true;
                window.chatbotState.pasoActual = 'nombre'; // Start of reservation flow
                
                // If coming from availability check, pre-populate some data
                if (window.chatbotState.lastAvailabilityCheck) {
                    const availCheck = window.chatbotState.lastAvailabilityCheck;
                    window.chatbotState.datosReserva = {
                        fecha: availCheck.fecha, // Already in YYYY-MM-DD format
                        personas: availCheck.personas
                    };
                    
                    botResponse = `¡Perfecto! Veo que quieres hacer una reserva para ${availCheck.personas} ${availCheck.personas == 1 ? 'persona' : 'personas'} el ${availCheck.fechaFormateada}.
                    <br><br>Para comenzar, ¿podrías decirme tu nombre y apellido?`;
                    
                    // Clear the availability check context
                    window.chatbotState.lastAvailabilityCheck = null;
                } else {
                    botResponse = `Genial ¿podrías decirme tu nombre y apellido?`;
                }
            } else {
                // Process as a general query, now passing the action
                botResponse = await procesarConsultaGeneral(userMessage, action);
            }
        }
    } catch (error) {
        console.error("Error in sendMessage:", error);
        botResponse = "Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, intenta de nuevo.";
    }

    // addMessageToChat will remove the typing indicator when it adds the bot's message
    addMessageToChat(botResponse, 'bot-message');
}

// Inicialización del chatbot
document.addEventListener('DOMContentLoaded', function() {
    console.log('[CHATBOT_INIT] DOMContentLoaded event fired');
    let initialized = false;

    // Wait for DOM elements to be ready
    const waitForElements = setInterval(() => {
        const elements = {
            chatMessages: document.getElementById('chatMessages'),
            chatInput: document.getElementById('chatInput'),
            sendButton: document.getElementById('sendButton'),
            quickActionContainer: document.getElementById('quickActionContainer')
        };
        
        // Check if all elements are present
        if (Object.values(elements).every(el => el) && !initialized) {
            clearInterval(waitForElements);
            initialized = true;
            initializeChatbot(elements);
        }
    }, 100);

    // Set a timeout to avoid infinite waiting
    setTimeout(() => {
        if (!initialized) {
            clearInterval(waitForElements);
            console.error('[CHATBOT_ERROR] Timed out waiting for DOM elements');
            showErrorMessage('Error al cargar el chatbot. Por favor, recarga la página.');
        }
    }, 5000);
});

// Main initialization function
function initializeChatbot(elements) {
    console.log('[CHATBOT_DEBUG] initializeChatbot called');

    // Validate configuration
    if (!window.chatbotConfig) {
        console.error('[CHATBOT_ERROR] Missing chatbotConfig');
        showErrorMessage('Error al cargar la configuración del chatbot');
        return;
    }

    // Initialize chatbot data
    if (!inicializarDatosChatbot()) {
        console.error('[CHATBOT_ERROR] Failed to initialize chatbot data');
        showErrorMessage('Error al inicializar el chatbot');
        return;
    }

        // Set up event listeners if elements are available
    if (elements.chatInput && elements.sendButton) {
        setupEventListeners(elements);
    } else {
        console.error('[CHATBOT_ERROR] Missing required elements for event listeners');
        showErrorMessage('Error al configurar el chat');
        return;
    }
    
    // Set up quick action buttons
    setupQuickActions();

    // Show welcome message after a short delay to allow for rendering
    setTimeout(showWelcomeMessage, 500);

    window.chatbotState.chatbotInitializedSuccessfully = true;
    console.log('[CHATBOT_INFO] Chatbot initialized successfully');
}

// Show a welcome message in the chat
function showWelcomeMessage() {
    // Get restaurant name from config
    const restaurantName = 
        window.chatbotState?.restaurantInfo?.restaurantName || 
        window.chatbotConfig?.restaurantName || 
        'el restaurante';

    // Compose welcome message
    const welcome = window.chatbotConfig?.welcomeMessage ||
        `¡Hola! Soy el asistente virtual de ${restaurantName}. ¿En qué puedo ayudarte hoy? Puedes preguntarme sobre nuestro menú, horarios, o hacer una reserva.`;

    // Use typewriter effect
    displayBotMessageWithTypewriter(welcome);
}

// Show an error message in the chat
function showErrorMessage(msg) {
    addMessageToChat(msg || 'Ocurrió un error al cargar el chatbot.', 'bot-message');
}

// Set up event listeners for user input
function setupEventListeners(elements) {
    const { chatInput, sendButton } = elements;

    // Handle send button click
    sendButton.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            displayUserMessage(message);
            chatInput.value = '';
            procesarMensajeUsuario(message);
        }
    });

    // Handle Enter key press
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (message) {
                displayUserMessage(message);
                chatInput.value = '';
                procesarMensajeUsuario(message);
            }
        }
    });
}

// Función para mostrar el mensaje del usuario en el chat
function displayUserMessage(message) {
    addMessageToChat(message, 'user-message');
}

// Set up quick action buttons
function setupQuickActions() {
    const quickActionContainer = document.getElementById('quickActionContainer');
    if (!quickActionContainer) {
        console.error('[CHATBOT_ERROR] Quick action container not found');
        return;
    }

    // Remove any existing event listeners
    const newContainer = quickActionContainer.cloneNode(true);
    quickActionContainer.parentNode.replaceChild(newContainer, quickActionContainer);

    // Add event listeners to all quick action buttons
    const quickButtons = newContainer.querySelectorAll('.quick-button');
    quickButtons.forEach(button => {
        const question = button.getAttribute('data-question');
        
        if (!question) {
            console.error('[CHATBOT_ERROR] Button missing data-question attribute:', button.textContent);
            return;
        }

        button.addEventListener('click', (e) => {
            e.preventDefault();
            console.log(`[CHATBOT_DEBUG] Quick action clicked with question: ${question}`);
            
            // Show the user's question
            displayUserMessage(question);

            // Get the action from data-action attribute, or determine based on question content
            let action = button.getAttribute('data-action');
            if (!action) {
                // Fallback to determining action from question content
                if (question.toLowerCase().includes('horario')) action = 'ver_horarios';
                else if (question.toLowerCase().includes('menu') || question.toLowerCase().includes('menú')) action = 'ver_menu';
                else if (question.toLowerCase().includes('ubicados') || question.toLowerCase().includes('ubicación')) action = 'ver_ubicacion';
                else if (question.toLowerCase().includes('tacc') || question.toLowerCase().includes('gluten')) action = 'ver_menu_especial';
            }

            // Process the message
            procesarMensajeUsuario(question, action);
        });
    });
    
    console.log('[CHATBOT_INFO] Quick actions setup complete:', quickButtons.length, 'buttons');
}

// Process user messages
async function procesarMensajeUsuario(message, action = null) {
    const typingIndicator = showTypingIndicator();
    
    try {
        let response;
        if (window.chatbotState.reservaEnProceso) {
            response = await procesarRespuestaReserva(message);
        } else if (action === 'iniciar_reserva' || (!action && quiereHacerReserva(message))) {
            console.log("[CHATBOT_DEBUG] procesarMensajeUsuario: Detectada intención de reserva.");
            window.chatbotState.reservaEnProceso = true;
            window.chatbotState.pasoActual = 'nombre';
            
            // If coming from availability check, pre-populate some data
            if (window.chatbotState.lastAvailabilityCheck) {
                const availCheck = window.chatbotState.lastAvailabilityCheck;
                window.chatbotState.datosReserva = {
                    fecha: availCheck.fecha, // Already in YYYY-MM-DD format
                    personas: availCheck.personas
                };
                
                response = `¡Perfecto! Veo que quieres hacer una reserva para ${availCheck.personas} ${availCheck.personas == 1 ? 'persona' : 'personas'} el ${availCheck.fechaFormateada}.
                <br><br>Para comenzar, ¿podrías decirme tu nombre y apellido?`;
                
                // Clear the availability check context
                window.chatbotState.lastAvailabilityCheck = null;
            } else {
                response = '¡Claro! Para comenzar con tu reserva, ¿podrías decirme tu nombre y apellido?';
            }
        } else {
            response = await procesarConsultaGeneral(message, action);
        }

        // Cambiamos displayBotMessage por displayBotMessageWithTypewriter
        displayBotMessageWithTypewriter(response);
    } catch (error) {
        console.error('[CHATBOT_ERROR] Error processing message:', error);
        displayBotMessageWithTypewriter('Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, intenta de nuevo.');
    } finally {
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
}

// Function to make API calls with retry logic
async function makeApiCall(url, options, retries = 2, delay = 2000) {
    for (let i = 0; i < retries; i++) {
        if (i > 0) {
            console.log(`Retry attempt ${i + 1} for ${url}`);
            // Exponential backoff with jitter
            await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i) * (0.8 + Math.random() * 0.4)));
        }

        try {
            // Add cache control headers to prevent SSL/TLS caching issues
            const finalOptions = {
                ...options,
                headers: {
                    ...options.headers,
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            };

            // Force HTTP if we're in development/localhost
            const finalUrl = window.location.hostname === 'localhost' 
                ? url.replace('https://', 'http://') 
                : url;

            const response = await fetch(finalUrl, finalOptions);
            
            // Check if we got an HTML response (usually error pages)
            let responseText = '';
            const respContentType = response.headers.get('content-type');
            if (respContentType && respContentType.includes('text/html')) {
                throw new Error('Received HTML response instead of JSON');
            }

            if (!response.ok) {
                // Try to get error details from response
                let errorMessage = `HTTP error! status: ${response.status}`;
                try {
                    responseText = await response.text();
                    let parsedError;
                    try {
                        parsedError = JSON.parse(responseText);
                        errorMessage = parsedError.message || errorMessage;
                    } catch (e) {
                        // If it's not JSON, use the raw text if it's not too long
                        if (responseText.length < 100) errorMessage = responseText;
                    }
                } catch (e) {
                    // If we can't read the response, just use the status
                }
                throw new Error(errorMessage);
            }

            responseText = await response.text();
            if (!responseText) {
                return {}; // Empty response is okay
            }
            
            try {
                return JSON.parse(responseText);
            } catch (e) {
                console.error('Error parsing JSON response:', responseText);
                throw new Error('Invalid JSON response from server');
            }
        } catch (error) {
            console.error(`Attempt ${i + 1} failed:`, error);
            
            // Don't retry on 405 Method Not Allowed
            if (error.message.includes('405')) {
                throw error;
            }
            
            // On last retry, throw the error
            if (i === retries - 1) throw error;
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1))); // Exponential backoff
        }
    }
}

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
        displayBotResponse(`Procesando envío de email de confirmación...`);
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

// Initialize chatbot data from config
function inicializarDatosChatbot() {
    try {
        console.log('[CHATBOT_DEBUG] Initializing chatbot data from config:', window.chatbotConfig);
        
        // Initialize restaurant info
        window.chatbotState.restaurantInfo = {
            restaurantId: window.chatbotConfig.restaurantId || '',
            restaurantName: window.chatbotConfig.restaurantName || 'Restaurante',
            address: window.chatbotConfig.address || '',
            contactPhone: window.chatbotConfig.contactPhone || '',
            contactWhatsapp: window.chatbotConfig.contactWhatsapp || '',
            openingHours: window.chatbotConfig.openingHours || {}
        };

        // Initialize menu info
        window.chatbotState.menuInfo = window.chatbotConfig.menuData || {};

        // Initialize opening hours with defaults if not provided
        window.chatbotState.openingHours = window.chatbotConfig.openingHours || {
            lunes: { open: "12:00", close: "23:00" },
            martes: { open: "12:00", close: "23:00" },
            miercoles: { open: "12:00", close: "23:00" },
            jueves: { open: "12:00", close: "23:00" },
            viernes: { open: "12:00", close: "23:00" },
            sabado: { open: "12:00", close: "23:00" },
            domingo: { open: "12:00", close: "23:00" }
        };

        console.log('[CHATBOT_INFO] Chatbot data initialized successfully');
        return true;
    } catch (error) {
        console.error('[CHATBOT_ERROR] Failed to initialize chatbot data:', error);
        return false;
    }
}