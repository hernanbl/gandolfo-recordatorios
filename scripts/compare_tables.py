#!/usr/bin/env python
"""
Script para comparar las tablas reservas (legacy) y reservas_prod.
"""

import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from db.supabase_client import get_supabase_client
    
    # Obtener cliente Supabase
    supabase = get_supabase_client()
    if not supabase:
        print("Error: No se pudo obtener el cliente Supabase")
        sys.exit(1)
    
    # Fecha para filtrar (últimos 7 días)
    fecha_desde = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    print(f"Comparando reservas desde {fecha_desde} hasta hoy")
    
    # Consultar reservas recientes en ambas tablas
    print("\nConsultando tabla 'reservas' (legacy)...")
    response_legacy = supabase.table('reservas').select('*')\
        .gte('fecha', fecha_desde)\
        .order('created_at', desc=True)\
        .execute()
    
    print("Consultando tabla 'reservas_prod' (nueva)...")
    response_prod = supabase.table('reservas_prod').select('*')\
        .gte('fecha', fecha_desde)\
        .order('created_at', desc=True)\
        .execute()
    
    # Contar reservas por tabla
    count_legacy = len(response_legacy.data) if hasattr(response_legacy, 'data') else 0
    count_prod = len(response_prod.data) if hasattr(response_prod, 'data') else 0
    
    print(f"\nResultados del último periodo ({fecha_desde} hasta hoy):")
    print(f"- Reservas en tabla legacy 'reservas': {count_legacy}")
    print(f"- Reservas en tabla nueva 'reservas_prod': {count_prod}")
    
    # Análisis más detallado
    if count_legacy > 0 and count_prod == 0:
        print("\n🚨 ADVERTENCIA: Aún se están creando reservas en la tabla legacy, pero NO en la nueva.")
        print("Esto indica que la migración NO está funcionando correctamente.")
    elif count_legacy == 0 and count_prod > 0:
        print("\n✅ ÉXITO: Solo se están creando reservas en la tabla nueva.")
        print("La migración está funcionando correctamente.")
    elif count_legacy > 0 and count_prod > 0:
        print("\n⚠️ ADVERTENCIA: Se están creando reservas en AMBAS tablas.")
        print("La migración está parcialmente implementada o hay múltiples fuentes creando reservas.")
    else:
        print("\nNo se encontraron reservas recientes en ninguna tabla.")

except Exception as e:
    print(f"Error al comparar tablas: {str(e)}")
    sys.exit(1)
