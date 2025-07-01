import sys
import os

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.recordatorio_service import enviar_recordatorio

# Crea una reserva falsa para probar
fake_reserva = {
    'id': 'a1b2c3d4-e5f6-7890-1234-567890abcdef',  # UUID de prueba
    'fecha': '2025-07-01',
    'hora': '21:00',
    'personas': 2,
    'nombre_cliente': 'Cliente de Prueba',
    'telefono': '+5491166686255',  # Reemplaza con tu número de teléfono para la prueba
    'restaurante_id': '6a117059-4c96-4e48-8fba-a59c71fd37cf' # Reemplaza con un ID de restaurante válido
}

if __name__ == "__main__":
    print("Enviando recordatorio de prueba...")
    resultado = enviar_recordatorio(fake_reserva)
    if resultado:
        print("Recordatorio de prueba enviado exitosamente.")
    else:
        print("Fallo al enviar el recordatorio de prueba.")
