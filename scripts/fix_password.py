#!/usr/bin/env python3
"""
Script para establecer contraseña para usuario con email gandolfo@vivacom.com.ar
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import supabase

def fix_password():
    email = "gandolfo@vivacom.com.ar"
    new_password = "sofi1907"  # La contraseña que intentas usar
    
    try:
        # Verificar que el usuario existe
        result = supabase.table('usuarios').select('*').eq('email', email).execute()
        
        if not result.data:
            print(f"❌ Usuario no encontrado con email: {email}")
            return False
            
        user = result.data[0]
        print(f"✅ Usuario encontrado:")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Nombre: {user.get('nombre', 'N/A')}")
        print(f"   Password actual: {user.get('password', 'None')}")
        
        # Actualizar la contraseña
        update_result = supabase.table('usuarios').update({
            'password': new_password
        }).eq('email', email).execute()
        
        if update_result.data:
            print(f"✅ Contraseña actualizada exitosamente para {email}")
            print(f"   Nueva contraseña: {new_password}")
            return True
        else:
            print(f"❌ Error al actualizar la contraseña")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Estableciendo contraseña para gandolfo@vivacom.com.ar...")
    success = fix_password()
    
    if success:
        print("\n✅ ¡Contraseña establecida! Ahora puedes hacer login.")
    else:
        print("\n❌ No se pudo establecer la contraseña.")
