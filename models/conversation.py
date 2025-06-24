class ConversationManager:
    def __init__(self):
        self.conversation_states = {}
    
    def get_state(self, user_id):
        """Obtiene el estado de conversación para un usuario"""
        if user_id not in self.conversation_states:
            self.conversation_states[user_id] = {
                "messages": [],
                "reservation_data": {},
                "current_step": "inicio"
            }
        return self.conversation_states[user_id]
    
    def add_message(self, user_id, role, content):
        """Agrega un mensaje al historial de conversación"""
        state = self.get_state(user_id)
        state["messages"].append({"role": role, "content": content})
        
        # Limitar el historial a los últimos 10 mensajes para evitar tokens excesivos
        if len(state["messages"]) > 10:
            state["messages"] = state["messages"][-10:]
    
    def get_messages(self, user_id):
        """Obtiene todos los mensajes de un usuario"""
        return self.get_state(user_id)["messages"]
    
    def set_reservation_data(self, user_id, key, value):
        """Establece un dato de reserva"""
        state = self.get_state(user_id)
        state["reservation_data"][key] = value
    
    def get_reservation_data(self, user_id):
        """Obtiene todos los datos de reserva de un usuario"""
        return self.get_state(user_id)["reservation_data"]
    
    def clear_reservation_data(self, user_id):
        """Limpia los datos de reserva de un usuario"""
        state = self.get_state(user_id)
        state["reservation_data"] = {}
    
    def set_current_step(self, user_id, step):
        """Establece el paso actual del proceso de reserva"""
        state = self.get_state(user_id)
        state["current_step"] = step
    
    def get_current_step(self, user_id):
        """Obtiene el paso actual del proceso de reserva"""
        return self.get_state(user_id)["current_step"]

# Instancia global del gestor de conversaciones
conversation_manager = ConversationManager()