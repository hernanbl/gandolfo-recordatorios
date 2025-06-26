"""
Utilidades de autenticación robustas para Supabase
Manejan diferencias entre versiones de la librería
"""


def robust_supabase_auth(supabase_client, email, password):
    """
    Función robusta que funciona tanto en local como en producción
    Intenta primero sign_in_with_password, luego sign_in, luego sign_in_with_email
    """
    # Log métodos disponibles para debugging
    available_methods = [m for m in dir(supabase_client.auth) if not m.startswith('_')]
    print(f"🔍 Métodos disponibles en cliente auth: {available_methods}")
    
    # OPCIÓN 1: Método que funciona en versiones recientes
    if hasattr(supabase_client.auth, 'sign_in_with_password'):
        try:
            print("🔧 Usando sign_in_with_password (versión nueva)")
            return supabase_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as e:
            print(f"⚠️ sign_in_with_password falló: {str(e)}")
    
    # OPCIÓN 2: Método que funciona en local (0.7.1)
    if hasattr(supabase_client.auth, 'sign_in'):
        try:
            print("🔧 Usando sign_in (versión 0.7.1)")
            return supabase_client.auth.sign_in(
                email=email,
                password=password
            )
        except Exception as e:
            print(f"⚠️ sign_in falló: {str(e)}")
    
    # OPCIÓN 3: Método para versiones muy antiguas
    if hasattr(supabase_client.auth, 'sign_in_with_email'):
        try:
            print("🔧 Usando sign_in_with_email (versión antigua)")
            return supabase_client.auth.sign_in_with_email(email, password)
        except Exception as e:
            print(f"⚠️ sign_in_with_email falló: {str(e)}")
    
    # Si llegamos aquí, ningún método funcionó
    print(f"❌ No se encontró método de autenticación válido. Métodos disponibles: {available_methods}")
    raise Exception("Ningún método de autenticación disponible")

