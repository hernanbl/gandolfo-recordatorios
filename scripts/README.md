# Scripts de Recordatorios para Gandolfo Restaurant

Este directorio contiene los scripts necesarios para el sistema de recordatorios de reservas.

## Descripción de los Scripts

- `send_reminders.py`: Envía recordatorios de WhatsApp a clientes con reservas para el día siguiente.
- `check_reservations.py`: Verifica las reservas próximas y envía recordatorios para las que son en 24 horas.

## Configuración del Cron

Para que los recordatorios se envíen automáticamente, es necesario configurar tareas programadas (cron jobs). En el archivo `crontab.txt` en la raíz del proyecto se encuentra la configuración recomendada.

### Instalación del Cron

1. Asegúrate de estar en el directorio raíz del proyecto:
   ```
   cd /Volumes/AUDIO/gandolfo-restaurant-main
   ```

2. Instala la configuración del cron:
   ```
   crontab crontab.txt
   ```

3. Verifica que la configuración se haya instalado correctamente:
   ```
   crontab -l
   ```

## Ejecución Manual

También puedes ejecutar los scripts manualmente para probar su funcionamiento:

```bash
# Para enviar recordatorios de reservas para el día siguiente
python3 scripts/send_reminders.py

# Para verificar reservas próximas y enviar recordatorios
python3 scripts/check_reservations.py
```

## Logs

Los logs de ejecución se guardan en el directorio `logs/` en la raíz del proyecto:

- `reminders.log`: Log del script de envío de recordatorios
- `check_reservations.log`: Log del script de verificación de reservas
- `cron_reminders.log`: Log de la ejecución programada del script de recordatorios
- `cron_check_reservations.log`: Log de la ejecución programada del script de verificación

## Pruebas

Para probar el sistema de recordatorios, puedes utilizar el script `test_reminder_confirmation.py` en la raíz del proyecto:

```bash
python3 test_reminder_confirmation.py
```

Este script permite probar tanto el envío de recordatorios como la confirmación de reservas.