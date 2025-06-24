from flask import Blueprint, jsonify
import os
import sys

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/supabase')
def debug_supabase():
    """Endpoint para debuggear configuración de Supabase en producción"""
    debug_info = {
        "environment": {},
        "supabase_client": {},
        "errors": []
    }
    
    try:
        # Check environment variables
        debug_info["environment"]["SUPABASE_URL"] = "SET" if os.environ.get('SUPABASE_URL') else "NOT SET"
        debug_info["environment"]["SUPABASE_KEY"] = "SET" if os.environ.get('SUPABASE_KEY') else "NOT SET"
        debug_info["environment"]["python_path"] = sys.path
        debug_info["environment"]["working_directory"] = os.getcwd()
        
        # Try to import and check supabase client
        try:
            from db.supabase_client import supabase
            if supabase:
                debug_info["supabase_client"]["status"] = "INITIALIZED"
                debug_info["supabase_client"]["type"] = str(type(supabase))
                debug_info["supabase_client"]["has_auth"] = hasattr(supabase, 'auth')
                
                # Test basic database connection
                try:
                    result = supabase.table('usuarios').select('id').limit(1).execute()
                    debug_info["supabase_client"]["db_connection"] = "OK"
                    debug_info["supabase_client"]["sample_users"] = len(result.data)
                except Exception as e:
                    debug_info["supabase_client"]["db_connection"] = f"ERROR: {str(e)}"
                
                # Test auth client
                try:
                    auth_client = supabase.auth
                    debug_info["supabase_client"]["auth_client"] = "OK"
                    debug_info["supabase_client"]["auth_type"] = str(type(auth_client))
                except Exception as e:
                    debug_info["supabase_client"]["auth_client"] = f"ERROR: {str(e)}"
            else:
                debug_info["supabase_client"]["status"] = "NOT INITIALIZED (None)"
                debug_info["errors"].append("Supabase client is None")
        except Exception as e:
            debug_info["supabase_client"]["import_error"] = str(e)
            debug_info["errors"].append(f"Import error: {str(e)}")
            
    except Exception as e:
        debug_info["errors"].append(f"General error: {str(e)}")
    
    return jsonify(debug_info)

@debug_bp.route('/env')
def debug_env():
    """Endpoint para debuggear variables de entorno (sin mostrar valores sensibles)"""
    env_info = {}
    
    # Variables que queremos verificar
    important_vars = [
        'SUPABASE_URL', 'SUPABASE_KEY', 'TWILIO_ACCOUNT_SID', 
        'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER', 'TZ'
    ]
    
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            # Mostrar solo los primeros y últimos caracteres para variables sensibles
            if 'KEY' in var or 'TOKEN' in var or 'SID' in var:
                env_info[var] = f"SET ({value[:8]}...{value[-4:]})"
            else:
                env_info[var] = value
        else:
            env_info[var] = "NOT SET"
    
    return jsonify(env_info)

@debug_bp.route('/test-auth')
def test_auth():
    """Endpoint para probar autenticación básica de Supabase"""
    result = {
        "test": "supabase_auth",
        "status": "unknown",
        "details": {}
    }
    
    try:
        from db.supabase_client import supabase
        
        if not supabase:
            result["status"] = "error"
            result["details"]["error"] = "Supabase client not initialized"
            return jsonify(result)
        
        # Test básico de conexión
        try:
            users = supabase.table('usuarios').select('id, email').limit(3).execute()
            result["details"]["users_found"] = len(users.data)
            result["details"]["sample_users"] = [{"id": u["id"], "email": u["email"]} for u in users.data[:2]]
        except Exception as e:
            result["details"]["db_error"] = str(e)
        
        # Test de auth client
        try:
            auth = supabase.auth
            result["details"]["auth_available"] = True
            result["details"]["auth_type"] = str(type(auth))
        except Exception as e:
            result["details"]["auth_error"] = str(e)
            result["status"] = "error"
            return jsonify(result)
        
        result["status"] = "success"
        
    except Exception as e:
        result["status"] = "error"
        result["details"]["import_error"] = str(e)
    
    return jsonify(result)
