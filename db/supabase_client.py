import os
from dotenv import load_dotenv
import sys

# Cargar variables de entorno desde .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

print(f"Loading environment from: {dotenv_path}")

# Intentar importar supabase
try:
    from supabase import create_client
    
    # Obtener credenciales desde variables de entorno
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    print(f"SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
    print(f"SUPABASE_KEY: {'SET' if supabase_key else 'NOT SET'}")
    
    if not supabase_url or not supabase_key:
        print("ERROR CRÍTICO: Variables de entorno SUPABASE_URL o SUPABASE_KEY no encontradas")
        print("Esto causará errores de autenticación. Verifique la configuración.")
        supabase = None
    else:
        print(f"Inicializando cliente Supabase con URL: {supabase_url}")
        try:
            supabase = create_client(supabase_url, supabase_key)
            print("✅ Cliente Supabase inicializado correctamente")
        except Exception as e:
            print(f"❌ Error al crear cliente Supabase: {str(e)}")
            supabase = None
        
except ImportError:
    print("ERROR: No se pudo importar el módulo 'supabase'. Instalando...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
        from supabase import create_client
        
        # Obtener credenciales desde variables de entorno
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("ADVERTENCIA: Variables de entorno SUPABASE_URL o SUPABASE_KEY no encontradas")
            supabase = None
        else:
            print(f"Inicializando cliente Supabase con URL: {supabase_url}")
            supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"ERROR al instalar supabase: {str(e)}")
        supabase = None

# Alias para mantener compatibilidad con código existente
supabase_client = supabase

def get_supabase_client():
    """Devuelve la instancia del cliente Supabase."""
    return supabase

def get_restaurants():
    """Obtiene todos los restaurantes desde Supabase"""
    try:
        if not supabase:
            print("Cliente Supabase no disponible, devolviendo lista vacía")
            return []
            
        response = supabase.table('restaurantes').select('*').execute()
        
        if response.data:
            return response.data
        else:
            print("No se encontraron restaurantes")
            return []
            
    except Exception as e:
        print(f"Error obteniendo restaurantes: {str(e)}")
        return []

def get_restaurant_by_id(restaurant_id):
    """Obtiene un restaurante específico por su ID"""
    try:
        if not supabase:
            print(f"Cliente Supabase no disponible, devolviendo datos por defecto para {restaurant_id}")
            return {"id": restaurant_id, "name": "Restaurante por defecto"}
            
        response = supabase.table('restaurantes').select('*').eq('id', restaurant_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            print(f"Restaurante {restaurant_id} no encontrado")
            return {"id": restaurant_id, "name": "Restaurante no encontrado"}
            
    except Exception as e:
        print(f"Error obteniendo restaurante {restaurant_id}: {str(e)}")
        return {"id": restaurant_id, "name": "Error al cargar restaurante"}