#!/usr/bin/env python3
"""
Script para crear un usuario de prueba en Supabase Auth
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crear_usuario_auth():
    """Crear usuario en Supabase Auth"""
    email = "gandolfo@vivacom.com.ar"
    password = "sofi1907"
    nombre = "Gandolfo Admin"
    
    try:
        # 1. Crear usuario en Supabase Auth
        logger.info(f"Creando usuario en Supabase Auth: {email}")
        auth_result = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        if auth_result.user:
            auth_user_id = auth_result.user.id
            logger.info(f"✅ Usuario creado en Auth con ID: {auth_user_id}")
            
            # 2. Verificar si ya existe en tabla usuarios
            existing_result = supabase.table('usuarios').select('*').eq('email', email).execute()
            
            if existing_result.data:
                # Actualizar el auth_user_id
                user_id = existing_result.data[0]['id']
                logger.info(f"Usuario ya existe en tabla usuarios con ID: {user_id}")
                
                update_result = supabase.table('usuarios').update({
                    'auth_user_id': auth_user_id
                }).eq('id', user_id).execute()
                
                if update_result.data:
                    logger.info(f"✅ auth_user_id actualizado para usuario {user_id}")
                else:
                    logger.error("❌ Error actualizando auth_user_id")
            else:
                # Crear en tabla usuarios
                logger.info("Usuario no existe en tabla usuarios, creando...")
                create_result = supabase.table('usuarios').insert({
                    'email': email,
                    'nombre': nombre,
                    'auth_user_id': auth_user_id,
                    'rol': 'admin'
                }).execute()
                
                if create_result.data:
                    logger.info(f"✅ Usuario creado en tabla usuarios con ID: {create_result.data[0]['id']}")
                else:
                    logger.error("❌ Error creando usuario en tabla usuarios")
        else:
            logger.error("❌ Error creando usuario en Auth")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if "already been registered" in str(e):
            logger.info("El usuario ya existe en Auth, intentando obtener info...")
            try:
                # Intentar login para obtener el user ID
                login_result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if login_result.user:
                    auth_user_id = login_result.user.id
                    logger.info(f"✅ Usuario encontrado en Auth con ID: {auth_user_id}")
                    
                    # Actualizar tabla usuarios
                    existing_result = supabase.table('usuarios').select('*').eq('email', email).execute()
                    if existing_result.data:
                        user_id = existing_result.data[0]['id']
                        update_result = supabase.table('usuarios').update({
                            'auth_user_id': auth_user_id
                        }).eq('id', user_id).execute()
                        
                        if update_result.data:
                            logger.info(f"✅ auth_user_id actualizado para usuario existente {user_id}")
                        
            except Exception as login_error:
                logger.error(f"Error en login de prueba: {login_error}")

if __name__ == "__main__":
    crear_usuario_auth()
