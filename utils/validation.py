import re

def is_strong_password(password: str) -> bool:
    """Verifica que la contraseña tenga al menos 8 caracteres, una mayúscula, una minúscula y un número."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True
