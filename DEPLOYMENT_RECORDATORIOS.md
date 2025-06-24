# 🚀 Instrucciones de Deployment del Sistema de Recordatorios

## 📋 Resumen del Sistema

El sistema de recordatorios automáticos está **COMPLETAMENTE CONFIGURADO** y listo para deployment en Render. Envía recordatorios por WhatsApp 24 horas antes de las reservas, usando la zona horaria de Argentina (GMT-3).

## ✅ Estado Actual del Sistema

### ✅ Scripts Implementados:
- `scripts/send_reminders.py` - Script principal de envío de recordatorios
- `scripts/check_reminder_system.py` - Verificación diaria del sistema  
- `scripts/test_reminders_system.py` - Testing interactivo
- `scripts/test_automated.py` - Testing automatizado

### ✅ Configuración de Render:
- **3 Cron Jobs** configurados en `render.yaml`:
  - 09:00 AM Argentina: Verificación del sistema
  - 10:00 AM Argentina: Envío principal de recordatorios
  - 14:00 PM Argentina: Envío de respaldo
- Zona horaria Argentina configurada (`TZ=America/Argentina/Buenos_Aires`)
- Python 3.11 con todas las dependencias

### ✅ Base de Datos:
- Integración completa con Supabase vía MCP
- Tabla `reservas` con campos para recordatorios
- Lógica de "mañana" basada en zona horaria Argentina

### ✅ WhatsApp/Twilio:
- Envío de mensajes con botones interactivos
- Manejo de respuestas (confirmar/cancelar)
- Formato de números argentinos (+549...)

## 🚀 Pasos para el Deployment en Render

### 1. Verificar Variables de Entorno

Asegúrate de que estas variables estén configuradas en Render:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_ENABLED=true
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+your_number
TZ=America/Argentina/Buenos_Aires
```

### 2. Deployment Automático

El sistema está configurado para **deployment automático**. Simplemente:

```bash
git add .
git commit -m "Deploy sistema de recordatorios completo"
git push origin main
```

### 3. Verificar Deployment

Una vez deployado, los siguientes servicios se crearán automáticamente:

1. **`gandolfo-restaurant`** (Web Service)
2. **`daily-system-check`** (Cron - 09:00 AM Argentina)
3. **`daily-reminders-morning`** (Cron - 10:00 AM Argentina)  
4. **`daily-reminders-backup`** (Cron - 14:00 PM Argentina)

### 4. Monitoreo Post-Deployment

```bash
# Ver logs de verificación diaria
render logs --service=daily-system-check

# Ver logs de envío de recordatorios
render logs --service=daily-reminders-morning

# Ver todos los servicios
render services list
```

## 🧪 Testing del Sistema

### Prueba Local (Antes del Deploy):

```bash
# Prueba automatizada completa
python3 scripts/test_automated.py

# Verificación del sistema
python3 scripts/check_reminder_system.py

# Testing interactivo
python3 scripts/test_reminders_system.py
```

### Prueba en Producción:

1. **Crear Reserva de Prueba**:
   ```sql
   INSERT INTO reservas (nombre, fecha, hora, telefono, personas, estado, recordatorio_enviado)
   VALUES ('Test Cliente', '2025-06-11', '20:00', '1166686255', 2, 'Confirmada', false);
   ```

2. **Ejecutar Manualmente**:
   ```bash
   # En Render Console o trigger manual
   python3 scripts/send_reminders.py
   ```

3. **Verificar Logs**:
   - Comprobar que se envió el WhatsApp
   - Verificar que se marcó `recordatorio_enviado = true`
   - Confirmar que se guardó la sesión para respuestas

## ⏰ Horarios de Ejecución

| Horario Argentina | UTC | Cron Job | Función |
|------------------|-----|----------|---------|
| 09:00 AM | 12:00 | `daily-system-check` | Verificación del sistema |
| 10:00 AM | 13:00 | `daily-reminders-morning` | Envío principal |
| 14:00 PM | 17:00 | `daily-reminders-backup` | Envío de respaldo |

## 📱 Funcionamiento del Sistema

### Flujo Diario:

1. **09:00 AM** - Sistema verifica:
   - Variables de entorno ✅
   - Conexión Supabase ✅  
   - Conexión Twilio ✅
   - Reservas para mañana 📊

2. **10:00 AM** - Envío principal:
   - Busca reservas para mañana sin recordatorio
   - Envía WhatsApp con botones interactivos
   - Marca reservas como `recordatorio_enviado = true`
   - Guarda sesiones para manejar respuestas

3. **14:00 PM** - Envío de respaldo:
   - Procesa reservas que no se enviaron en la mañana
   - Asegura que no se pierda ningún recordatorio

### Mensaje de Recordatorio:

```
¡Hola [NOMBRE]! 👋

Te recordamos tu reserva para mañana en Gandolfo Restaurant:

📅 *Fecha:* [DD/MM/YYYY]
🕒 *Hora:* [HH:MM] hs
👥 *Personas:* [CANTIDAD]

Responde con *1* para CONFIRMAR o *2* para CANCELAR tu reserva.

¡Te esperamos! 🍽️
```

## 🔧 Mantenimiento y Monitoreo

### Logs Importantes:

- `logs/reminders.log` - Envío de recordatorios
- `logs/system_check.log` - Verificaciones diarias
- `logs/system_check_YYYYMMDD.json` - Reportes en JSON

### Comandos de Diagnóstico:

```bash
# Ver reservas próximas
python3 scripts/test_reminders_system.py

# Verificar estado del sistema
python3 scripts/check_reminder_system.py

# Crear reserva de prueba
python3 scripts/test_reminders_system.py
```

### Solución de Problemas:

1. **No se envían recordatorios**:
   - Verificar variables de entorno en Render
   - Revisar logs de Twilio
   - Comprobar formato de números telefónicos

2. **Recordatorios duplicados**:
   - Verificar campo `recordatorio_enviado` en BD
   - Revisar horarios de cron

3. **Error de zona horaria**:
   - Confirmar variable `TZ=America/Argentina/Buenos_Aires`
   - Verificar cálculo de fecha "mañana"

## 📊 Métricas de Éxito

El sistema está **LISTO PARA PRODUCCIÓN** cuando:

- ✅ Todas las variables de entorno configuradas
- ✅ Conexiones Supabase y Twilio funcionales  
- ✅ Cron jobs desplegados y programados
- ✅ Pruebas de envío exitosas
- ✅ Logs funcionando correctamente
- ✅ Respuestas interactivas operativas

## 🎯 Próximos Pasos

1. **Deploy inmediato**: El sistema está listo para producción
2. **Monitoreo**: Revisar logs durante los primeros días
3. **Optimización**: Ajustar horarios si es necesario
4. **Escalabilidad**: Considerar múltiples restaurantes

---

**🎉 EL SISTEMA ESTÁ COMPLETAMENTE LISTO PARA DEPLOYMENT**

*Desarrollado para Gandolfo Restaurant - Junio 2025*
