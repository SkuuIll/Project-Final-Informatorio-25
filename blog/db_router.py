class ReadReplicaRouter:
    """
    Router de base de datos que dirige las lecturas a una réplica de lectura
    y las escrituras a la base de datos principal.
    """
    
    def db_for_read(self, model, **hints):
        """
        Dirigir lecturas a la réplica de lectura si está disponible.
        """
        return "read_replica"
    
    def db_for_write(self, model, **hints):
        """
        Dirigir escrituras a la base de datos principal.
        """
        return "default"
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Permitir relaciones entre objetos en cualquier base de datos.
        """
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Permitir migraciones solo en la base de datos principal.
        """
        return db == "default"