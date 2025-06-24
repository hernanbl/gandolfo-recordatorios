from flask import Blueprint, request, jsonify, session
from services.reservas_service import registrar_reserva, actualizar_estado_reserva, validar_disponibilidad_horaria, verificar_capacidad_disponible
from services.ai_service import call_deepseek_api, get_supabase_client
from services.email_service import enviar_correo_confirmacion
import logging
import os
import json
import re
import locale
import asyncio
from datetime import datetime, timedelta
import uuid
import traceback

logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Helper to get restaurant config by ID
def get_restaurant_config_by_id(restaurant_id):
    from app import supabase
    if not supabase:
        raise Exception("Supabase client not initialized.")
    try:
        response = supabase.table('restaurantes').select('*').eq('id', restaurant_id).single().execute()
        if response.data:
            return response.data
        return None
    except Exception as e:
        print(f"Error fetching restaurant config by ID {restaurant_id}: {e}")
        return None

# Validation endpoint
@api_bp.route('/reservas/validar_disponibilidad', methods=['POST'])
def validar_disponibilidad_endpoint():
    """Endpoint para validar la disponibilidad de una reserva"""
    if not request.is_json:
        return jsonify({'available': False, 'message': 'Se esperaba JSON'}), 400

    try:
        data = request.json
        restaurant_id = data.get('restaurant_id')
        fecha_str = data.get('fecha')  # Expected in YYYY-MM-DD from chatbot
        hora_str = data.get('hora')
        personas_str = data.get('personas')

        if not all([restaurant_id, fecha_str, hora_str, personas_str]):
            return jsonify({
                'available': False, 
                'message': 'Faltan datos para validar la disponibilidad (restaurant_id, fecha, hora, personas).'
            }), 400

        try:
            personas = int(personas_str)
        except ValueError:
            return jsonify({
                'available': False, 
                'message': 'El número de personas debe ser un valor numérico.'
            }), 400

        restaurant_config = get_restaurant_config_by_id(restaurant_id)
        if not restaurant_config:
            return jsonify({
                'available': False, 
                'message': f'No se pudo cargar la configuración para el restaurante ID {restaurant_id}.'
            }), 500

        # Convert date from YYYY-MM-DD to DD/MM/YYYY
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
            fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
        except ValueError:
            return jsonify({
                'available': False, 
                'message': 'Formato de fecha inválido. Se espera YYYY-MM-DD'
            }), 400

        # 1. Validate opening hours
        disponible_horario, msg_horario = validar_disponibilidad_horaria(fecha_formateada, hora_str, restaurant_config)
        if not disponible_horario:
            return jsonify({'available': False, 'message': msg_horario}), 200

        # 2. Validate capacity by running the async function in an event loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            disponible_capacidad, msg_capacidad, _ = loop.run_until_complete(
                verificar_capacidad_disponible(fecha_formateada, personas, restaurant_config)
            )
            loop.close()
        except Exception as e:
            traceback.print_exc()
            return jsonify({
                'available': False, 
                'message': f'Error al verificar capacidad: {str(e)}'
            }), 500

        if not disponible_capacidad:
            return jsonify({'available': False, 'message': msg_capacidad}), 200
            
        return jsonify({'available': True, 'message': 'Horario y capacidad disponibles.'}), 200

    except Exception as e:
        print(f"Error en validar_disponibilidad_endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'available': False, 
            'message': f'Error interno del servidor al validar disponibilidad: {str(e)}'
        }), 500
