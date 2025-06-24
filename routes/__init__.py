# Este archivo permite que la carpeta routes sea un paquete de Python

from .admin_routes import admin_bp
from . import admin  # Esto asegura que las rutas de admin.py se registren con admin_bp

__all__ = ['admin_bp']