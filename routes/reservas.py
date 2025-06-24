from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import the service function
from services.reservas_service import registrar_reserva
from config import get_restaurant_id  # Assuming you have a way to get this

router = APIRouter()

# Modelo para la reserva (puede ser el mismo o adaptado)
class ReservaCreate(BaseModel):
    nombre: str
    fecha: str
    hora: str
    personas: str  # The service expects personas as str, then converts
    telefono: str
    email: str
    comentarios: Optional[str] = ""
    origen: Optional[str] = "chatbot-web"  # Add origin if you want to pass it

@router.post("/api/reservas", tags=["Reservas"])
async def crear_reserva_endpoint(
    reserva_data: ReservaCreate,
    restaurant_id: str = Depends(get_restaurant_id)  # Get restaurant_id from config/dependencies
):
    try:
        # Convert Pydantic model to dict for the service function
        datos_reserva_dict = reserva_data.model_dump()

        # Ensure all necessary fields for registrar_reserva are present
        # 'estado' and 'fecha_creacion' are typically set by the backend service.
        # 'restaurante_id' will be passed to the service.

        print(f"[API_RESERVAS_ROUTE] Datos recibidos para reserva: {datos_reserva_dict}")
        print(f"[API_RESERVAS_ROUTE] Usando restaurant_id: {restaurant_id}")

        # Call the service function
        # The service function expects restaurant_id_from_config as its second argument
        service_response = registrar_reserva(datos_reserva_dict, restaurant_id)

        print(f"[API_RESERVAS_ROUTE] Respuesta del servicio registrar_reserva: {service_response}")

        if service_response.get("success"):
            return {
                "success": True,
                "message": service_response.get("message", "Reserva procesada."),
                "reserva_id": service_response.get("reserva_id"),
            }
        else:
            # Use the status_code from the service if available, otherwise default
            status_code = service_response.get("status_code", 500)
            if not isinstance(status_code, int) or not (100 <= status_code <= 599):
                print(f"[API_RESERVAS_ROUTE_WARN] Invalid status_code from service: {status_code}, defaulting to 500.")
                status_code = 500

            raise HTTPException(
                status_code=status_code,
                detail=service_response.get("message", "Error al procesar la reserva.")
            )

    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        print(f"[API_RESERVAS_ROUTE_ERROR] Excepción inesperada en el endpoint /api/reservas: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al procesar la reserva: {str(e)}")