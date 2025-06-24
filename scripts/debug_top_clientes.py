#!/usr/bin/env python3
"""
Debug script for Top Clientes card in dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from db.supabase_client import get_supabase_client
import json

def debug_top_clientes():
    print("=== Debug Top Clientes Dashboard ===")
    
    # Configuration
    supabase = get_supabase_client()
    current_restaurant_id = "e0f20795-d325-4af1-8603-1c52050048db"  # Gandolfo
    
    # Calculate date range (same as dashboard)
    now = datetime.now(timezone.utc)
    start_of_month_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    three_months_ago_dt_chart = start_of_month_dt - relativedelta(months=3)
    today_dt_chart = now.date()
    tomorrow_dt_chart = today_dt_chart + relativedelta(days=1)
    three_months_ago_iso_chart = three_months_ago_dt_chart.date().isoformat()
    tomorrow_iso_chart = tomorrow_dt_chart.isoformat()
    
    print(f"Restaurant ID: {current_restaurant_id}")
    print(f"Date range: {three_months_ago_iso_chart} to {tomorrow_iso_chart} (excluding)")
    print()
    
    # Use the exact same query as in the dashboard
    reservas_table = 'reservas'
    id_column = 'restaurant_id'
    fecha_column = 'fecha'
    
    # Query all reservations for the date range
    top_clients_response = (supabase.table(reservas_table)
        .select('nombre_cliente, estado, fecha')
        .eq(id_column, current_restaurant_id)
        .gte(fecha_column, three_months_ago_iso_chart)
        .lt(fecha_column, tomorrow_iso_chart)
        .execute())
    
    print(f"Total reservations found: {len(top_clients_response.data) if top_clients_response.data else 0}")
    
    if top_clients_response.data:
        print("\nAll reservations in range:")
        for i, res in enumerate(top_clients_response.data, 1):
            print(f"{i:2d}. Cliente: {res.get('nombre_cliente', '')}, Estado: {res.get('estado', '')}, Fecha: {res.get('fecha', '')}")
        
        print("\n" + "="*50)
        print("Processing confirmed reservations only...")
        
        client_confirmations = {}
        confirmed_count = 0
        
        for res in top_clients_response.data:
            estado = res.get('estado', '').strip()
            # Only count confirmed reservations (case-insensitive)
            if estado.lower() in ['confirmada', 'confirmado']:
                confirmed_count += 1
                client_name = res.get('nombre_cliente', '').strip()
                fecha = res.get('fecha', '')
                if client_name and client_name != 'Sin nombre' and client_name != '':
                    client_confirmations[client_name] = client_confirmations.get(client_name, 0) + 1
                    print(f"✓ Confirmed - Cliente: {client_name}, Fecha: {fecha}, Estado: {estado}")
                else:
                    print(f"✗ Skipped (no name) - Cliente: '{client_name}', Fecha: {fecha}, Estado: {estado}")
            else:
                print(f"✗ Not confirmed - Cliente: {res.get('nombre_cliente', '')}, Estado: {estado}, Fecha: {res.get('fecha', '')}")
        
        print(f"\nTotal confirmed reservations: {confirmed_count}")
        print(f"Clients with confirmed reservations: {client_confirmations}")
        
        # Get top 8 clients by confirmed reservations
        sorted_clients = sorted(client_confirmations.items(), key=lambda item: item[1], reverse=True)[:8]
        
        print("\nTop 8 clients (sorted):")
        for i, (name, count_val) in enumerate(sorted_clients, 1):
            print(f"{i}. {name}: {count_val} reservas confirmadas")
        
        # Final dashboard data
        top_clientes_labels = [name for name, count in sorted_clients]
        top_clientes_counts = [count for name, count in sorted_clients]
        
        print(f"\nFinal dashboard data:")
        print(f"Labels: {top_clientes_labels}")
        print(f"Counts: {top_clientes_counts}")
        print(f"Total clients shown: {len(top_clientes_labels)}")
        
    else:
        print("No reservations found for the specified criteria")

if __name__ == "__main__":
    debug_top_clientes()
