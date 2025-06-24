#!/usr/bin/env python3
"""
Script para corregir la relación entre el usuario gandolfo y su restaurante
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.supabase_client import get_supabase_client

def fix_gandolfo_restaurant():
    try:
        supabase = get_supabase_client()
        
        # Obtener el usuario gandolfo
        print("Buscando usuario gandolfo...")
        usuario_resp = supabase.table('usuarios').select('*').eq('email', 'gandolfo@vivacom.com.ar').execute()
        
        if not usuario_resp.data:
            print("Error: Usuario gandolfo no encontrado")
            return
            
        usuario = usuario_resp.data[0]
        user_id = usuario['id']
        auth_id = usuario['auth_user_id']
        
        print(f"Usuario encontrado:")
        print(f"  - ID en tabla usuarios: {user_id}")
        print(f"  - Auth User ID: {auth_id}")
        print(f"  - Email: {usuario['email']}")
        
        # Buscar el restaurante Gandolfo
        print("\nBuscando restaurante Gandolfo...")
        rest_resp = supabase.table('restaurantes').select('*').ilike('nombre', '%gandolfo%').execute()
        
        if not rest_resp.data:
            print("Error: Restaurante Gandolfo no encontrado")
            return
            
        restaurante = rest_resp.data[0]
        print(f"Restaurante encontrado:")
        print(f"  - ID: {restaurante['id']}")
        print(f"  - Nombre: {restaurante['nombre']}")
        print(f"  - Admin ID actual: {restaurante.get('admin_id', 'Sin admin')}")
        print(f"  - Activo: {restaurante.get('activo', False)}")
        
        # Actualizar el restaurante
        print(f"\nActualizando restaurante...")
        update_data = {
            'admin_id': user_id,  # Usar el ID de la tabla usuarios
            'activo': True
        }
        
        update_resp = supabase.table('restaurantes').update(update_data).eq('id', restaurante['id']).execute()
        
        if update_resp.data:
            updated_rest = update_resp.data[0]
            print(f"✅ Restaurante actualizado exitosamente:")
            print(f"  - ID: {updated_rest['id']}")
            print(f"  - Nombre: {updated_rest['nombre']}")
            print(f"  - Admin ID: {updated_rest['admin_id']}")
            print(f"  - Activo: {updated_rest['activo']}")
            
            # Verificar la relación
            print(f"\nVerificando relación...")
            check_resp = supabase.table('restaurantes').select('*').eq('admin_id', user_id).execute()
            print(f"Restaurantes asignados al usuario: {len(check_resp.data)}")
            
        else:
            print("❌ Error al actualizar el restaurante")
            print(f"Respuesta: {update_resp}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_gandolfo_restaurant()
