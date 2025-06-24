from datetime import datetime

class Reserva:
    """Modelo para representar una reserva en el restaurante"""
    
    def __init__(self, nombre, fecha, hora, personas, telefono, email, origen="web", id=None, estado="pendiente", created_at=None):
        self.id = id
        self.nombre = nombre
        self.fecha = fecha  # Formato YYYY-MM-DD
        self.hora = hora    # Formato HH:MM
        self.personas = personas
        self.telefono = telefono
        self.email = email
        self.origen = origen  # web, whatsapp, telefono, etc.
        self.estado = estado  # pendiente, confirmada, cancelada
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self):
        """Convierte el objeto a un diccionario para almacenar en la base de datos"""
        return {
            "nombre": self.nombre,
            "fecha": self.fecha,
            "hora": self.hora,
            "personas": self.personas,
            "telefono": self.telefono,
            "email": self.email,
            "origen": self.origen,
            "estado": self.estado,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea una instancia de Reserva a partir de un diccionario"""
        return cls(
            id=data.get("id"),
            nombre=data.get("nombre"),
            fecha=data.get("fecha"),
            hora=data.get("hora"),
            personas=data.get("personas"),
            telefono=data.get("telefono"),
            email=data.get("email"),
            origen=data.get("origen", "web"),
            estado=data.get("estado", "pendiente"),
            created_at=data.get("created_at")
        )