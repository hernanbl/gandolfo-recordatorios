#!/usr/bin/env python3
"""
Script para crear todos los usuarios existentes en Supabase Auth
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crear_usuarios_auth():
    """Crear usuarios en Supabase Auth para todos los existentes en la tabla usuarios"""
    
    # Obtener todos los usuarios de la tabla usuarios
    result = supabase.table('usuarios').select('*').execute()
    usuarios = result.data
    
    # Contraseñas por defecto basadas en el email
    password_map = {
        "gandolfo@vivacom.com.ar": "sofi1907",
        "vivacomargentina@gmail.com": "vivacom123", 
        "jorgea@vivacom.com.ar": "jorge123",
        "resto@vivacom.com.ar": "sofi1907"  # Cambiado de ostende123 a sofi1907
    }
    
    for usuario in usuarios:
        email = usuario['email']
        nombre = usuario.get('nombre', 'Usuario')
        user_id = usuario['id']
        
        # Usar contraseña por defecto
        password = password_map.get(email, "default123")
        
        try:
            logger.info(f"Procesando usuario: {email}")
            
            # Intentar crear/registrar usuario en Auth
            try:
                auth_result = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                
                if auth_result.user:
                    auth_user_id = auth_result.user.id
                    logger.info(f"✅ Usuario creado/encontrado en Auth con ID: {auth_user_id}")
                    
                    # Actualizar la tabla usuarios con el auth_user_id
                    update_result = supabase.table('usuarios').update({
                        'auth_user_id': auth_user_id
                    }).eq('id', user_id).execute()
                    
                    if update_result.data:
                        logger.info(f"✅ auth_user_id actualizado para usuario {user_id}")
                    else:
                        logger.error(f"❌ Error actualizando auth_user_id para {user_id}")
                else:
                    logger.error(f"❌ No se pudo crear usuario en Auth para {email}")
                    
            except Exception as e:
                if "already been registered" in str(e) or "already registered" in str(e):
                    logger.info(f"Usuario {email} ya existe en Auth, intentando login...")
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
                            update_result = supabase.table('usuarios').update({
                                'auth_user_id': auth_user_id
                            }).eq('id', user_id).execute()
                            
                            if update_result.data:
                                logger.info(f"✅ auth_user_id actualizado para usuario existente {user_id}")
                            
                    except Exception as login_error:
                        logger.error(f"Error en login de prueba para {email}: {login_error}")
                else:
                    logger.error(f"Error creando usuario {email}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error procesando usuario {email}: {str(e)}")

if __name__ == "__main__":
    crear_usuarios_auth()
