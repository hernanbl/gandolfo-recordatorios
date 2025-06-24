#!/usr/bin/env python3
"""
Script para verificar y crear el usuario faltante de Ostende
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import supabase
import json

def main():
    print('=== Diagnóstico Usuario Ostende ===')
    
    # Datos del restaurante Ostende
    restaurant_id = '6a117059-4c96-4e48-8fba-a59c71fd37cf'
    admin_id = 'd98c18fc-060d-42a4-b9f9-943db3eccece'
    email = 'resto@vivacom.com.ar'
    
    print(f'Restaurant ID: {restaurant_id}')
    print(f'Admin ID: {admin_id}')
    print(f'Email: {email}')
    
    # 1. Verificar si el restaurante existe
    print('\n1. Verificando restaurante...')
    resto_response = supabase.table('restaurantes').select('*').eq('id', restaurant_id).execute()
    if resto_response.data:
        print('✓ Restaurante Ostende encontrado')
        resto = resto_response.data[0]
        print(f'  Nombre: {resto.get("nombre")}')
        print(f'  Admin ID: {resto.get("admin_id")}')
    else:
        print('✗ Restaurante no encontrado')
        return
    
    # 2. Verificar si existe usuario con ese auth_user_id
    print('\n2. Verificando usuario en tabla usuarios...')
    user_response = supabase.table('usuarios').select('*').eq('auth_user_id', admin_id).execute()
    if user_response.data:
        print('✓ Usuario encontrado en tabla usuarios')
        user = user_response.data[0]
        print(f'  ID: {user.get("id")}')
        print(f'  Email: {user.get("email")}')
        print(f'  Nombre: {user.get("nombre")}')
    else:
        print('✗ Usuario NO encontrado en tabla usuarios')
        print('  Creando usuario...')
        
        # Crear el usuario
        new_user_data = {
            'auth_user_id': admin_id,
            'email': email,
            'nombre': 'Administrador Ostende',
            'rol': 'admin'
        }
        
        try:
            create_response = supabase.table('usuarios').insert(new_user_data).execute()
            if create_response.data:
                print('✓ Usuario creado exitosamente')
                created_user = create_response.data[0]
                print(f'  ID creado: {created_user.get("id")}')
                print(f'  Email: {created_user.get("email")}')
            else:
                print('✗ Error al crear usuario')
                print(f'  Error: {create_response}')
        except Exception as e:
            print(f'✗ Excepción al crear usuario: {e}')
    
    # 3. Verificar si existe usuario con el email
    print('\n3. Verificando usuario por email...')
    email_response = supabase.table('usuarios').select('*').eq('email', email).execute()
    if email_response.data:
        print('✓ Usuario encontrado por email')
        user = email_response.data[0]
        print(f'  Auth User ID: {user.get("auth_user_id")}')
        print(f'  Nombre: {user.get("nombre")}')
    else:
        print('✗ Usuario NO encontrado por email')
    
    print('\n=== Resultado Final ===')
    
    # Verificación final
    final_check = supabase.table('usuarios').select('*').eq('email', email).execute()
    if final_check.data:
        user = final_check.data[0]
        resto_check = supabase.table('restaurantes').select('*').eq('admin_id', user.get('auth_user_id')).execute()
        
        if resto_check.data:
            print('✓ El usuario puede loguearse y acceder a su restaurante')
            print(f'  Usuario: {user.get("email")} -> Restaurante: {resto_check.data[0].get("nombre")}')
        else:
            print('✗ El usuario existe pero no tiene restaurante asociado')
    else:
        print('✗ El usuario todavía no existe')

if __name__ == '__main__':
    main()
