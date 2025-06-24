# Sistema de Recordatorios Automáticos

Este documento describe el sistema de recordatorios automáticos para reservas de restaurante que se ejecuta en Render.

## 📋 Descripción General

El sistema envía recordatorios automáticos por WhatsApp a los clientes 24 horas antes de su reserva, utilizando la zona horaria de Argentina (GMT-3) para determinar correctamente "mañana".

## 🕒 Horarios de Ejecución

### Cron Jobs Configurados en Render:

1. **Verificación del Sistema** - `daily-system-check`
   - **Horario**: 9:00 AM Argentina (12:00 UTC)
   - **Función**: Verifica que el sistema esté listo antes del envío
   - **Script**: `scripts/check_reminder_system.py`

2. **Envío Principal** - `daily-reminders-morning`
   - **Horario**: 10:00 AM Argentina (13:00 UTC)
   - **Función**: Envío principal de recordatorios
   - **Script**: `scripts/send_reminders.py`

3. **Envío de Respaldo** - `daily-reminders-backup`
   - **Horario**: 2:00 PM Argentina (17:00 UTC)
   - **Función**: Envío de respaldo para reservas no procesadas
   - **Script**: `scripts/send_reminders.py`

## 🔧 Componentes del Sistema

### Scripts Principales:

1. **`scripts/send_reminders.py`** - Script principal de envío
2. **`scripts/check_reminder_system.py`** - Verificación del sistema
3. **`scripts/test_reminders_system.py`** - Testing y debugging

### Servicios:

1. **`services/recordatorio_service.py`** - Lógica de recordatorios
2. **`services/twilio/messaging.py`** - Envío de WhatsApp
3. **`utils/session_manager.py`** - Manejo de sesiones para respuestas

## 📊 Flujo de Trabajo

```
09:00 AM → Verificación del Sistema
           ├── Verifica variables de entorno
           ├── Prueba conexión Supabase
           ├── Prueba conexión Twilio
           ├── Analiza reservas para mañana
           └── Genera reporte de estado

10:00 AM → Envío Principal de Recordatorios
           ├── Calcula fecha "mañana" en zona Argentina
           ├── Busca reservas activas sin recordatorio
           ├── Envía WhatsApp con botones interactivos
           ├── Guarda sesión para respuestas
           └── Marca reserva como recordatorio enviado

14:00 PM → Envío de Respaldo (solo si hay pendientes)
```

## 🗄️ Base de Datos

### Tabla: `reservas`

Campos relevantes para recordatorios:
- `fecha`: Fecha de la reserva (YYYY-MM-DD)
- `hora`: Hora de la reserva (HH:MM)
- `nombre`: Nombre del cliente titular
- `telefono`: Teléfono del cliente (formato WhatsApp)
- `recordatorio_enviado`: Boolean indicando si se envió recordatorio
- `fecha_recordatorio`: Timestamp del envío del recordatorio
- `estado`: Estado de la reserva (activa/cancelada/etc.)

### Consulta Principal:

```sql
SELECT * FROM reservas 
WHERE fecha = 'FECHA_MAÑANA' 
  AND recordatorio_enviado = false 
  AND estado NOT IN ('Cancelada', 'No asistió')
```

## 📱 Mensaje de Recordatorio

### Formato del Mensaje:

```
¡Hola [NOMBRE]! 👋

Te recordamos tu reserva para mañana en [RESTAURANTE]:

📅 *Fecha:* [DD/MM/YYYY]
🕒 *Hora:* [HH:MM] hs
👥 *Personas:* [CANTIDAD]

Responde con *1* para CONFIRMAR o *2* para CANCELAR tu reserva.

¡Te esperamos! 🍽️
```

### Respuestas Interactivas:

- **"1"** → Confirma la reserva
- **"2"** → Cancela la reserva
- Otras respuestas → Información adicional

## 🔒 Variables de Entorno Requeridas

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_ENABLED=true

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+your_number

# Configuración
TZ=America/Argentina/Buenos_Aires
TEST_MODE=false
```

## 🧪 Testing y Debugging

### Script de Pruebas:

```bash
python3 scripts/test_reminders_system.py
```

**Opciones del menú:**
1. Verificar configuración
2. Mostrar reservas próximas
3. Crear reserva de prueba para mañana
4. Probar sistema de recordatorios
5. Eliminar reservas de prueba
6. Prueba completa

### Logs del Sistema:

- **`logs/reminders.log`** - Logs del envío de recordatorios
- **`logs/system_check.log`** - Logs de verificación del sistema
- **`logs/system_check_YYYYMMDD.json`** - Reportes diarios en JSON

### Modo de Prueba:

```bash
export TEST_MODE=true
python3 scripts/send_reminders.py
```

## 🚨 Monitoreo y Alertas

### Indicadores de Salud:

1. **Variables de Entorno** ✅/❌
2. **Conexión Supabase** ✅/❌
3. **Conexión Twilio** ✅/❌
4. **Reservas Detectadas** 📊
5. **Problemas en Datos** ⚠️

### Estados del Sistema:

- **OK**: Todo funcionando correctamente
- **WARNING**: Funcional pero con alertas menores
- **ERROR**: Requiere intervención inmediata

### Verificación Manual:

```bash
# Verificar sistema
python3 scripts/check_reminder_system.py

# Enviar recordatorios manualmente
python3 scripts/send_reminders.py

# Ver logs en tiempo real
tail -f logs/reminders.log
```

## 📈 Mejoras Futuras

### Implementadas:
- ✅ Zona horaria correcta (Argentina GMT-3)
- ✅ Validación de datos antes del envío
- ✅ Manejo robusto de errores
- ✅ Logs detallados para debugging
- ✅ Sistema de verificación preventiva
- ✅ Envío de respaldo automático
- ✅ Botones interactivos en WhatsApp

### Propuestas:
- 📧 Notificaciones por email en caso de errores
- 📊 Dashboard web para monitoreo
- 🔄 Reintentos automáticos con backoff
- 📱 Integración con Telegram como backup
- 🤖 IA para personalizar mensajes

## 🐛 Troubleshooting

### Problemas Comunes:

1. **"No se envían recordatorios"**
   - Verificar variables de entorno
   - Verificar conexión Twilio/Supabase
   - Verificar formato de números de teléfono

2. **"Recordatorios duplicados"**
   - Verificar campo `recordatorio_enviado`
   - Verificar horarios de cron

3. **"Error de zona horaria"**
   - Verificar variable `TZ`
   - Verificar cálculo de "mañana"

4. **"Números no válidos"**
   - Verificar formato argentino (+549...)
   - Verificar prefijo WhatsApp

### Comandos de Diagnóstico:

```bash
# Ver estado de cron jobs en Render
render services list

# Ver logs de cron específico
render logs --service=daily-reminders-morning

# Probar conexiones
python3 scripts/check_reminder_system.py

# Crear reserva de prueba
python3 scripts/test_reminders_system.py
```

## 🔄 Deployment en Render

### Archivo de Configuración: `render.yaml`

El sistema está configurado para desplegarse automáticamente en Render con:
- 3 cron jobs programados
- Variables de entorno sincronizadas
- Zona horaria configurada
- Python 3.11 con dependencias automáticas

### Comandos de Deploy:

1. **Git Push**: El deploy es automático al hacer push a la rama principal
2. **Manual**: A través del dashboard de Render
3. **Blueprint**: Usando el archivo `render.yaml`

---

*Última actualización: Junio 2025*
*Desarrollado para Gandolfo Restaurant*
