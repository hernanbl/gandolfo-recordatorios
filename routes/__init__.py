# Este archivo permite que la carpeta routes sea un paquete de Python


# Importar SIEMPRE admin_routes antes que admin para asegurar que todas las rutas se agregan al blueprint
from . import admin_routes  # Importa y ejecuta todo admin_routes (asegura registro de rutas)
from . import admin         # Importa y ejecuta admin (puede agregar más rutas al mismo blueprint)
from .admin_routes import admin_bp

__all__ = ['admin_bp']