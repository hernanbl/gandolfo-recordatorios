# ... existing code ...

def create_reservation(name, people, date, time, phone, email, comments=None):
    """
    Crea una nueva reserva en la base de datos
    """
    try:
        # Intentar convertir la fecha al formato esperado si viene en formato ISO
        try:
            # Si la fecha viene en formato YYYY-MM-DD, convertirla a DD/MM/YYYY
            if '-' in date and len(date) == 10:  # formato YYYY-MM-DD
                from datetime import datetime
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                date = date_obj.strftime('%d/%m/%Y')
        except Exception as format_error:
            print(f"Error al formatear la fecha: {str(format_error)}")
            # Continuar con el formato original si hay error

        # Resto del código para crear la reserva
        # ... existing code ...
    
    except Exception as e:
        print(f"Error al crear reserva: {str(e)}")
        raise Exception(f"Error al registrar en base de datos: {str(e)}")

# ... existing code ...