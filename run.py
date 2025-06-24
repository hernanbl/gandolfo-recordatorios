#!/usr/bin/env python
# filepath: c:\Users\Mariana\Desktop\gandolfo-resto-system\run.py

from app import app
from config import PORT, DEBUG
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT)
