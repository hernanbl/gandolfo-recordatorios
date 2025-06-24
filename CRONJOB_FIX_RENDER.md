# 🚨 SOLUCIÓN PARA ERROR DE CRON JOB EN RENDER

## ❌ **Error Común:**
```
❌ Faltan las siguientes variables de entorno: SUPABASE_URL, SUPABASE_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
```

## 🔧 **Solución Paso a Paso:**

### 1. 🔍 **Acceder al Cron Job en Render**
1. Ve a tu dashboard de Render: https://dashboard.render.com
2. Busca el servicio **"daily-reminders-backup"** (tipo: Cron Job)
3. Click en el nombre del servicio para abrirlo

### 2. ⚙️ **Configurar Variables de Entorno**
1. En el menú lateral, click en **"Environment"**
2. Agrega **TODAS** estas variables (una por una):

```
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_key_de_supabase  
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_WHATSAPP_NUMBER=tu_numero_whatsapp
TZ=America/Argentina/Buenos_Aires
USE_PROD_TABLES=true
```

3. **NO agregar:** `DEFAULT_RESTAURANT_ID` (debe quedar vacío)
4. Click en **"Save Changes"**

### 3. ✅ **Verificar la Configuración**
1. Ve a la pestaña **"Logs"** del cron job
2. Click en **"Trigger Job"** para ejecutar manualmente
3. Verifica que ya no aparezca el error de variables faltantes

### 4. 📊 **Logs Esperados (cuando funcione):**
```
=== INICIANDO PROCESO DE RECORDATORIOS ===
✅ Todas las variables de entorno requeridas están presentes
🚀 Llamando al servicio de recordatorios...
=== RESUMEN FINAL ===
📊 Reservas encontradas para mañana: X
✅ Mensajes enviados exitosamente: X
🎉 PROCESO COMPLETADO CON ÉXITO
```

## 🛠️ **Script de Verificación**

Puedes usar este comando para verificar las variables antes del cron job:

```bash
python3 scripts/verify_env_vars.py
```

## 📱 **Horario de Ejecución**

El cron job se ejecuta automáticamente:
- ⏰ **Todos los días a las 10:00 AM (Argentina)**  
- 🌍 **Horario configurado:** `0 13 * * *` (UTC = 10:00 AM Argentina)

## 🔄 **¿Por qué pasa esto?**

Render maneja cada servicio de forma independiente:
- ✅ **Servicio Web:** Tiene sus propias variables de entorno
- ❌ **Cron Job:** Necesita sus **PROPIAS** variables de entorno (separadas)

**Solución:** Configurar las variables en **AMBOS** servicios.

## 📞 **¿Necesitas ayuda?**

1. 📖 Ver documentación completa: `VARIABLES_ENTORNO_RENDER_SAFE.md`
2. 🔍 Ejecutar verificación: `python3 scripts/verify_env_vars.py`
3. 📊 Revisar logs del cron job en Render

---

**¡Con estas variables configuradas, el sistema de recordatorios funcionará perfectamente!** 🚀
