"""
Utilidades de autenticación robustas para Supabase
Manejan diferencias entre versiones de la librería
"""


def robust_supabase_auth(supabase_client, email, password):
    """
    Función robusta que funciona tanto en local (0.7.1) como en producción
    Intenta primero sign_in_with_password (nuevo SDK), luego sign_in (viejo), luego sign_in_with_email
    """
    try:
        # SOLO usar sign_in_with_password si existe (SDK >=1.0.3, producción)
        if hasattr(supabase_client.auth, 'sign_in_with_password'):
            print("🔧 Usando sign_in_with_password (SDK >=1.0.3)")
            # Algunos SDKs requieren dict, otros argumentos nombrados
            try:
                return supabase_client.auth.sign_in_with_password(email=email, password=password)
            except TypeError:
                return supabase_client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        print(f"⚠️ sign_in_with_password falló: {str(e)}")
    try:
        # Solo intentar sign_in si NO existe sign_in_with_password (SDK <1.0, solo local)
        if not hasattr(supabase_client.auth, 'sign_in_with_password') and hasattr(supabase_client.auth, 'sign_in'):
            print("🔧 Usando sign_in (SDK <1.0, solo local)")
            return supabase_client.auth.sign_in(email=email, password=password)
    except Exception as e:
        print(f"⚠️ sign_in falló: {str(e)}")
    try:
        if hasattr(supabase_client.auth, 'sign_in_with_email'):
            print("🔧 Usando sign_in_with_email (SDK muy antiguo)")
            return supabase_client.auth.sign_in_with_email(email, password)
    except Exception as e:
        print(f"⚠️ sign_in_with_email falló: {str(e)}")
    raise Exception("Ningún método de autenticación disponible")

