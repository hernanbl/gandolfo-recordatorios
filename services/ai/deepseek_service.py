import aiohttp
import asyncio
import json
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class DeepSeekService:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-235c7f78de8a4c1d84fcb139f0b2e1a7')
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        
    async def _make_request(self, messages: list, max_tokens: int = 150, temperature: float = 0.3) -> Optional[str]:
        """Realiza una petición a la API de DeepSeek"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content'].strip()
                    else:
                        logger.error(f"Error en API DeepSeek: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error conectando con DeepSeek: {str(e)}")
            return None

    async def interpret_natural_date(self, message: str) -> Optional[str]:
        """Interpreta fechas en lenguaje natural usando IA"""
        today = date.today()
        today_str = today.strftime("%d/%m/%Y")
        day_name = today.strftime("%A")
        
        # Días de la semana en español
        spanish_days = {
            "Monday": "lunes", "Tuesday": "martes", "Wednesday": "miércoles",
            "Thursday": "jueves", "Friday": "viernes", "Saturday": "sábado", "Sunday": "domingo"
        }
        today_spanish = spanish_days.get(day_name, day_name)
        
        system_prompt = f"""Eres un asistente que interpreta fechas en español. 
Hoy es {today_spanish} {today_str}.

Tu tarea es convertir la fecha mencionada por el usuario al formato DD/MM/YYYY.

Reglas:
- Si dice "hoy" → {today_str}
- Si dice "mañana" → calcula el día siguiente
- Si menciona un día de la semana (ej: "viernes"), encuentra el próximo viernes
- Si dice "25 de mayo" o similar, convierte al formato DD/MM/YYYY
- Si ya está en formato DD/MM/YYYY, devuélvelo tal como está

Responde SOLO con la fecha en formato DD/MM/YYYY, nada más."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Fecha mencionada: {message}"}
        ]
        
        try:
            result = await self._make_request(messages, max_tokens=50, temperature=0.1)
            
            # Validar que el resultado sea una fecha válida
            if result and "/" in result:
                # Extraer solo la fecha del resultado
                import re
                date_match = re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', result)
                if date_match:
                    return f"{date_match.group(1).zfill(2)}/{date_match.group(2).zfill(2)}/{date_match.group(3)}"
            
            return None
        except Exception as e:
            logger.error(f"Error interpretando fecha con IA: {str(e)}")
            return None

    async def analyze_intent(self, message: str, restaurant_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la intención del mensaje del usuario"""
        restaurant_name = restaurant_info.get('nombre_restaurante', 'el restaurante')
        
        system_prompt = f"""Eres un asistente inteligente para {restaurant_name}. 
Analiza el mensaje del usuario y determina su intención principal.

Posibles intenciones:
1. RESERVA - quiere hacer una reserva
2. MENU - pregunta sobre el menú, platos, precios
3. INFO - pregunta sobre horarios, ubicación, contacto del restaurante
4. SALUDO - saluda o dice hola
5. DESPEDIDA - se despide
6. CANCELACION - quiere cancelar una reserva
7. CONSULTA - pregunta general sobre el restaurante
8. OTRO - cualquier otra cosa

Responde en este formato JSON exacto:
{{"intent": "INTENT_NAME", "confidence": 0.9, "entities": ["entidad1", "entidad2"]}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        try:
            result = await self._make_request(messages, max_tokens=100, temperature=0.2)
            
            if result:
                # Intentar parsear el JSON
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    # Si no es JSON válido, extraer intención manualmente
                    intent = "CONSULTA"
                    if any(word in message.lower() for word in ['reserva', 'mesa', 'cena', 'almuerzo']):
                        intent = "RESERVA"
                    elif any(word in message.lower() for word in ['menu', 'menú', 'plato', 'comida', 'precio']):
                        intent = "MENU"
                    elif any(word in message.lower() for word in ['hola', 'buenas', 'saludos']):
                        intent = "SALUDO"
                    
                    return {"intent": intent, "confidence": 0.7, "entities": []}
            
            return {"intent": "CONSULTA", "confidence": 0.5, "entities": []}
            
        except Exception as e:
            logger.error(f"Error analizando intención: {str(e)}")
            return {"intent": "CONSULTA", "confidence": 0.3, "entities": []}

    async def generate_menu_response(self, question: str, menu_data: Dict[str, Any], restaurant_info: Dict[str, Any]) -> str:
        """Genera una respuesta inteligente sobre el menú"""
        restaurant_name = restaurant_info.get('nombre_restaurante', 'el restaurante')
        
        # Construir información del menú
        menu_text = ""
        if 'categorias' in menu_data:
            for categoria in menu_data['categorias']:
                menu_text += f"\n{categoria['nombre']}:\n"
                for plato in categoria.get('platos', []):
                    precio = f"${plato.get('precio', 'N/A')}" if plato.get('precio') else ""
                    descripcion = f" - {plato.get('descripcion', '')}" if plato.get('descripcion') else ""
                    menu_text += f"• {plato.get('nombre', '')} {precio}{descripcion}\n"
        
        system_prompt = f"""Eres un asistente experto del restaurante {restaurant_name}.
Responde preguntas sobre el menú de manera amigable y útil.

INFORMACIÓN DEL MENÚ:
{menu_text}

Reglas:
- Sé conciso pero informativo
- Usa emojis apropiados y de manera discreta 🍽️🥗🍕
- Si preguntan por algo específico que no está en el json del menú, no inventes menues que no existen
- Si preguntan precios, menciona los que estén disponibles en el json de menú
- Mantén un tono amigable y profesional
- Máximo 200 palabras por respuesta"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        try:
            result = await self._make_request(messages, max_tokens=300, temperature=0.4)
            return result or f"Te ayudo con información sobre nuestro menú en {restaurant_name}. ¿Qué te gustaría saber específicamente? 🍽️"
        except Exception as e:
            logger.error(f"Error generando respuesta de menú: {str(e)}")
            return f"¡Hola! Te ayudo con información sobre nuestro menú en {restaurant_name}. ¿Qué te gustaría saber? 🍽️"

    async def generate_restaurant_info_response(self, question: str, restaurant_info: Dict[str, Any]) -> str:
        """Genera una respuesta sobre información del restaurante"""
        restaurant_name = restaurant_info.get('nombre_restaurante', 'el restaurante')
        
        # Construir información del restaurante
        info_text = f"Nombre: {restaurant_name}\n"
        if restaurant_info.get('direccion'):
            info_text += f"Dirección: {restaurant_info['direccion']}\n"
        if restaurant_info.get('telefono'):
            info_text += f"Teléfono: {restaurant_info['telefono']}\n"
        if restaurant_info.get('horarios'):
            info_text += f"Horarios: {restaurant_info['horarios']}\n"
        if restaurant_info.get('email'):
            info_text += f"Email: {restaurant_info['email']}\n"
        if restaurant_info.get('descripcion'):
            info_text += f"Descripción: {restaurant_info['descripcion']}\n"
        
        system_prompt = f"""Eres un asistente del restaurante {restaurant_name}.
Responde preguntas sobre el restaurante usando esta información:

{info_text}

Reglas:
- Sé útil y amigable
- Usa emojis apropiados 📍📞⏰
- Si no tienes la información específica, sugiere contactar directamente
- Mantén respuestas concisas
- Máximo 150 palabras"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        try:
            result = await self._make_request(messages, max_tokens=250, temperature=0.3)
            return result or f"¡Hola! Te ayudo con información sobre {restaurant_name}. ¿Qué necesitas saber? 📍"
        except Exception as e:
            logger.error(f"Error generando respuesta de info: {str(e)}")
            return f"¡Hola! Te ayudo con información sobre {restaurant_name}. ¿Qué necesitas saber? 📍"

    async def generate_conversational_response(self, message: str, restaurant_info: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Genera una respuesta conversacional general"""
        restaurant_name = restaurant_info.get('nombre_restaurante', 'el restaurante')
        user_name = context.get('nombre_completo', '').split()[0] if context and context.get('nombre_completo') else ''
        
        greeting = f"¡Hola{f' {user_name}' if user_name else ''}! " if user_name else "¡Hola! "
        
        system_prompt = f"""Eres un asistente amigable del restaurante {restaurant_name}.
Responde de manera conversacional y útil.

Contexto:
- Puedes ayudar con reservas (di "reservar" para empezar)
- Puedes responder sobre el menú
- Puedes dar información del restaurante
- Mantén un tono amigable y profesional

Reglas:
- Respuestas cortas y útiles
- Usa emojis apropiados
- Siempre ofrece ayuda específica
- Máximo 100 palabras"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        try:
            result = await self._make_request(messages, max_tokens=150, temperature=0.5)
            if result:
                return result
            else:
                return f"{greeting}¿En qué puedo ayudarte hoy? Puedo ayudarte con reservas, información del menú o del restaurante. 😊"
        except Exception as e:
            logger.error(f"Error generando respuesta conversacional: {str(e)}")
            return f"{greeting}¿En qué puedo ayudarte hoy? Puedo ayudarte con reservas, información del menú o del restaurante. 😊"

    async def handle_menu_query(self, message: str, restaurant_info: Dict[str, Any], restaurant_name: str) -> Optional[str]:
        """Maneja consultas específicas sobre el menú"""
        try:
            menu_data = restaurant_info.get('menu', {})
            return await self.generate_menu_response(message, menu_data, restaurant_info)
        except Exception as e:
            logger.error(f"Error en handle_menu_query: {str(e)}")
            return None

    async def handle_general_conversation(self, message: str, restaurant_info: Dict[str, Any], restaurant_name: str) -> Optional[str]:
        """Maneja conversación general sobre el restaurante"""
        try:
            return await self.generate_conversational_response(message, restaurant_info)
        except Exception as e:
            logger.error(f"Error en handle_general_conversation: {str(e)}")
            return None

# Instancia global del servicio
deepseek_service = DeepSeekService()

# Funciones de conveniencia para usar en otros módulos
async def interpret_natural_date(message: str) -> Optional[str]:
    """Función de conveniencia para interpretar fechas"""
    return await deepseek_service.interpret_natural_date(message)

async def analyze_message_intent(message: str, restaurant_info: Dict[str, Any]) -> Dict[str, Any]:
    """Función de conveniencia para analizar intención"""
    return await deepseek_service.analyze_intent(message, restaurant_info)

async def generate_ai_response(message: str, restaurant_info: Dict[str, Any], response_type: str = "conversational", **kwargs) -> str:
    """Función de conveniencia para generar respuestas IA"""
    if response_type == "menu":
        menu_data = kwargs.get('menu_data', {})
        return await deepseek_service.generate_menu_response(message, menu_data, restaurant_info)
    elif response_type == "info":
        return await deepseek_service.generate_restaurant_info_response(message, restaurant_info)
    else:
        context = kwargs.get('context', {})
        return await deepseek_service.generate_conversational_response(message, restaurant_info, context)
