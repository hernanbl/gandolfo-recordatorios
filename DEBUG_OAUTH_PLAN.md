## 🐛 PLAN DE DEBUG OAUTH - REDIRECT LOCALHOST

### 📋 PROBLEMA CONFIRMADO
- **LOCAL**: OAuth funciona perfectamente → va a localhost:5000
- **PRODUCCIÓN**: OAuth redirige incorrectamente → va a localhost:5000 
- **EXPECTATIVA**: En producción debería ir a gandolfo.app/admin/auth/callback

### 🔍 HIPÓTESIS PRINCIPAL
El problema NO está en Supabase (funciona igual local y prod), está en la **detección de entorno en JavaScript**.

### 📱 PLAN DE TESTING

#### PASO 1: Verificar Logs en Producción
1. Ir a https://gandolfo.app/admin/login
2. Abrir DevTools → Console
3. Hacer clic en "Continuar con Google"
4. **BUSCAR EN CONSOLE:**
   ```
   🌐 DEBUG - Información de entorno:
      hostname: [VALOR]
      protocol: [VALOR]
      origin: [VALOR]
      href: [VALOR]
   
   🔍 DEBUG - Detección de entorno:
      isGandolfoApp: [VALOR]
      isRenderDomain: [VALOR]
      isLocalhost: [VALOR]
      isProduction: [VALOR]
   
   🎯 Redirect URL configurada: [VALOR]
   🚨 CRITICAL - Esta URL se enviará a Supabase OAuth: [VALOR]
   ```

#### PASO 2: Analizar Resultados
- **SI `isGandolfoApp: true`** → El problema está en otro lado
- **SI `isGandolfoApp: false`** → La detección de hostname está fallando
- **VERIFICAR** que `redirectUrl` sea exactamente `https://gandolfo.app/admin/auth/callback`

#### PASO 3: Posibles Causas y Soluciones

**CAUSA A: Hostname no se detecta como gandolfo.app**
- Puede ser un proxy/CDN cambiando el hostname
- **SOLUCIÓN**: Hardcodear para HTTPS y no localhost

**CAUSA B: Supabase está usando configuración cached/incorrecta**
- **SOLUCIÓN**: Verificar Dashboard de Supabase nuevamente

**CAUSA C: Hay algún middleware/proxy interceptando**
- **SOLUCIÓN**: Verificar headers y configuración de Render

### 🎯 PRÓXIMOS PASOS

1. **DEPLOY** → Confirmar que el commit se deployó
2. **TEST** → Ejecutar el plan de testing arriba
3. **ANALYZE** → Revisar logs del console
4. **FIX** → Aplicar la corrección específica basada en los logs

### 📞 INSTRUCCIONES PARA USUARIO

**Ve a https://gandolfo.app/admin/login ahora:**
1. Abre DevTools (F12) → tab Console
2. Haz clic en "Continuar con Google"
3. **COPIA TODOS LOS LOGS** que empiecen con 🌐, 🔍, 🎯, 🚨
4. **REPORTA** exactamente qué URL te abre (localhost vs gandolfo.app)

Con esa información podremos identificar exactamente dónde está el problema.
