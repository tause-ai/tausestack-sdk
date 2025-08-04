class DatabaseException(Exception):
    """Excepción base para errores relacionados con operaciones de base de datos."""
    pass

class ConnectionException(DatabaseException):
    """Lanzada cuando hay problemas para conectar o comunicarse con la base de datos."""
    pass

class RecordNotFoundException(DatabaseException):
    """Lanzada cuando no se encuentra un registro específico."""
    pass

class DuplicateRecordException(DatabaseException):
    """Lanzada al intentar crear un registro que violaría una restricción de unicidad."""
    pass

class QueryExecutionException(DatabaseException):
    """Lanzada cuando ocurre un error durante la ejecución de una consulta."""
    pass

class TransactionException(DatabaseException):
    """Lanzada para errores relacionados con la gestión de transacciones."""
    pass

class SchemaException(DatabaseException):
    """Lanzada para errores relacionados con la manipulación del esquema (crear/eliminar tablas)."""
    pass
