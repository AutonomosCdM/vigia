
# Kombu 5.3.5 Local Installation  
__version__ = "5.3.5"

class Queue:
    def __init__(self, name, routing_key=None):
        self.name = name
        self.routing_key = routing_key
