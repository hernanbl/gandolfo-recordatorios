#!/usr/bin/env python
"""
Script para probar la creación de reservas a través del endpoint /api/reservas,
simulando el proceso que realiza el chatbot en el frontend.
"""

import sys
import os
import json
import traceback
import requests
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('probar_api_reservas')

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import RESERVAS_TABLE, USE_PROD_TABLES
except ImportError as e:
    logger.error(f"Error al importar los módulos necesarios: {str(e)}")
    sys.exit(1)

# URL base del API (local)
BASE_URL = 'http://localhost:5000'  # Cambiar si se ejecuta en otro puerto o servidor

def probar_endpoint_reservas():
    """
    Prueba el endpoint /api/reservas simulando cómo lo haría el chatbot.
    """
    logger.info("Iniciando prueba del endpoint /api/reservas...")
    
    # IDs de los restaurantes
    restaurantes = {
        'gandolfo': '6a117059-4c96-4e48-8fba-a59c71fd37cf',
        'ostende': 'e0f20795-d325-4af1-8603-1c52050048db'
    }
    
    # Lista de reservas a probar (una para cada restaurante)
    reservas = [
        {
            'restaurant_id': restaurantes['gandolfo'],  # Probamos con restaurant_id (como lo envía chatbot.js original)
            'restaurante_id': restaurantes['gandolfo'],  # Enviamos ambos para mayor compatibilidad
            'nombre': 'API Test Gandolfo',
            'fecha': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'hora': '19:00',
            'personas': 3,
            'telefono': '1144445555',
            'email': 'api.test.gandolfo@example.com',
            'comentarios': 'Reserva de prueba API para Gandolfo',
            'estado': 'Pendiente',
            'origen': 'script_api_test'
        },
        {
            'restaurant_id': restaurantes['ostende'],
            'restaurante_id': restaurantes['ostende'],
            'nombre': 'API Test Ostende',
            'fecha': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'hora': '14:00',
            'personas': 5,
            'telefono': '1166667777',
            'email': 'api.test.ostende@example.com',
            'comentarios': 'Reserva de prueba API para Ostende',
            'estado': 'Pendiente',
            'origen': 'script_api_test'
        }
    ]
    
    resultados = []
    
    for reserva in reservas:
        # Determinar el restaurante
        restaurante_nombre = "Gandolfo" if reserva['restaurant_id'] == restaurantes['gandolfo'] else "Ostende"
        
        logger.info(f"\n== Probando creación de reserva vía API para {restaurante_nombre} ==")
        logger.info(f"URL: {BASE_URL}/api/reservas")
        logger.info(f"Payload: {json.dumps(reserva, indent=2)}")
        
        # Mostrar detalles clave de la reserva
        logger.info(f"Nombre: {reserva['nombre']}")
        logger.info(f"Fecha/Hora: {reserva['fecha']} a las {reserva['hora']}")
        logger.info(f"Personas: {reserva['personas']}")
        
        try:
            # Enviar solicitud POST al endpoint
            response = requests.post(
                f"{BASE_URL}/api/reservas",
                json=reserva,
                headers={'Content-Type': 'application/json'}
            )
            
            # Verificar respuesta
            logger.info(f"Código de respuesta: {response.status_code}")
            logger.info(f"Respuesta: {response.text}")
            
            # Intentar parsear la respuesta como JSON
            try:
                response_data = response.json()
                if response.status_code == 200 and response_data.get('success'):
                    logger.info(f"✅ Reserva creada exitosamente para {restaurante_nombre}!")
                    logger.info(f"ID de reserva: {response_data.get('id')}")
                    resultados.append({
                        'restaurante': restaurante_nombre,
                        'success': True, 
                        'id': response_data.get('id'),
                        'status_code': response.status_code
                    })
                else:
                    logger.error(f"❌ Error al crear la reserva para {restaurante_nombre}: {response_data.get('error', 'Error desconocido')}")
                    resultados.append({
                        'restaurante': restaurante_nombre,
                        'success': False, 
                        'error': response_data.get('error', 'Error desconocido'),
                        'status_code': response.status_code
                    })
            except ValueError:
                logger.error(f"❌ Error al parsear respuesta como JSON: {response.text}")
                resultados.append({
                    'restaurante': restaurante_nombre,
                    'success': False, 
                    'error': 'Error al parsear respuesta como JSON',
                    'response_text': response.text,
                    'status_code': response.status_code
                })
                
        except Exception as e:
            logger.error(f"❌ Error al hacer la solicitud para {restaurante_nombre}: {str(e)}")
            logger.error(traceback.format_exc())
            resultados.append({
                'restaurante': restaurante_nombre,
                'success': False, 
                'error': str(e)
            })
    
    # Mostrar resumen de resultados
    logger.info("\n== RESUMEN DE RESULTADOS ==")
    exitos = sum(1 for r in resultados if r.get('success'))
    logger.info(f"Total de pruebas: {len(resultados)}")
    logger.info(f"Exitosas: {exitos}")
    logger.info(f"Fallidas: {len(resultados) - exitos}")
    
    for i, resultado in enumerate(resultados, 1):
        logger.info(f"\n[{i}] Restaurante: {resultado['restaurante']}")
        logger.info(f"    Resultado: {'✅ Éxito' if resultado.get('success') else '❌ Error'}")
        if resultado.get('success'):
            logger.info(f"    ID de reserva: {resultado.get('id')}")
        else:
            logger.info(f"    Error: {resultado.get('error', 'Desconocido')}")
            logger.info(f"    Código: {resultado.get('status_code', 'N/A')}")
    
    return exitos > 0

def confirmar_con_usuario():
    """
    Solicita confirmación al usuario antes de proceder.
    """
    print("\n¡ATENCIÓN!")
    print("Este script enviará solicitudes POST al endpoint /api/reservas para crear reservas de prueba.")
    print("La aplicación debe estar en ejecución en localhost:5000 (o la URL configurada).")
    print("Esta acción no puede deshacerse automáticamente.")
    
    while True:
        respuesta = input("\n¿Deseas continuar? (s/n): ").strip().lower()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif respuesta in ['n', 'no']:
            return False
        else:
            print("Por favor, responde 's' para sí o 'n' para no.")

def main():
    """Función principal"""
    print("\\n===== PROBADOR DEL ENDPOINT API DE RESERVAS =====\\n")
    
    try:
        # Verificar la configuración actual
        logger.info("Verificando configuración del sistema...")
        logger.info(f"USE_PROD_TABLES: {USE_PROD_TABLES}")
        logger.info(f"RESERVAS_TABLE configurado como: {RESERVAS_TABLE}")
        
        # Permitir cambiar la URL base
        global BASE_URL
        custom_url = input(f"URL del servidor (presione Enter para usar {BASE_URL}): ").strip()
        if custom_url:
            BASE_URL = custom_url
        logger.info(f"Usando URL base: {BASE_URL}")
        
        if not confirmar_con_usuario():
            print("Operación cancelada por el usuario.")
            # Permitir que caiga al bloque finally
        else:
            resultado = probar_endpoint_reservas()
            
            if resultado:
                print("\\n✅ Al menos una prueba del endpoint de reservas fue exitosa.")
                print("Para verificar las reservas creadas, ejecuta:")
                print("   python scripts/verificar_reservas_prod.py prod")
            else:
                print("\\n❌ Todas las pruebas del endpoint de reservas fallaron.")
    
    except KeyboardInterrupt:
        print("\\n🚫 Operación interrumpida por el usuario.")
        logger.warning("Script interrumpido por el usuario (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"❌ Ocurrió un error inesperado en la ejecución principal del script: {str(e)}")
        logger.error(traceback.format_exc())
        print("\\n❌ Ocurrió un error inesperado. Revisa los logs para más detalles.")
    finally:
        print("\\n===== FIN DEL PROCESO =====")

if __name__ == "__main__":
    main()