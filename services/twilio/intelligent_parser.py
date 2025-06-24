"""
Servicio de parsing inteligente para extraer información completa de reservas desde mensajes de WhatsApp
"""
import re
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

class IntelligentReservationParser:
    """Parser inteligente para extraer datos de reserva de mensajes completos"""
    
    def __init__(self):
        # Patrones para detectar fechas
        self.date_patterns = [
            # Fechas completas
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b',
            # DD de Mes
            r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
            # Palabras clave temporales
            r'\b(hoy|mañana|ma[ñn]ana|pasado\s*ma[ñn]ana)\b',
            # Días de la semana
            r'\b(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b'
        ]
        
        # Patrones para detectar horas
        self.time_patterns = [
            # HH:MM
            r'\b(\d{1,2}):(\d{2})\b',
            # A las HH
            r'\ba\s*las?\s*(\d{1,2})(?::(\d{2}))?\b',
            # HH horas
            r'\b(\d{1,2})\s*(?:hs?|horas?)\b',
            # Turnos específicos
            r'\b(almuerzo|mediod[ií]a|cena|noche)\b'
        ]
        
        # Patrones para detectar cantidad de personas
        self.people_patterns = [
            # N personas
            r'\b(\d{1,2})\s*personas?\b',
            # Para N
            r'\bpara\s+(\d{1,2})\b',
            # Somos N
            r'\bsomos\s+(\d{1,2})\b',
            # Mesa para N
            r'\bmesa\s+para\s+(\d{1,2})\b'
        ]
        
        # Mapeo de meses
        self.months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

    def parse_complete_message(self, message: str) -> Dict[str, Optional[str]]:
        """
        Parsea un mensaje completo y extrae toda la información posible de reserva
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Dict con fecha, hora, personas y confidence score
        """
        try:
            message_lower = message.lower().strip()
            logger.info(f"🔍 PARSING: Analizando mensaje: '{message}'")
            
            result = {
                'fecha': None,
                'hora': None, 
                'personas': None,
                'confidence': 0,
                'extracted_info': []
            }
            
            # Verificar si es un mensaje de reserva
            if not self._is_reservation_message(message_lower):
                logger.info("❌ PARSING: No es un mensaje de reserva")
                return result
            
            # Extraer cada componente
            fecha = self._extract_date(message_lower)
            hora = self._extract_time(message_lower)
            personas = self._extract_people_count(message_lower)
            
            if fecha:
                result['fecha'] = fecha
                result['extracted_info'].append('fecha')
                result['confidence'] += 0.4
                
            if hora:
                result['hora'] = hora
                result['extracted_info'].append('hora')
                result['confidence'] += 0.3
                
            if personas:
                result['personas'] = personas
                result['extracted_info'].append('personas')
                result['confidence'] += 0.3
            
            logger.info(f"✅ PARSING: Resultado: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ ERROR en parsing: {str(e)}")
            return {
                'fecha': None,
                'hora': None,
                'personas': None,
                'confidence': 0,
                'extracted_info': []
            }

    def _is_reservation_message(self, message: str) -> bool:
        """Verifica si el mensaje contiene intención de reserva"""
        reservation_keywords = [
            'reserva', 'reservar', 'mesa', 'lugar', 'comer', 'cenar', 'almorzar',
            'disponible', 'libre', 'tienen', 'hay', 'puedo', 'podemos',
            'quiero', 'queremos', 'quisiera', 'necesito', 'para'
        ]
        
        return any(keyword in message for keyword in reservation_keywords)

    def _extract_date(self, message: str) -> Optional[str]:
        """Extrae fecha del mensaje"""
        try:
            today = date.today()
            
            # Buscar palabras clave temporales
            if 'hoy' in message:
                return today.strftime("%d/%m/%Y")
            
            if any(word in message for word in ['mañana', 'maña', 'ma[ñn]ana']):
                tomorrow = today + timedelta(days=1)
                return tomorrow.strftime("%d/%m/%Y")
            
            # Buscar patrones de fecha DD/MM/YYYY
            date_match = re.search(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b', message)
            if date_match:
                day, month, year = date_match.groups()
                
                # Normalizar año
                if len(year) == 2:
                    year = '20' + year
                
                try:
                    # Validar fecha
                    date_obj = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
                    if date_obj.date() >= today:
                        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                except ValueError:
                    pass
            
            # Buscar patrón "DD de Mes"
            month_match = re.search(r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', message)
            if month_match:
                day = int(month_match.group(1))
                month_name = month_match.group(2)
                month = self.months.get(month_name)
                
                if month and 1 <= day <= 31:
                    year = today.year
                    try:
                        date_obj = date(year, month, day)
                        if date_obj < today:
                            year += 1
                            date_obj = date(year, month, day)
                        return date_obj.strftime("%d/%m/%Y")
                    except ValueError:
                        pass
                        
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo fecha: {str(e)}")
            return None

    def _extract_time(self, message: str) -> Optional[str]:
        """Extrae hora del mensaje"""
        try:
            # Buscar patrón HH:MM
            time_match = re.search(r'\b(\d{1,2}):(\d{2})\b', message)
            if time_match:
                hour, minute = time_match.groups()
                hour_int = int(hour)
                minute_int = int(minute)
                
                if 0 <= hour_int <= 23 and 0 <= minute_int <= 59:
                    return f"{hour.zfill(2)}:{minute}"
            
            # Buscar "a las X"
            a_las_match = re.search(r'\ba\s*las?\s*(\d{1,2})(?::(\d{2}))?\b', message)
            if a_las_match:
                hour = a_las_match.group(1)
                minute = a_las_match.group(2) or '00'
                hour_int = int(hour)
                
                if 1 <= hour_int <= 23:
                    return f"{hour.zfill(2)}:{minute}"
            
            # Buscar solo número + "hs" o "horas"
            hs_match = re.search(r'\b(\d{1,2})\s*(?:hs?|horas?)\b', message)
            if hs_match:
                hour = int(hs_match.group(1))
                if 1 <= hour <= 23:
                    return f"{str(hour).zfill(2)}:00"
            
            # Turnos específicos
            if any(word in message for word in ['almuerzo', 'mediodia', 'mediodía']):
                return "13:00"
            elif any(word in message for word in ['cena', 'noche']):
                return "21:00"
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo hora: {str(e)}")
            return None

    def _extract_people_count(self, message: str) -> Optional[int]:
        """Extrae cantidad de personas del mensaje"""
        try:
            # Buscar "N personas"
            people_match = re.search(r'\b(\d{1,2})\s*personas?\b', message)
            if people_match:
                count = int(people_match.group(1))
                if 1 <= count <= 20:
                    return count
            
            # Buscar "para N"
            para_match = re.search(r'\bpara\s+(\d{1,2})\b', message)
            if para_match:
                count = int(para_match.group(1))
                if 1 <= count <= 20:
                    return count
            
            # Buscar "somos N"
            somos_match = re.search(r'\bsomos\s+(\d{1,2})\b', message)
            if somos_match:
                count = int(somos_match.group(1))
                if 1 <= count <= 20:
                    return count
            
            # Buscar "mesa para N"
            mesa_match = re.search(r'\bmesa\s+para\s+(\d{1,2})\b', message)
            if mesa_match:
                count = int(mesa_match.group(1))
                if 1 <= count <= 20:
                    return count
                    
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo cantidad de personas: {str(e)}")
            return None

    def generate_confirmation_message(self, parsed_data: Dict, restaurant_name: str) -> str:
        """Genera mensaje de confirmación basado en los datos parseados"""
        extracted = parsed_data['extracted_info']
        confidence = parsed_data['confidence']
        
        if confidence >= 0.7 and len(extracted) >= 2:
            # Información suficiente para continuar
            mensaje = f"Bien. Entiendo que quieres hacer una reserva en {restaurant_name}. 📝\n\n"
            mensaje += "He detectado la siguiente información:\n"
            
            if parsed_data['fecha']:
                mensaje += f"📅 **Fecha:** {parsed_data['fecha']}\n"
            if parsed_data['hora']:
                mensaje += f"🕐 **Hora:** {parsed_data['hora']}\n"
            if parsed_data['personas']:
                mensaje += f"👥 **Personas:** {parsed_data['personas']}\n"
            
            # Preguntar por la información faltante
            missing = []
            if not parsed_data['fecha']:
                missing.append("fecha")
            if not parsed_data['hora']:
                missing.append("hora")
            if not parsed_data['personas']:
                missing.append("cantidad de personas")
            
            if missing:
                mensaje += f"\nPor favor, completá la información faltante:\n"
                mensaje += f"**{', '.join(missing)}**"
            else:
                mensaje += f"\n¿Es correcta esta información? Responde **SÍ** para continuar o **NO** para modificar."
                
        else:
            # Información insuficiente
            mensaje = f"Entiendo que quieres hacer una reserva en {restaurant_name}. 📝\n\n"
            mensaje += "Para ayudarte mejor, necesito algunos datos:\n\n"
            mensaje += "📅 **¿Para qué fecha?** (ej: hoy, mañana, 25/12)\n"
            mensaje += "🕐 **¿A qué hora?** (ej: 20:00, a las 21)\n"
            mensaje += "👥 **¿Para cuántas personas?** (ej: 4 personas)\n\n"
            mensaje += "Puedes enviarme toda la información junta o paso a paso."
        
        return mensaje

# Instancia global del parser
intelligent_parser = IntelligentReservationParser()
