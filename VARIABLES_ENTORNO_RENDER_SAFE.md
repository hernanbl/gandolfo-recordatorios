# 🔑 VARIABLES DE ENTORNO PARA RENDER - MULTI RESTAURANTE

## 📋 VARIABLES REQUERIDAS EN RENDER

Agrega estas variables en **TODOS LOS SERVICIOS** de Render:
- ✅ **Servicio Web Principal** 
- ✅ **Cron Job "daily-reminders-backup"**
- ✅ **Cualquier otro servicio adicional**

### 🗄️ **Supabase (Base de Datos)**
```
SUPABASE_URL=YOUR_SUPABASE_PROJECT_URL
SUPABASE_KEY=YOUR_SUPABASE_ANON_KEY
```

### 📱 **Twilio (WhatsApp)**
```
TWILIO_ACCOUNT_SID=YOUR_TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN=YOUR_TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_NUMBER=YOUR_TWILIO_WHATSAPP_NUMBER
```

### ⚙️ **Sistema Multi-Restaurante**
```
TZ=America/Argentina/Buenos_Aires
USE_PROD_TABLES=true
DEFAULT_RESTAURANT_NAME=Plataforma Multi-Restaurante
```

### 🚨 **IMPORTANTE - NO AGREGAR DEFAULT_RESTAURANT_ID**

**NO agregues `DEFAULT_RESTAURANT_ID`** - Déjalo vacío o no lo configures.

Esto permitirá que el sistema:
- ✅ Procese **TODOS los restaurantes** automáticamente
- ✅ Envíe recordatorios para **Gandolfo, Ostende, y cualquier otro restaurante**
- ✅ Funcione como plataforma multi-restaurante

## 🔧 **CONFIGURACIÓN ESPECÍFICA PARA CRON JOB**

**⚠️ MUY IMPORTANTE:** El cron job "daily-reminders-backup" necesita las **MISMAS variables** que el servicio web.

### 📝 **Pasos para configurar el Cron Job:**

1. 🔍 Ve a tu dashboard de Render
2. 🔎 Busca el servicio "daily-reminders-backup" (Cron Job)
3. ⚙️ Ve a "Environment" en el menú lateral
4. ➕ Agrega **TODAS** las variables listadas arriba
5. 💾 Guarda los cambios
6. 🔄 El cron job se actualizará automáticamente

**Sin estas variables, el cron job fallará con error:**
```
❌ Faltan las siguientes variables de entorno: SUPABASE_URL, SUPABASE_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
```

## 🎯 **FUNCIONAMIENTO MULTI-RESTAURANTE**

**Todos los días a las 10:00 AM Argentina**, el sistema:

1. 🔍 Busca reservas en **TODOS los restaurantes** para mañana
2. 📱 Envía WhatsApp personalizado con el **nombre de cada restaurante**
3. ✅ Marca `recordatorio_enviado = true` para evitar duplicados
4. 📊 Genera logs detallados de cada restaurante procesado

### 📱 **Ejemplo de Mensaje:**
```
¡Hola Juan! 👋

Te recordamos tu reserva para mañana en Gandolfo Restaurant:

📅 *Fecha:* 11/06/2025
🕒 *Hora:* 20:00 hs
👥 *Personas:* 4

Responde con *1* para CONFIRMAR o *2* para CANCELAR tu reserva.

¡Te esperamos! 🍽️
```

## 🔧 **CONFIGURACIÓN DE ARCHIVOS JSON**

Los archivos de configuración de restaurantes usan placeholders que se reemplazan automáticamente con variables de entorno:

- `PHONE_FROM_ENV` → Se reemplaza con número real en producción
- `EMAIL_FROM_ENV` → Se reemplaza con email real en producción  
- `WHATSAPP_FROM_ENV` → Se reemplaza con WhatsApp real en producción
- `TWILIO_*_FROM_ENV` → Se reemplazan con credenciales reales en producción

## ✅ **PRÓXIMO PASO**

Con estas variables configuradas en **TODOS los servicios** de Render (incluyendo el cron job), el sistema funcionará automáticamente para **TODOS los restaurantes** de tu plataforma.

### 🔍 **Verificar que el Cron Job funcione:**

1. ✅ Configura las variables en el cron job "daily-reminders-backup"
2. 🔄 Espera la próxima ejecución automática (10:00 AM Argentina)
3. 📊 O ejecuta manualmente para probar:
   - Ve al cron job en Render
   - Click en "Trigger Job" para ejecutar ahora
   - Revisa los logs para confirmar que no hay errores

### 📱 **Logs esperados cuando funcione correctamente:**
```
=== INICIANDO PROCESO DE RECORDATORIOS ===
✅ Todas las variables de entorno requeridas están presentes
🚀 Llamando al servicio de recordatorios...
=== RESUMEN FINAL ===
📊 Reservas encontradas para mañana: X
✅ Mensajes enviados exitosamente: X
🎉 PROCESO COMPLETADO CON ÉXITO
```

### 🚨 **¿El cron job sigue fallando?**

📖 **Ver solución completa:** [`CRONJOB_FIX_RENDER.md`](./CRONJOB_FIX_RENDER.md)

🔍 **Verificar variables:** `python3 scripts/verify_env_vars.py`

---

**¡Perfecto para plataforma multi-restaurante!** 🚀