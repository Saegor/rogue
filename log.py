class GameLog:
    """
    Classe pour gérer le log du jeu.
    """
    def __init__(self, capacity=4096):
        self.capacity = capacity
        self.messages = ["Bienvenue dans Aiouu v0.10 !"]

    def add(self, message):
        """Ajoute un message dans le log et retire le plus ancien si la capacité est dépassée."""
        self.messages.append(message)
        if len(self.messages) > self.capacity:
            self.messages.pop(0)

    def get_recent_messages(self, count=4):
        """Retourne les derniers messages (par défaut 16)."""
        return self.messages[-count:]

    def clear(self):
        """Efface le log."""
        self.messages.clear()
