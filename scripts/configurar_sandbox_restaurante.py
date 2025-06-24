#!/usr/bin/env python3
"""
Script para configurar temporalmente un restaurante con el número de sandbox
para que las respuestas a recordatorios funcionen correctamente.
"""

import sys
import os

# Añadir el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def configurar_sandbox_en_restaurante():
    """Configurar número de sandbox en el primer restaurante activo"""
    print("🔧 CONFIGURANDO NÚMERO DE SANDBOX EN RESTAURANTE")
    print("=" * 50)
    
    try:
        from db.supabase_client import supabase_client
        
        # Buscar el primer restaurante activo
        response = supabase_client.table('restaurantes')\
            .select('id, nombre, config')\
            .eq('estado', 'activo')\
            .limit(1)\
            .execute()
        
        if not response.data:
            print("❌ No se encontraron restaurantes activos")
            return False
        
        restaurant = response.data[0]
        restaurant_id = restaurant['id']
        restaurant_name = restaurant['nombre']
        
        print(f"📍 Restaurante encontrado: {restaurant_name} (ID: {restaurant_id})")
        
        # Obtener configuración actual
        current_config = restaurant.get('config', {})
        
        # Actualizar con número de sandbox
        sandbox_number = "+14155238886"
        updated_config = current_config.copy()
        updated_config['twilio_phone_number'] = sandbox_number
        
        print(f"🔄 Actualizando configuración...")
        print(f"   Número anterior: {current_config.get('twilio_phone_number', 'No configurado')}")
        print(f"   Número nuevo (sandbox): {sandbox_number}")
        
        # Actualizar en la base de datos
        update_response = supabase_client.table('restaurantes')\
            .update({'config': updated_config})\
            .eq('id', restaurant_id)\
            .execute()
        
        if update_response.data:
            print(f"✅ Configuración actualizada exitosamente")
            print(f"   Restaurante: {restaurant_name}")
            print(f"   ID: {restaurant_id}")
            print(f"   Número Twilio: {sandbox_number}")
            return True
        else:
            print(f"❌ Error actualizando configuración")
            return False
            
    except Exception as e:
        print(f"❌ Error configurando sandbox: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def verificar_configuracion():
    """Verificar que la configuración se aplicó correctamente"""
    print(f"\n🔍 VERIFICANDO CONFIGURACIÓN")
    print("=" * 30)
    
    try:
        from db.supabase_client import supabase_client
        
        sandbox_number = "+14155238886"
        
        # Buscar restaurantes con el número de sandbox
        response = supabase_client.table('restaurantes')\
            .select('id, nombre, config')\
            .execute()
        
        restaurants_with_sandbox = []
        
        for restaurant in response.data:
            config = restaurant.get('config', {})
            twilio_number = config.get('twilio_phone_number')
            
            if twilio_number == sandbox_number:
                restaurants_with_sandbox.append(restaurant)
        
        if restaurants_with_sandbox:
            print(f"✅ {len(restaurants_with_sandbox)} restaurante(s) configurado(s) con sandbox:")
            for restaurant in restaurants_with_sandbox:
                print(f"   - {restaurant['nombre']} (ID: {restaurant['id']})")
            return True
        else:
            print(f"❌ Ningún restaurante configurado con {sandbox_number}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando configuración: {str(e)}")
        return False

def mostrar_instrucciones():
    """Mostrar instrucciones sobre el funcionamiento"""
    print(f"\n" + "=" * 50)
    print("📋 CÓMO FUNCIONA AHORA")
    print("=" * 50)
    
    print(f"""
🔧 CONFIGURACIÓN APLICADA:
- Un restaurante ahora tiene el número +14155238886 configurado
- Las respuestas a recordatorios funcionarán correctamente
- El sistema encontrará el restaurante cuando respondas con "1" o "2"

🧪 PARA PROBAR:
1. Ejecutar recordatorios: python3 scripts/send_reminders.py
2. Recibir recordatorio en WhatsApp
3. Responder con "1" (confirmar) o "2" (cancelar)
4. Verificar que funciona sin error

🚀 EN PRODUCCIÓN:
- Cada restaurante tendrá su propio número de WhatsApp Business
- El número será real y verificado por WhatsApp
- No será necesario este fallback

⚠️  IMPORTANTE:
- Esta es una solución temporal para sandbox
- En producción, cada restaurante debe tener su número real
""")

def main():
    print("🔧 CONFIGURADOR DE SANDBOX PARA RESTAURANTES")
    print("=" * 60)
    
    # 1. Configurar sandbox en restaurante
    if not configurar_sandbox_en_restaurante():
        print("\n❌ No se pudo configurar el sandbox")
        return False
    
    # 2. Verificar configuración
    if not verificar_configuracion():
        print("\n❌ Verificación falló")
        return False
    
    # 3. Mostrar instrucciones
    mostrar_instrucciones()
    
    print(f"\n✅ CONFIGURACIÓN COMPLETADA")
    print("🧪 Ahora puedes probar las respuestas a recordatorios")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
