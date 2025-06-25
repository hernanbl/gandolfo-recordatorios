"""
Utilidades de autenticación robustas para Supabase
Manejan diferencias entre versiones de la librería
"""


def robust_supabase_auth(supabase_client, email, password):
    """
    Función robusta que funciona tanto en local (0.7.1) como en producción
    Intenta primero sign_in, luego sign_in_with_password
    """
    try:
        # OPCIÓN 1: Método que funciona en local (0.7.1)
        if hasattr(supabase_client.auth, 'sign_in'):
            print("🔧 Usando sign_in (versión 0.7.1)")
            return supabase_client.auth.sign_in(
                email=email,
                password=password
            )
    except Exception as e:
        print(f"⚠️ sign_in falló: {str(e)}")
    
    try:
        # OPCIÓN 2: Método alternativo para versiones más nuevas
        if hasattr(supabase_client.auth, 'sign_in_with_password'):
            print("🔧 Usando sign_in_with_password (versión nueva)")
            return supabase_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
    except Exception as e:
        print(f"⚠️ sign_in_with_password falló: {str(e)}")
    
    # OPCIÓN 3: Método para versiones muy antiguas
    try:
        if hasattr(supabase_client.auth, 'sign_in_with_email'):
            print("🔧 Usando sign_in_with_email (versión antigua)")
            return supabase_client.auth.sign_in_with_email(email, password)
    except Exception as e:
        print(f"⚠️ sign_in_with_email falló: {str(e)}")
    
    raise Exception("Ningún método de autenticación disponible")

