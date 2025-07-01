from supabase import create_client
import supabase
print("Versión de supabase-py:", supabase.__version__)
client = create_client("https://dummy.supabase.co", "dummy")
print("Métodos de auth:", dir(client.auth))