// Script para interceptar redirects de localhost a gandolfo.app
// Agregar este código a la página de login o como script separado

(function() {
    // Interceptar si estamos en localhost con tokens OAuth
    if (window.location.hostname === 'localhost' && window.location.hash.includes('access_token')) {
        console.log('🔄 Interceptando redirect de localhost, redirigiendo a gandolfo.app...');
        
        // Extraer el hash completo con todos los parámetros
        const hashParams = window.location.hash;
        
        // Construir la URL correcta de producción
        const productionUrl = `https://gandolfo.app/admin/auth/callback${hashParams}`;
        
        console.log('🎯 Redirigiendo a:', productionUrl);
        
        // Redirigir inmediatamente
        window.location.href = productionUrl;
        
        return;
    }
})();

// Exportar para uso manual si es necesario
window.redirectToProduction = function() {
    if (window.location.hash.includes('access_token')) {
        const hashParams = window.location.hash;
        const productionUrl = `https://gandolfo.app/admin/auth/callback${hashParams}`;
        window.location.href = productionUrl;
    }
};
