# 🔧 SOLUCIÓN: Usar Número de Sandbox de Twilio

## 🚨 Problema Identificado

Estás usando el número de **producción** `+18059093442` cuando aún estás en **modo sandbox** de Twilio WhatsApp.

## ✅ Solución: Cambiar a Número de Sandbox

Necesitas actualizar la variable de entorno en Render para usar el número de sandbox:

### 📱 Número Correcto para Sandbox
```
TWILIO_WHATSAPP_NUMBER=+14155238886
```

## 🔧 Pasos para Actualizar en Render

### 1. Actualizar Servicio Web Principal
1. Ve a tu **Dashboard de Render**
2. Selecciona tu **servicio web principal**
3. Ve a **Environment** en el menú lateral
4. Busca la variable `TWILIO_WHATSAPP_NUMBER`
5. Cambia el valor de `+18059093442` a `+14155238886`
6. Haz clic en **Save Changes**

### 2. Actualizar Cron Job de Recordatorios
1. En tu Dashboard de Render
2. Selecciona el **cron job "daily-reminders-backup"**
3. Ve a **Environment** en el menú lateral
4. Busca la variable `TWILIO_WHATSAPP_NUMBER`
5. Cambia el valor de `+18059093442` a `+14155238886`
6. Haz clic en **Save Changes**

### 3. Redeployar Servicios
Después de cambiar las variables:
1. **Redeploy** el servicio web
2. **Redeploy** el cron job
3. Espera a que ambos servicios se actualicen

## 🧪 Verificar la Configuración

### Ejecutar Diagnóstico
```bash
# En Render o localmente
python3 scripts/diagnostico_completo.py
```

### Probar Envío de Recordatorio
```bash
# Probar el sistema de recordatorios
python3 scripts/send_reminders.py
```

## 📋 Configuración Completa para Sandbox

En Render, asegúrate de tener estas variables configuradas:

```bash
# Twilio Sandbox Configuration
TWILIO_ACCOUNT_SID=AC...tu_account_sid
TWILIO_AUTH_TOKEN=...tu_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886

# Otras variables (sin cambios)
SUPABASE_URL=...
SUPABASE_KEY=...
TZ=America/Argentina/Buenos_Aires
USE_PROD_TABLES=true
```

## 📱 Importante: Configuración del Sandbox

### Para que funcione el sandbox de WhatsApp:

1. **El número de destino** (el cliente) debe estar registrado en el sandbox
2. **El cliente debe enviar** el código de sandbox a `+14155238886` primero
3. **Código de sandbox**: `join <code>` (ej: `join happy-cat`)

### Mensaje que debe enviar el cliente:
```
join happy-cat
```
*(El código específico lo encuentras en Twilio Console > Messaging > Try it out > Send a WhatsApp message)*

## 🚀 Migración a Producción (Futuro)

Cuando tengas WhatsApp Business aprobado:

1. Cambiar `TWILIO_WHATSAPP_NUMBER` de `+14155238886` a `+18059093442`
2. Ya no será necesario el registro en sandbox
3. Los clientes podrán recibir mensajes directamente

## ⚡ Solución Rápida

**Para solucionar AHORA:**

1. Ve a Render → Tu servicio web → Environment
2. Cambia `TWILIO_WHATSAPP_NUMBER=+18059093442` por `TWILIO_WHATSAPP_NUMBER=+14155238886`
3. Haz lo mismo en el cron job
4. Redeploy ambos servicios
5. Ejecuta: `python3 scripts/send_reminders.py`

## 🎯 Verificación Final

Después de hacer los cambios, el log debería mostrar:
```
Enviando mensaje WhatsApp desde: whatsapp:+14155238886 hacia: whatsapp:+549...
```

¡Y los mensajes deberían enviarse exitosamente! 🎉
