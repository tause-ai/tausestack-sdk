from typing import Any, Dict, List, Optional, Type
from typing import Any, Dict, List, Optional, Type, TypeVar, AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy import MetaData, select, func, asc, desc, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncTransaction
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

from tausestack.sdk.database.base import AbstractDatabaseBackend, ItemID
# Renombramos el TypeVar Model importado para evitar conflicto con pydantic.BaseModel
from tausestack.sdk.database.base import _PydanticModelType as PydanticModelType 
from tausestack.sdk.database.exceptions import (
    ConnectionException,
    QueryExecutionException, # Lo necesitaremos
    RecordNotFoundException, # Lo necesitaremos
    SchemaException,
    TransactionException
)

# Asumimos que los modelos SQLAlchemy serán algún tipo de clase base declarativa
# No es necesario importar Base = declarative_base() aquí, ya que los modelos vienen de fuera.
SQLAlchemyModel = TypeVar('SQLAlchemyModel') 

class SQLAlchemyBackend(AbstractDatabaseBackend):
    """
    Implementación de AbstractDatabaseBackend que utiliza SQLAlchemy para interactuar
    con bases de datos relacionales de forma asíncrona.

    Esta clase proporciona una capa de abstracción sobre SQLAlchemy, permitiendo
    realizar operaciones CRUD, gestión de transacciones y ejecución de consultas
    SQL crudas. Está diseñada para trabajar con modelos de datos Pydantic para la
    entrada/salida de datos y modelos SQLAlchemy para la persistencia.

    La conexión a la base de datos, el esquema (a través de `MetaData`) y el mapeo
    entre modelos Pydantic y SQLAlchemy se configuran durante la instanciación.
    """

    def __init__(
        self, 
        database_url: str, 
        metadata: MetaData, 
        model_mapping: Dict[Type[PydanticModelType], Type[SQLAlchemyModel]],
        echo: bool = False
    ):
        """
        Inicializa el backend de SQLAlchemy.

        Args:
            database_url (str): La URL de conexión a la base de datos,
                compatible con SQLAlchemy (ej. "postgresql+asyncpg://user:pass@host/dbname",
                "sqlite+aiosqlite:///./test.db").
            metadata (MetaData): Una instancia de `sqlalchemy.MetaData` que contiene
                la definición de todas las tablas. Se utiliza para operaciones como
                `create_tables` y `drop_tables`.
            model_mapping (Dict[Type[PydanticModelType], Type[SQLAlchemyModel]]):
                Un diccionario crucial que mapea los modelos Pydantic (usados en la
                API del backend) a sus correspondientes modelos declarativos de SQLAlchemy
                (usados para la persistencia).
                Ejemplo:
                {
                    MyPydanticModel: MySQLAlchemyTableModel,
                    AnotherPydanticModel: AnotherSQLAlchemyTableModel
                }
                Los modelos SQLAlchemy deben ser clases que hereden de una base
                declarativa de SQLAlchemy (ej. `declarative_base()`) y definan
                las columnas y relaciones de la tabla.
            echo (bool, optional): Si es True, SQLAlchemy registrará todas las
                instrucciones SQL generadas. Útil para depuración. Por defecto es False.
        """
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=echo)
        self.async_session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.metadata = metadata
        self.model_mapping = model_mapping
        self._managed_session: Optional[AsyncSession] = None
        self._managed_transaction: Optional[AsyncTransaction] = None

    async def connect(self) -> None:
        """Establece la conexión e intenta una operación simple para verificar."""
        try:
            async with self.engine.connect() as connection:
                # Realizar una prueba de conexión simple (no bloqueante si es posible)
                # Para asyncpg, una simple query puede ser 'SELECT 1'
                # Para run_sync, una función lambda vacía es suficiente para probar la conectividad básica del pool.
                await connection.run_sync(lambda sync_conn: None) 
            print(f"Conectado exitosamente a la base de datos: {self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url}") # Evitar loguear creds
        except Exception as e:
            # Loguear solo el tipo de error y parte de la URL para no exponer credenciales
            db_identifier = self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url
            print(f"Error al conectar a la base de datos {db_identifier}: {type(e).__name__} - {e}")
            raise ConnectionException(f"No se pudo conectar a la base de datos {db_identifier}: {e}") from e

    async def disconnect(self) -> None:
        """Cierra la conexión con la base de datos (dispose del engine)."""
        await self.engine.dispose()
        db_identifier = self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url
        print(f"Desconectado de la base de datos: {db_identifier}")

    async def create_tables(self, models: Optional[List[Type[PydanticModelType]]] = None) -> None:
        """
        Crea todas las tablas definidas en la metadata proporcionada durante la inicialización.
        El argumento `models` (Pydantic models) no se usa directamente aquí, ya que operamos
        sobre la metadata de SQLAlchemy.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.create_all)
            print("Tablas creadas (si no existían) basadas en la metadata proporcionada.")
        except Exception as e:
            raise SchemaException(f"Error al crear tablas: {e}") from e

    async def drop_tables(self, models: Optional[List[Type[PydanticModelType]]] = None) -> None:
        """
        Elimina todas las tablas definidas en la metadata proporcionada.
        El argumento `models` (Pydantic models) no se usa directamente aquí.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.drop_all)
            print("Tablas eliminadas basadas en la metadata proporcionada.")
        except Exception as e:
            raise SchemaException(f"Error al eliminar tablas: {e}") from e

    async def create(self, model_cls: Type[PydanticModelType], data: Dict[str, Any]) -> PydanticModelType:
        sqla_model_cls = self.model_mapping.get(model_cls)
        if not sqla_model_cls:
            raise QueryExecutionException(f"No SQLAlchemy model mapping found for Pydantic model {model_cls.__name__}")

        sqla_instance = sqla_model_cls(**data)
        
        try:
            async with self._get_session_for_operation() as session:
                session.add(sqla_instance)
                await session.flush() # Necesario para obtener el ID si es autogenerado antes del commit
                await session.refresh(sqla_instance) # Refrescar para obtener todos los campos de la BD
            # El objeto Pydantic se crea después de que la transacción de sesión haya terminado.
            # Esto asegura que todos los datos (incluyendo los cargados por relaciones lazy si los hubiera)
            # estén disponibles si from_attributes=True los necesita.
            pydantic_instance = model_cls.model_validate(sqla_instance, from_attributes=True)
            return pydantic_instance
        except Exception as e:
            # Aquí podrías diferenciar tipos de excepciones de SQLAlchemy (ej. IntegrityError)
            raise QueryExecutionException(f"Error creating record for {model_cls.__name__}: {e}") from e

    async def get_by_id(self, model_cls: Type[PydanticModelType], item_id: ItemID) -> Optional[PydanticModelType]:
        sqla_model_cls = self.model_mapping.get(model_cls)
        if not sqla_model_cls:
            raise QueryExecutionException(f"No SQLAlchemy model mapping found for Pydantic model {model_cls.__name__}")

        try:
            async with self._get_session_for_operation() as session:
                sqla_instance = await session.get(sqla_model_cls, item_id)
            
            if sqla_instance:
                return model_cls.model_validate(sqla_instance, from_attributes=True)
            return None
        except Exception as e:
            raise QueryExecutionException(f"Error fetching record by ID for {model_cls.__name__}: {e}") from e
    
    async def update(self, model_cls: Type[PydanticModelType], item_id: ItemID, data: Dict[str, Any]) -> Optional[PydanticModelType]:
        sqla_model_cls = self.model_mapping.get(model_cls)
        if not sqla_model_cls:
            raise QueryExecutionException(f"No SQLAlchemy model mapping found for Pydantic model {model_cls.__name__}")

        try:
            async with self._get_session_for_operation() as session:
                sqla_instance = await session.get(sqla_model_cls, item_id)
                if not sqla_instance:
                    return None # Registro no encontrado

                # Actualizar los campos del objeto SQLAlchemy
                for key, value in data.items():
                    setattr(sqla_instance, key, value)
                
                await session.flush() # Aplicar cambios a la BD
                await session.refresh(sqla_instance) # Refrescar con datos de la BD
            
            # Convertir la instancia SQLAlchemy actualizada a Pydantic
            updated_pydantic_instance = model_cls.model_validate(sqla_instance, from_attributes=True)
            return updated_pydantic_instance
        except Exception as e:
            raise QueryExecutionException(f"Error updating record ID {item_id} for {model_cls.__name__}: {e}") from e

    async def delete(self, model_cls: Type[PydanticModelType], item_id: ItemID) -> bool:
        sqla_model_cls = self.model_mapping.get(model_cls)
        if not sqla_model_cls:
            raise QueryExecutionException(f"No SQLAlchemy model mapping found for Pydantic model {model_cls.__name__}")

        try:
            async with self._get_session_for_operation() as session:
                sqla_instance = await session.get(sqla_model_cls, item_id)
                if not sqla_instance:
                    return False # Registro no encontrado para eliminar

                await session.delete(sqla_instance)
                # El commit/rollback se maneja por _get_session_for_operation o externamente
            return True
        except Exception as e:
            raise QueryExecutionException(f"Error deleting record ID {item_id} for {model_cls.__name__}: {e}") from e

    async def find(
        self,
        model_cls: Type[PydanticModelType],
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: Optional[int] = 100,
        sort_by: Optional[List[str]] = None
    ) -> List[PydanticModelType]:
        sqla_model_cls = self.model_mapping.get(model_cls)
        if not sqla_model_cls:
            raise QueryExecutionException(f"No SQLAlchemy model mapping found for Pydantic model {model_cls.__name__}")

        stmt = select(sqla_model_cls)

        if filters:
            for field, value in filters.items():
                if hasattr(sqla_model_cls, field):
                    stmt = stmt.where(getattr(sqla_model_cls, field) == value)
                # else: podrías lanzar un error o ignorar el filtro si el campo no existe

        if sort_by:
            for sort_instruction in sort_by:
                field_name = sort_instruction
                order_func = asc

                if sort_instruction.endswith("_desc"):
                    field_name = sort_instruction[:-5]  # Remove "_desc"
                    order_func = desc
                elif sort_instruction.endswith("_asc"):
                    field_name = sort_instruction[:-4]  # Remove "_asc"
                    # order_func is already asc
                elif sort_instruction.startswith("-"): # Keep support for '-' prefix
                    field_name = sort_instruction[1:]
                    order_func = desc
                # If no suffix/prefix, field_name remains sort_instruction, order_func remains asc

                if hasattr(sqla_model_cls, field_name):
                    stmt = stmt.order_by(order_func(getattr(sqla_model_cls, field_name)))
                else:
                    # Consider logging a warning or raising an error for invalid sort fields
                    print(f"Warning: Sort field '{field_name}' (derived from '{sort_instruction}') not found in model {sqla_model_cls.__name__}. Ignoring.")

        if offset > 0:
            stmt = stmt.offset(offset)
        
        if limit is not None and limit > 0: # Asegurarse que limit es positivo
            stmt = stmt.limit(limit)

        try:
            async with self._get_session_for_operation() as session:
                result = await session.execute(stmt)
                sqla_instances = result.scalars().all()
            
            return [model_cls.model_validate(instance, from_attributes=True) for instance in sqla_instances]
        except Exception as e:
            raise QueryExecutionException(f"Error finding records for {model_cls.__name__}: {e}") from e

    async def count(
        self,
        model_cls: Type[PydanticModelType],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        sqla_model_cls = self.model_mapping.get(model_cls)
        if not sqla_model_cls:
            raise QueryExecutionException(f"No SQLAlchemy model mapping found for Pydantic model {model_cls.__name__}")

        stmt = select(func.count()).select_from(sqla_model_cls)

        if filters:
            for field, value in filters.items():
                if hasattr(sqla_model_cls, field):
                    stmt = stmt.where(getattr(sqla_model_cls, field) == value)

        try:
            async with self._get_session_for_operation() as session:
                result = await session.execute(stmt)
                count_value = result.scalar_one_or_none()
            return count_value if count_value is not None else 0
        except Exception as e:
            raise QueryExecutionException(f"Error counting records for {model_cls.__name__}: {e}") from e

    @asynccontextmanager
    async def _get_session_for_operation(self) -> AsyncIterator[AsyncSession]:
        if self._managed_session and self._managed_transaction and self._managed_transaction.is_active:
            # Estamos dentro de una transacción gestionada externamente.
            yield self._managed_session
        else:
            # No hay transacción gestionada, crear una nueva sesión y bloque de transacción.
            async with self.async_session_factory() as session:
                async with session.begin(): # Esto maneja commit/rollback para este bloque
                    yield session

    async def begin_transaction(self) -> None:
        if self._managed_transaction and self._managed_transaction.is_active:
            raise TransactionException("Transaction already active.")
        try:
            self._managed_session = self.async_session_factory()
            self._managed_transaction = await self._managed_session.begin()
            print("Transaction begun.")
        except Exception as e:
            # Asegurarse de limpiar si begin() falla después de crear la sesión
            if self._managed_session:
                await self._managed_session.close()
            self._managed_session = None
            self._managed_transaction = None
            raise TransactionException(f"Failed to begin transaction: {e}") from e

    async def commit_transaction(self) -> None:
        if not self._managed_transaction or not self._managed_session or not self._managed_transaction.is_active:
            raise TransactionException("No active transaction to commit.")
        try:
            await self._managed_transaction.commit()
            print("Transaction committed.")
        except Exception as e:
            # Intenta rollback si commit falla, aunque el estado de la transacción puede ser inconsistente.
            try:
                await self._managed_transaction.rollback()
            except Exception as rb_exc:
                print(f"Error during rollback after commit failed: {rb_exc}")
            raise TransactionException(f"Failed to commit transaction: {e}") from e
        finally:
            if self._managed_session:
                await self._managed_session.close()
            self._managed_session = None
            self._managed_transaction = None

    async def rollback_transaction(self) -> None:
        if not self._managed_transaction or not self._managed_session or not self._managed_transaction.is_active:
            # Podría ser silencioso si no hay transacción, o lanzar excepción. Lanzar es más estricto.
            raise TransactionException("No active transaction to rollback.")
        try:
            await self._managed_transaction.rollback()
            print("Transaction rolled back.")
        except Exception as e:
            raise TransactionException(f"Failed to rollback transaction: {e}") from e
        finally:
            if self._managed_session:
                await self._managed_session.close()
            self._managed_session = None
            self._managed_transaction = None

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """
        Proporciona un gestor de contexto para manejar transacciones automáticamente.

        Uso:
        async with backend.transaction():
            # ... operaciones de base de datos ...
            # Si no hay excepciones, se hace commit automáticamente.
            # Si hay una excepción, se hace rollback automáticamente.
        """
        if self._managed_transaction and self._managed_transaction.is_active:
            # Ya estamos dentro de una transacción gestionada manualmente, no crear una nueva.
            # Simplemente cedemos el control y dejamos que la transacción externa la maneje.
            # Esto podría ser un punto de debate: ¿debería lanzar un error o permitir anidamiento no real?
            # Por ahora, para simplicidad, no permitimos anidamiento real de transacciones gestionadas por este backend.
            # Si se usa `async with backend.transaction()` dentro de `backend.begin_transaction()`, este bloque no hará nada nuevo.
            # Si se usa `async with backend.transaction()` dentro de otro `async with backend.transaction()`, se comportará como un bloque anidado
            # pero solo la transacción más externa será real.
            # Para la mayoría de los casos de uso, esto es suficiente.
            # Una implementación más robusta podría usar SAVEPOINTs para transacciones anidadas.
            yield
            return

        await self.begin_transaction()
        try:
            yield
            await self.commit_transaction()
        except Exception as e:
            print(f"Exception within transaction context: {type(e).__name__} - {e}. Rolling back.")
            await self.rollback_transaction()
            raise
        finally:
            # Asegurarse de que la sesión y transacción gestionadas se limpian
            # si no fueron limpiadas por commit/rollback (aunque deberían haberlo sido).
            if self._managed_session:
                await self._managed_session.close()
            self._managed_session = None
            self._managed_transaction = None

    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            async with self._get_session_for_operation() as session:
                stmt = text(query)
                result = await session.execute(stmt, params)
                return result.rowcount 
        except Exception as e:
            raise QueryExecutionException(f"Error executing raw query: {e}") from e

    async def fetch_all_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            async with self._get_session_for_operation() as session:
                stmt = text(query)
                result = await session.execute(stmt, params)
                return [dict(row._mapping) for row in result.all()]
        except Exception as e:
            raise QueryExecutionException(f"Error fetching all raw results: {e}") from e

    async def fetch_one_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            async with self._get_session_for_operation() as session:
                stmt = text(query)
                result = await session.execute(stmt, params)
                row = result.first()
                return dict(row._mapping) if row else None
        except Exception as e:
            raise QueryExecutionException(f"Error fetching one raw result: {e}") from e
