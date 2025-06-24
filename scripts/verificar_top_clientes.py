#!/usr/bin/env python3
"""
Script para verificar específicamente el cálculo de Top Clientes
"""

import os
import sys
sys.path.append('/Volumes/AUDIO/gandolfo_150625')

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from db.supabase_client import get_supabase_client
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_top_clientes():
    """Verificar el cálculo de Top Clientes para Gandolfo"""
    
    # Configuración
    supabase = get_supabase_client()
    reservas_table = "reservas"
    gandolfo_id = "e0f20795-d325-4af1-8603-1c52050048db"
    
    # Calcular fechas (últimos 3 meses)
    now = datetime.now()
    start_of_month_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    three_months_ago_dt = start_of_month_dt - relativedelta(months=3)
    today_dt = now.date()
    
    three_months_ago_iso = three_months_ago_dt.date().isoformat()
    today_iso = today_dt.isoformat()
    
    print(f"\n=== VERIFICACIÓN TOP CLIENTES GANDOLFO ===")
    print(f"Restaurant ID: {gandolfo_id}")
    print(f"Período: {three_months_ago_iso} hasta {today_iso}")
    
    try:
        # 1. Verificar reservas totales en el período
        total_response = (supabase.table(reservas_table)
            .select('nombre, estado, fecha')
            .eq('restaurant_id', gandolfo_id)
            .gte('fecha', three_months_ago_iso)
            .lt('fecha', today_iso)
            .execute())
        
        if hasattr(total_response, 'data') and total_response.data:
            print(f"\nTotal reservas encontradas: {len(total_response.data)}")
            
            # Analizar estados únicos
            estados_unicos = set()
            for res in total_response.data:
                estado = res.get('estado', '').strip()
                if estado:
                    estados_unicos.add(estado)
            
            print(f"Estados únicos encontrados: {sorted(estados_unicos)}")
            
            # Contar por estado
            conteo_estados = {}
            for res in total_response.data:
                estado = res.get('estado', '').strip()
                conteo_estados[estado] = conteo_estados.get(estado, 0) + 1
            
            print(f"\nConteo por estado:")
            for estado, count in sorted(conteo_estados.items()):
                print(f"  {estado}: {count}")
            
            # 2. Calcular Top Clientes con reservas confirmadas
            print(f"\n=== CÁLCULO TOP CLIENTES ===")
            
            # Definir todos los posibles estados confirmados
            estados_confirmados = [
                'confirmada', 'confirmado', 'Confirmada', 'Confirmado',
                'CONFIRMADA', 'CONFIRMADO'
            ]
            
            client_confirmations = {}
            reservas_confirmadas = []
            
            for res in total_response.data:
                estado = res.get('estado', '').strip()
                
                if estado in estados_confirmados:
                    client_name = res.get('nombre', '').strip()
                    fecha = res.get('fecha', '')
                    
                    if client_name and client_name != 'Sin nombre':
                        client_confirmations[client_name] = client_confirmations.get(client_name, 0) + 1
                        reservas_confirmadas.append({
                            'cliente': client_name,
                            'estado': estado,
                            'fecha': fecha
                        })
            
            print(f"Total reservas confirmadas: {len(reservas_confirmadas)}")
            print(f"Clientes únicos con reservas confirmadas: {len(client_confirmations)}")
            
            if reservas_confirmadas:
                print(f"\nPrimeras 5 reservas confirmadas:")
                for i, res in enumerate(reservas_confirmadas[:5]):
                    print(f"  {i+1}. {res['cliente']} - {res['estado']} - {res['fecha']}")
            
            # Ordenar y mostrar top 8
            sorted_clients = sorted(client_confirmations.items(), key=lambda x: x[1], reverse=True)[:8]
            
            print(f"\n=== TOP 8 CLIENTES ===")
            if sorted_clients:
                for i, (nombre, count) in enumerate(sorted_clients, 1):
                    print(f"{i}. {nombre}: {count} reservas confirmadas")
                
                # Preparar datos para el gráfico
                top_clientes_labels = [name for name, _ in sorted_clients]
                top_clientes_counts = [count for _, count in sorted_clients]
                
                print(f"\nDatos para el gráfico:")
                print(f"Labels: {top_clientes_labels}")
                print(f"Counts: {top_clientes_counts}")
                
            else:
                print("No se encontraron clientes con reservas confirmadas")
        
        else:
            print("No se encontraron reservas en el período especificado")
            
    except Exception as e:
        logger.error(f"Error verificando top clientes: {e}", exc_info=True)

if __name__ == "__main__":
    verificar_top_clientes()
