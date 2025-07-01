import sys
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# UUID de prueba que estamos usando
TEST_RESERVATION_ID = 'a1b2c3d4-e5f6-7890-1234-567890abcdef'
TEST_RESTAURANT_ID = '6a117059-4c96-4e48-8fba-a59c71fd37cf'

def ensure_test_reservation_exists():
    print(f"Verificando si la reserva de prueba {TEST_RESERVATION_ID} existe...")
    try:
        response = supabase.table('reservas_prod').select('id').eq('id', TEST_RESERVATION_ID).execute()
        if response.data:
            print(f"✅ Reserva {TEST_RESERVATION_ID} ya existe.")
            return True
        else:
            print(f"❌ Reserva {TEST_RESERVATION_ID} no encontrada. Insertando...")
            new_reservation = {
                'id': TEST_RESERVATION_ID,
                'fecha': '2025-07-01',
                'hora': '21:00',
                'personas': 2,
                'nombre_cliente': 'Cliente de Prueba',
                'telefono': '+5491166686255',
                'restaurante_id': TEST_RESTAURANT_ID,
                'estado': 'pendiente',
                'recordatorio_enviado': False
            }
            insert_response = supabase.table('reservas_prod').insert(new_reservation).execute()
            if insert_response.data:
                print(f"✅ Reserva {TEST_RESERVATION_ID} insertada exitosamente.")
                return True
            else:
                print(f"❌ Fallo al insertar la reserva {TEST_RESERVATION_ID}: {insert_response.data}")
                return False
    except Exception as e:
        print(f"Error al verificar/insertar reserva: {e}")
        return False

if __name__ == "__main__":
    ensure_test_reservation_exists()
