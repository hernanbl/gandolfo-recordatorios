import os
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# Initialize Supabase client
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    else:
        logger.warning("Supabase credentials not found. Using mock client.")
        # Create a mock client for development/testing
        class MockSupabaseClient:
            def table(self, table_name):
                return self
                
            def insert(self, data):
                logger.info(f"MOCK: Would insert into Supabase: {data}")
                return self
                
            def execute(self):
                return {"data": [{"id": "mock-id"}]}
                
            def select(self, *args):
                return self
                
            def eq(self, field, value):
                return self
                
        supabase_client = MockSupabaseClient()
except Exception as e:
    logger.error(f"Error initializing Supabase client: {str(e)}")
    # Provide a fallback mock client
    class FallbackMockClient:
        def table(self, table_name):
            return self
            
        def insert(self, data):
            logger.warning(f"FALLBACK MOCK: Would insert into Supabase: {data}")
            return self
            
        def execute(self):
            return {"data": [{"id": "fallback-mock-id"}]}
            
        def select(self, *args):
            return self
            
        def eq(self, field, value):
            return self
            
    supabase_client = FallbackMockClient()