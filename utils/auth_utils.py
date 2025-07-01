"""
Utilidades de autenticación robustas para Supabase
Manejan diferencias entre versiones de la librería
"""


def robust_supabase_auth(supabase_client, email, password):
    """
    Función robusta que funciona tanto en local (0.7.1) como en producción
    Intenta primero sign_in_with_password (nuevo SDK), luego sign_in (viejo), luego sign_in_with_email
    """
    # 1. Intento con el método más nuevo: sign_in_with_password
    if hasattr(supabase_client.auth, 'sign_in_with_password'):
        try:
            print("🔧 Usando sign_in_with_password (SDK >= 1.0.3)")
            return supabase_client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e:
            print(f"⚠️ sign_in_with_password falló: {e}")

    # 2. Intento con el método estándar: sign_in
    if hasattr(supabase_client.auth, 'sign_in'):
        try:
            print("🔧 Usando sign_in (SDK < 1.0)")
            return supabase_client.auth.sign_in(email=email, password=password)
        except Exception as e:
            print(f"⚠️ sign_in falló: {e}")

    # 3. Intento con el método más antiguo: sign_in_with_email
    if hasattr(supabase_client.auth, 'sign_in_with_email'):
        try:
            print("🔧 Usando sign_in_with_email (SDK muy antiguo)")
            return supabase_client.auth.sign_in_with_email(email, password)
        except Exception as e:
            print(f"⚠️ sign_in_with_email falló: {e}")

    # Si ninguno funciona, lanzar excepción
    raise Exception("Ningún método de autenticación de Supabase compatible fue encontrado.")

