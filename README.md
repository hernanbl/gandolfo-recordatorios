# Sistema de Gestión de Restaurantes - WhatsApp Bot

Sistema avanzado de gestión de reservas y comunicación por WhatsApp para múltiples restaurantes con IA integrada.

## Características Principales

- 🤖 **Bot inteligente de WhatsApp** con procesamiento de lenguaje natural
- 📅 **Gestión completa de reservas** con confirmaciones automáticas
- ⏰ **Recordatorios automáticos** personalizados por WhatsApp
- 📋 **Sistema de políticas dinámico** (mascotas, niños, fumar, estacionamiento, etc.)
- 🌟 **Sistema de feedback** para recolectar opiniones de clientes
- 👤 **Reconocimiento de usuarios** conocidos con saludos personalizados
- 🏢 **Multi-restaurante** con configuraciones independientes
- 🛡️ **Panel de administración** completo con autenticación
- 🔗 **Integración con Supabase** para almacenamiento en la nube
- 🧠 **IA conversacional** con DeepSeek para consultas generales

## Funcionalidades del Bot de WhatsApp

### 🎯 Detección Inteligente de Intenciones
El bot utiliza un sistema de prioridades para procesar mensajes:

1. **Detección de Feedback** - Calificaciones y opiniones de clientes
2. **Consultas sobre Políticas** - Información sobre mascotas, niños, fumar, etc.
3. **Consultas de Menú** - Información sobre platos y especialidades  
4. **Información de Ubicación** - Direcciones y cómo llegar
5. **Sistema de Reservas** - Procesamiento inteligente de datos de reserva
6. **IA Conversacional** - Para consultas generales

### 📋 Sistema de Políticas Dinámico
**TODAS las políticas se leen dinámicamente del JSON de cada restaurante:**

- 🐕 **Mascotas**: Políticas específicas por restaurante
- 👶 **Niños**: Menú infantil y servicios familiares
- 🚬 **Fumar**: Permisos interior/exterior por establecimiento
- ♿ **Accesibilidad**: Información sobre sillas de ruedas y braille
- 🌱 **Dietas especiales**: Opciones vegetarianas, veganas, sin gluten
- 🚗 **Estacionamiento**: Disponibilidad y tipo de parking
- 👔 **Vestimenta**: Códigos de vestimenta específicos
- 📅 **Cancelaciones**: Políticas de modificación y cancelación

### 👤 Reconocimiento de Usuarios
- Identifica automáticamente usuarios conocidos por su número de teléfono
- Ofrece saludos personalizados usando nombres previos
- Permite saltear pasos en el proceso de reserva
- Rellena automáticamente datos conocidos (nombre, email)

### 🌟 Sistema de Feedback
- Detección automática de feedback y calificaciones (1-5 estrellas)
- Solicitud automática de opiniones tras confirmación de reserva
- Almacenamiento organizado en Supabase para análisis

## Estructura del Proyecto

```
├── app.py                  # Aplicación principal Flask
├── config.py               # Configuración global de la aplicación
├── services/               # Servicios principales
│   ├── db/                 # Conexión a bases de datos
│   │   └── supabase_client.py # Cliente Supabase
│   ├── twilio/             # Servicios de WhatsApp/Twilio
│   │   ├── messaging.py    # Envío de mensajes
│   │   ├── handler.py      # Procesador principal de mensajes (IA + Políticas)
│   │   ├── reservation_handler.py # Lógica de reservas
│   │   └── utils.py        # Utilidades de WhatsApp
│   ├── ai/                 # Servicios de Inteligencia Artificial
│   │   └── deepseek_service.py # Integración con DeepSeek AI
│   └── recordatorio_service.py # Servicio de recordatorios automáticos
├── routes/                 # Rutas y controladores web
│   ├── admin_routes.py     # Panel de administración
│   ├── twilio_routes.py    # Webhooks de Twilio/WhatsApp
│   └── webhook_routes.py   # Webhooks de recordatorios
├── models/                 # Modelos de datos
│   ├── reserva.py         # Modelo de reserva
│   └── conversation.py    # Modelo de conversación
├── templates/              # Templates HTML para admin
├── scripts/                # Scripts de automatización
│   ├── send_reminders.py   # Cron job: Envío diario de recordatorios
│   └── check_reservations.py # Verificación horaria de reservas
├── data/                   # Datos de configuración por restaurante
│   ├── info/              # Archivos JSON con información de cada restaurante
│   ├── menus/             # Menús específicos por restaurante
│   └── sessions/          # Sesiones activas de usuarios
└── render.yaml            # Configuración para deployment en Render
```

## Configuración por Restaurante

### Archivos de Información (`data/info/`)
Cada restaurante tiene su archivo JSON con configuración completa:

```json
{
  "name": "Nombre del Restaurante",
  "description": "Descripción del establecimiento",
  "location": {
    "address": "Dirección completa",
    "google_maps_link": "URL de Google Maps"
  },
  "contact": {
    "phone": "Número de contacto",
    "email": "email@restaurante.com"
  },
  "policies": {
    "pets": {
      "allowed": true,
      "restrictions": "Solo en terraza",
      "description": "Política detallada..."
    },
    "smoking": {
      "allowed": false,
      "outdoor_allowed": true,
      "description": "Política específica..."
    },
    "children": {
      "allowed": true,
      "amenities": ["menú infantil", "sillas altas"]
    }
    // ... más políticas
  }
}
```

## Tareas Programadas (Cron Jobs)

El sistema utiliza dos tareas programadas principales:

1. **Envío diario de recordatorios**: Se ejecuta todos los días a las 10:00 AM UTC para enviar recordatorios de reservas programadas para el día siguiente.
   
2. **Verificación horaria de reservas**: Se ejecuta cada hora para verificar reservas próximas y enviar recordatorios adicionales si es necesario.

## Despliegue en Render

### Configuración Automática
El proyecto incluye `render.yaml` con configuración completa:

```yaml
services:
  - type: web
    name: gandolfo-bot
    plan: free
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python run.py
    
  - type: cron
    name: daily-reminders  
    schedule: "0 10 * * *"  # 10:00 AM UTC diariamente
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/send_reminders.py
```

### Despliegue
1. Conectar repositorio de GitHub a Render
2. Crear nuevo "Blueprint" en Render  
3. Seleccionar este repositorio
4. Configurar variables de entorno (ver lista arriba)
5. Deploy automático desde `render.yaml`

Los **cron jobs** se crearán automáticamente para recordatorios.

## Variables de Entorno Requeridas

### Supabase
- `SUPABASE_URL`: URL del proyecto Supabase
- `SUPABASE_KEY`: Clave API de Supabase  
- `SUPABASE_ENABLED`: true para habilitar conexión

### Twilio/WhatsApp
- `TWILIO_ACCOUNT_SID`: SID de cuenta Twilio
- `TWILIO_AUTH_TOKEN`: Token de autenticación
- `TWILIO_WHATSAPP_NUMBER`: Número WhatsApp Business (ej. +14155238886)

### IA y Servicios
- `DEEPSEEK_API_KEY`: Clave API para DeepSeek AI
- `SECRET_KEY`: Clave secreta para sesiones Flask

### Configuración
- `DEBUG`: true/false para modo de desarrollo
- `PORT`: Puerto de la aplicación (default: 5000)

## Funcionalidades Técnicas Avanzadas

### 🧠 Procesamiento Inteligente de Mensajes
- **Parser de reservas** con IA que extrae fecha, hora y cantidad de personas
- **Detección de intenciones** con sistema de prioridades
- **Interrupciones inteligentes** del flujo de reserva
- **Validación automática** de disponibilidad y capacidad

### 🔄 Estados de Reserva
- `INICIO` → `ESPERANDO_FECHA` → `ESPERANDO_PERSONAS` → `ESPERANDO_NOMBRE` → `CONFIRMADA` → `COMPLETADA`
- Manejo de **interrupciones** y **comandos de ayuda** en cualquier estado
- **Limpieza automática** de sesiones expiradas
- **Manejo de interrupciones** en cualquier estado
- **Rollback** ante errores de procesamiento

### 📱 Integración WhatsApp/Twilio
- Webhooks seguros con validación de origen
- Soporte para **mensajes de texto** y **respuestas de botones**
- **Retry automático** en caso de fallos de envío
- Logs detallados para debugging

### 🗄️ Base de Datos (Supabase)
```sql
-- Tabla principal de reservas
reservas_prod (
  id, restaurante_id, cliente_telefono, nombre_cliente,
  fecha_reserva, hora_reserva, cantidad_personas,
  estado, fecha_creacion, confirmado_por_cliente
)

-- Tabla de feedback
feedback (
  id, restaurante_id, cliente_telefono, comentario,
  puntuacion, fecha_feedback, reserva_id
)
```

## Desarrollo Local

### Configuración Inicial
```bash
# Clonar repositorio
git clone https://github.com/hernanbl/gandolfo-recordatorios.git
cd gandolfo-recordatorios

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de configuración
cp .env.example .env
# Editar .env con tus variables de entorno
```

### Ejecución Local
```bash
# Desarrollo con recarga automática
python run.py

# O usando Flask directamente
flask run --debug

# Para testing sin Supabase
export SUPABASE_ENABLED=false
python run.py
```

### Testing del Bot
```bash
# Configurar webhook de Twilio para testing local
# Usar ngrok para exponer puerto local:
ngrok http 5000

# URL del webhook en Twilio:
# https://tu-ngrok-url.ngrok.io/webhook/whatsapp
```

## Despliegue en Render

### Configuración Automática
El proyecto incluye `render.yaml` con configuración completa:

```yaml
services:
  - type: web
    name: gandolfo-bot
    plan: free
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python run.py
    
  - type: cron
    name: daily-reminders  
    schedule: "0 10 * * *"  # 10:00 AM UTC diariamente
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/send_reminders.py
```

### Despliegue
1. Conectar repositorio de GitHub a Render
2. Crear nuevo "Blueprint" en Render  
3. Seleccionar este repositorio
4. Configurar variables de entorno (ver lista arriba)
5. Deploy automático desde `render.yaml`

Los **cron jobs** se crearán automáticamente para recordatorios.

## Arquitectura y Flujo de Datos

### Flujo de Mensajes WhatsApp
```
WhatsApp → Twilio → Webhook → handler.py → 
  ├── Feedback Detection
  ├── Policy Queries  
  ├── Menu Queries
  ├── Location Queries
  ├── Reservation Flow
  └── AI Conversation
```

### Sistema de Prioridades
1. **Feedback** (máxima prioridad)
2. **Políticas** (interrumpe reservas)
3. **Menú** (específico)
4. **Ubicación** (específico)  
5. **Reservas** (intención explícita)
6. **IA General** (fallback)

### Gestión de Estados
- **Sesiones persistentes** en archivos JSON
- **Limpieza automática** de sesiones expiradas
- **Manejo de interrupciones** en cualquier estado
- **Rollback** ante errores de procesamiento

## Contribución

### Estructura de Commits
```bash
# Formato recomendado:
git commit -m "tipo: descripción breve

✅ CAMBIOS:
- Descripción detallada 1
- Descripción detallada 2

❌ FIXES:
- Problema resuelto 1
- Problema resuelto 2"
```

### Testing
```bash
# Ejecutar tests de integración
python -m pytest tests/

# Testing manual del bot (requiere configuración)
python scripts/test_bot_responses.py
```

---

## Changelog Reciente

### v2.1.0 - Sistema de Políticas Dinámico
- ✅ **Eliminado hardcode** de políticas del handler
- ✅ **Lectura dinámica** desde JSON por restaurante
- ✅ **Prioridades corregidas** - políticas antes que reservas
- ✅ **Interrupciones inteligentes** del flujo de reserva
- ✅ **Keywords expandidas** (fumar, estacionamiento, vestimenta)

### v2.0.0 - Reconocimiento de Usuarios  
- ✅ **Saludos personalizados** para usuarios conocidos
- ✅ **Autocompletado** de datos en reservas
- ✅ **Normalización avanzada** de números telefónicos
- ✅ **Sistema de feedback** automático post-reserva

---

**Desarrollado con ❤️ para la gestión inteligente de restaurantes**

<!-- Trigger deploy -->