#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla usuarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import supabase

def check_table_structure():
    try:
        # Obtener un usuario para ver qué campos existen
        result = supabase.table('usuarios').select('*').limit(1).execute()
        
        if result.data:
            user = result.data[0]
            print("📋 Campos disponibles en la tabla 'usuarios':")
            for field, value in user.items():
                print(f"   - {field}: {type(value).__name__} = {value}")
        else:
            print("❌ No hay usuarios en la tabla")
            
        # Verificar usuario específico
        specific_result = supabase.table('usuarios').select('*').eq('email', 'gandolfo@vivacom.com.ar').execute()
        
        if specific_result.data:
            print(f"\n👤 Usuario gandolfo@vivacom.com.ar:")
            user = specific_result.data[0]
            for field, value in user.items():
                print(f"   - {field}: {value}")
        else:
            print("\n❌ Usuario gandolfo@vivacom.com.ar no encontrado")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_table_structure()
