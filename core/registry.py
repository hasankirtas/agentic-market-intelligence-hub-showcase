"""
COREUS Registry System (Mock Implementation).

In production, this manages dynamic plugin loading and component lifecycle.
For this showcase, it serves as a lightweight service locator.
"""

class Registry:
    _instance = None
    _components = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Registry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name, component):
        cls._components[name] = component
        
    @classmethod
    def get(cls, name):
        return cls._components.get(name)
