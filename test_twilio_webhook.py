#!/usr/bin/env python3
"""
Test script para verificar que el webhook de Twilio funciona correctamente
"""
import requests
import json

# Configuración del test
BASE_URL = "http://localhost:5000"  # Cambia esto si la app está en otro puerto
WEBHOOK_URL = f"{BASE_URL}/api/twilio/webhook"

# Datos de ejemplo que Twilio enviaría
webhook_data = {
    'MessageSid': 'SM123456789',
    'From': 'whatsapp:+5491166686255',
    'To': 'whatsapp:+14155238886',  # Número de sandbox de Twilio
    'Body': 'Hola, quiero hacer una reserva',
    'NumMedia': '0'
}

def test_webhook_get():
    """Test del endpoint con GET"""
    try:
        print("🔍 Testeando webhook con GET...")
        response = requests.get(WEBHOOK_URL, timeout=10)
        print(f"✅ GET Status: {response.status_code}")
        print(f"✅ GET Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en GET: {str(e)}")
        return False

def test_webhook_post():
    """Test del endpoint con POST"""
    try:
        print("\n📤 Testeando webhook con POST...")
        response = requests.post(
            WEBHOOK_URL, 
            data=webhook_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        print(f"✅ POST Status: {response.status_code}")
        print(f"✅ POST Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en POST: {str(e)}")
        return False

def test_local_server():
    """Test si el servidor local está corriendo"""
    try:
        print("🔍 Verificando servidor local...")
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Servidor Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Servidor no está corriendo: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DEL WEBHOOK DE TWILIO")
    print("=" * 50)
    
    # Test 1: Servidor corriendo
    if not test_local_server():
        print("\n❌ El servidor no está corriendo. Inicia la app con 'python app.py' primero.")
        exit(1)
    
    # Test 2: GET request
    get_result = test_webhook_get()
    
    # Test 3: POST request
    post_result = test_webhook_post()
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS:")
    print(f"✅ Servidor corriendo: ✓")
    print(f"✅ GET request: {'✓' if get_result else '❌'}")
    print(f"✅ POST request: {'✓' if post_result else '❌'}")
    
    if get_result and post_result:
        print("\n🎉 ¡Todos los tests pasaron! El webhook funciona correctamente.")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisa los logs de la aplicación.")
