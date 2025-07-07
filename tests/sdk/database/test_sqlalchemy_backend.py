import pytest
import asyncio
from typing import Optional, Dict, Type, List
from sqlalchemy import MetaData, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

from tausestack.sdk.database import SQLAlchemyBackend, Model as PydanticModel, ItemID
from tausestack.sdk.database.exceptions import ConnectionException, QueryExecutionException

# --- Modelos de Prueba ---
Base = declarative_base()
metadata = MetaData()

class ItemSQLAModel(Base):
    __tablename__ = "test_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    value = Column(Integer)
    is_active = Column(Boolean, default=True)

# Asociar la tabla al metadata global que usará el backend
ItemSQLAModel.__table__.to_metadata(metadata)


class ItemPydanticModel(PydanticModel):
    id: Optional[ItemID] = None
    name: str
    value: Optional[int] = None
    is_active: bool = True


model_mapping_test: Dict[Type[PydanticModel], Type[Base]] = {
    ItemPydanticModel: ItemSQLAModel
}

DATABASE_URL_TEST = "sqlite+aiosqlite:///./test_db_sqlalchemy_backend.db" # Usaremos un archivo para inspección, podría ser ":memory:"

# --- Fixtures de Pytest ---

@pytest.fixture(scope="function") # 'function' para que cada test tenga una BD limpia
async def db_backend() -> SQLAlchemyBackend:
    """
    Proporciona una instancia de SQLAlchemyBackend configurada para pruebas,
    con tablas creadas y eliminadas alrededor de cada prueba.
    """
    backend = SQLAlchemyBackend(
        database_url=DATABASE_URL_TEST,
        metadata=metadata, # Usamos la metadata global donde se registró ItemSQLAModel
        model_mapping=model_mapping_test,
        echo=False # Puedes ponerlo a True para depurar SQL
    )
    await backend.connect()
    # Asegurarse que la metadata usada por create_tables es la correcta
    # Si ItemSQLAModel no se registra en el metadata global de SQLAlchemyBackend,
    # create_tables no la creará.
    # La línea ItemSQLAModel.__table__.to_metadata(metadata) debería asegurar esto.
    await backend.create_tables() # Crear tablas antes de cada test
    yield backend # El test se ejecuta aquí
    await backend.drop_tables() # Limpiar tablas después de cada test
    await backend.disconnect()
    
    # Opcional: eliminar el archivo de base de datos si se usa uno físico para pruebas
    import os
    # Construir la ruta completa al archivo de BD para evitar problemas con CWD
    # Asumimos que este archivo de prueba está en tests/sdk/database/
    # y la BD de prueba se crea en el mismo directorio.
    db_file_path = os.path.join(os.path.dirname(__file__), "test_db_sqlalchemy_backend.db")
    if os.path.exists(db_file_path):
        os.remove(db_file_path)

# --- Pruebas Básicas ---

@pytest.mark.asyncio
async def test_connection(db_backend: SQLAlchemyBackend):
    """Prueba la conexión y desconexión (implícita en la fixture)."""
    assert db_backend.engine is not None
    # La fixture ya maneja connect/disconnect, así que si llega aquí, funcionó.
    print("Conexión y creación de tablas exitosa (manejada por fixture).")

@pytest.mark.asyncio
async def test_create_and_get_item(db_backend: SQLAlchemyBackend):
    """Prueba crear un item y luego obtenerlo por ID."""
    item_data = {"name": "Test Item 1", "value": 100, "is_active": True}
    
    # Crear item
    created_item = await db_backend.create(ItemPydanticModel, item_data)
    assert created_item.id is not None
    assert created_item.name == item_data["name"]
    assert created_item.value == item_data["value"]
    
    # Obtener item por ID
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, created_item.id)
    assert fetched_item is not None
    assert fetched_item.id == created_item.id
    assert fetched_item.name == item_data["name"]

@pytest.mark.asyncio
async def test_get_item_not_found(db_backend: SQLAlchemyBackend):
    """Prueba obtener un item que no existe."""
    non_existent_id = 99999
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, non_existent_id)
    assert fetched_item is None

@pytest.mark.asyncio
async def test_update_item(db_backend: SQLAlchemyBackend):
    """Prueba actualizar un item existente."""
    # Crear item inicial
    initial_data = {"name": "Original Name", "value": 10, "is_active": True}
    created_item = await db_backend.create(ItemPydanticModel, initial_data)
    assert created_item.id is not None

    # Datos para actualizar
    update_data = {"name": "Updated Name", "value": 20}
    updated_item = await db_backend.update(ItemPydanticModel, created_item.id, update_data)
    
    assert updated_item is not None
    assert updated_item.id == created_item.id
    assert updated_item.name == update_data["name"]
    assert updated_item.value == update_data["value"]
    assert updated_item.is_active == initial_data["is_active"] # is_active no se actualizó, debe mantener su valor

    # Verificar que los datos se persistieron correctamente
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, created_item.id)
    assert fetched_item is not None
    assert fetched_item.name == update_data["name"]
    assert fetched_item.value == update_data["value"]

@pytest.mark.asyncio
async def test_update_item_not_found(db_backend: SQLAlchemyBackend):
    """Prueba actualizar un item que no existe."""
    non_existent_id = 99999
    update_data = {"name": "Non Existent Update"}
    updated_item = await db_backend.update(ItemPydanticModel, non_existent_id, update_data)
    assert updated_item is None

@pytest.mark.asyncio
async def test_delete_item(db_backend: SQLAlchemyBackend):
    """Prueba eliminar un item existente."""
    # Crear item
    item_data = {"name": "To Be Deleted", "value": 50}
    created_item = await db_backend.create(ItemPydanticModel, item_data)
    assert created_item.id is not None

    # Eliminar item
    delete_result = await db_backend.delete(ItemPydanticModel, created_item.id)
    assert delete_result is True

    # Verificar que el item ya no existe
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, created_item.id)
    assert fetched_item is None

@pytest.mark.asyncio
async def test_delete_item_not_found(db_backend: SQLAlchemyBackend):
    """Prueba eliminar un item que no existe."""
    non_existent_id = 88888
    delete_result = await db_backend.delete(ItemPydanticModel, non_existent_id)
    assert delete_result is False

@pytest.mark.asyncio
async def test_find_items_no_filters(db_backend: SQLAlchemyBackend):
    """Prueba buscar items sin filtros, esperando los items creados."""
    item1_data = {"name": "Find Item 1", "value": 101, "is_active": True}
    item2_data = {"name": "Find Item 2", "value": 102, "is_active": False}
    await db_backend.create(ItemPydanticModel, item1_data)
    await db_backend.create(ItemPydanticModel, item2_data)

    found_items = await db_backend.find(ItemPydanticModel)
    assert len(found_items) >= 2 # Puede haber items de tests anteriores si la BD no se limpia perfectamente entre tests
    # Para ser más precisos, podríamos contar cuántos tienen "Find Item" en el nombre
    count = sum(1 for item in found_items if item.name.startswith("Find Item"))
    assert count == 2

@pytest.mark.asyncio
async def test_find_items_with_filter(db_backend: SQLAlchemyBackend):
    """Prueba buscar items con un filtro simple."""
    item1_data = {"name": "Filterable A", "value": 200, "is_active": True}
    item2_data = {"name": "Filterable B", "value": 200, "is_active": False}
    await db_backend.create(ItemPydanticModel, item1_data)
    await db_backend.create(ItemPydanticModel, item2_data)

    found_items = await db_backend.find(ItemPydanticModel, filters={"value": 200})
    assert len(found_items) == 2
    assert all(item.value == 200 for item in found_items)

    found_items_active = await db_backend.find(ItemPydanticModel, filters={"is_active": True, "name": "Filterable A"})
    assert len(found_items_active) == 1
    assert found_items_active[0].name == "Filterable A"

@pytest.mark.asyncio
async def test_find_items_pagination(db_backend: SQLAlchemyBackend):
    """Prueba la paginación en la búsqueda de items."""
    for i in range(5):
        await db_backend.create(ItemPydanticModel, {"name": f"Paginate Item {i}", "value": 300 + i})
    
    # Obtener página 1 (2 items)
    items_page1 = await db_backend.find(ItemPydanticModel, filters={"value__gte": 300}, limit=2, offset=0, sort_by=["value_asc"])
    assert len(items_page1) == 2
    assert items_page1[0].value == 300
    assert items_page1[1].value == 301

    # Obtener página 2 (2 items)
    items_page2 = await db_backend.find(ItemPydanticModel, filters={"value__gte": 300}, limit=2, offset=2, sort_by=["value_asc"])
    assert len(items_page2) == 2
    assert items_page2[0].value == 302
    assert items_page2[1].value == 303

    # Obtener página 3 (1 item)
    items_page3 = await db_backend.find(ItemPydanticModel, filters={"value__gte": 300}, limit=2, offset=4, sort_by=["value_asc"])
    assert len(items_page3) == 1
    assert items_page3[0].value == 304

@pytest.mark.asyncio
async def test_find_items_sorting(db_backend: SQLAlchemyBackend):
    """Prueba el ordenamiento en la búsqueda de items."""
    await db_backend.create(ItemPydanticModel, {"name": "Sort C", "value": 402})
    await db_backend.create(ItemPydanticModel, {"name": "Sort A", "value": 400})
    await db_backend.create(ItemPydanticModel, {"name": "Sort B", "value": 401})

    # Ordenar por nombre ascendente
    sorted_by_name = await db_backend.find(ItemPydanticModel, filters={"value__gte": 400}, sort_by=["name_asc"])
    assert len(sorted_by_name) == 3
    assert [item.name for item in sorted_by_name] == ["Sort A", "Sort B", "Sort C"]

    # Ordenar por valor descendente
    sorted_by_value_desc = await db_backend.find(ItemPydanticModel, filters={"value__gte": 400}, sort_by=["value_desc"])
    assert len(sorted_by_value_desc) == 3
    assert [item.value for item in sorted_by_value_desc] == [402, 401, 400]

@pytest.mark.asyncio
async def test_find_items_not_found(db_backend: SQLAlchemyBackend):
    """Prueba buscar items con un filtro que no encuentra resultados."""
    found_items = await db_backend.find(ItemPydanticModel, filters={"name": "NonExistentNameForFind"})
    assert len(found_items) == 0

@pytest.mark.asyncio
async def test_count_items_no_filters(db_backend: SQLAlchemyBackend):
    """Prueba contar todos los items (considerando los creados en este test)."""
    # Limpiar la tabla o asegurarse de que no hay items antes de contar
    # Por simplicidad, crearemos items específicos para este test y contaremos esos.
    # Esto es más robusto que depender del estado de tests anteriores.
    # Primero, eliminemos los items que podrían coincidir con el nombre para evitar solapamientos.
    # Esto es un poco hacky para un test unitario, idealmente cada test es 100% aislado.
    # Una mejor aproximación sería usar una tabla diferente o limpiar la tabla al inicio del test.
    # Por ahora, asumimos que la fixture db_backend ya limpia las tablas.
    
    initial_count = await db_backend.count(ItemPydanticModel)
    
    await db_backend.create(ItemPydanticModel, {"name": "Count Item 1", "value": 500})
    await db_backend.create(ItemPydanticModel, {"name": "Count Item 2", "value": 501})
    
    total_count = await db_backend.count(ItemPydanticModel)
    assert total_count == initial_count + 2

@pytest.mark.asyncio
async def test_count_items_with_filter(db_backend: SQLAlchemyBackend):
    """Prueba contar items con un filtro."""
    await db_backend.create(ItemPydanticModel, {"name": "Count Filter A", "value": 600, "is_active": True})
    await db_backend.create(ItemPydanticModel, {"name": "Count Filter B", "value": 601, "is_active": True})
    await db_backend.create(ItemPydanticModel, {"name": "Count Filter C", "value": 602, "is_active": False})

    active_count = await db_backend.count(ItemPydanticModel, filters={"is_active": True, "name__startswith": "Count Filter"})
    assert active_count == 2

    value_count = await db_backend.count(ItemPydanticModel, filters={"value": 600})
    assert value_count == 1

# --- Pruebas de Transacciones ---

@pytest.mark.asyncio
async def test_transaction_commit(db_backend: SQLAlchemyBackend):
    """Prueba que un commit explícito guarda los cambios."""
    item_name = "Commit Test Item"
    item_id = None

    await db_backend.begin_transaction()
    try:
        created_item = await db_backend.create(ItemPydanticModel, {"name": item_name, "value": 700})
        item_id = created_item.id
        await db_backend.commit_transaction()
    except Exception:
        await db_backend.rollback_transaction()
        raise

    assert item_id is not None
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, item_id)
    assert fetched_item is not None
    assert fetched_item.name == item_name

@pytest.mark.asyncio
async def test_transaction_rollback(db_backend: SQLAlchemyBackend):
    """Prueba que un rollback explícito revierte los cambios."""
    item_name = "Rollback Test Item"
    item_id = None # Inicializamos a None

    await db_backend.begin_transaction()
    try:
        created_item = await db_backend.create(ItemPydanticModel, {"name": item_name, "value": 701})
        item_id = created_item.id # Asignamos el ID aquí
        # No hacemos commit, forzamos rollback
        await db_backend.rollback_transaction()
    except Exception:
        # Si algo falla en el create, el rollback también debería ocurrir (o no ser necesario si no hubo flush)
        await db_backend.rollback_transaction() # Asegurar rollback en caso de error en create
        raise

    assert item_id is not None # El ID se asignó antes del rollback
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, item_id)
    assert fetched_item is None # El item no debería existir después del rollback

@pytest.mark.asyncio
async def test_transaction_context_manager_success(db_backend: SQLAlchemyBackend):
    """Prueba que el context manager hace commit en caso de éxito."""
    item_name = "Context Success Item"
    item_id = None
    async with db_backend.transaction():
        created_item = await db_backend.create(ItemPydanticModel, {"name": item_name, "value": 702})
        item_id = created_item.id
    
    assert item_id is not None
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, item_id)
    assert fetched_item is not None
    assert fetched_item.name == item_name

@pytest.mark.asyncio
async def test_transaction_context_manager_exception(db_backend: SQLAlchemyBackend):
    """Prueba que el context manager hace rollback si ocurre una excepción."""
    item_name = "Context Exception Item"
    item_id = None
    with pytest.raises(ValueError, match="Test exception for rollback"):
        async with db_backend.transaction():
            created_item = await db_backend.create(ItemPydanticModel, {"name": item_name, "value": 703})
            item_id = created_item.id
            raise ValueError("Test exception for rollback")
    
    assert item_id is not None # El ID se pudo haber asignado antes de la excepción
    fetched_item = await db_backend.get_by_id(ItemPydanticModel, item_id)
    assert fetched_item is None # El item no debería existir debido al rollback

# --- Pruebas de SQL Crudo ---

@pytest.mark.asyncio
async def test_fetch_all_raw(db_backend: SQLAlchemyBackend):
    """Prueba fetch_all_raw para obtener múltiples filas."""
    item1 = await db_backend.create(ItemPydanticModel, {"name": "Raw All 1", "value": 800, "is_active": True})
    item2 = await db_backend.create(ItemPydanticModel, {"name": "Raw All 2", "value": 801, "is_active": False})

    # Usar el nombre de la tabla real 'test_items'
    query = "SELECT id, name, value, is_active FROM test_items WHERE name LIKE :name_pattern ORDER BY value ASC"
    params = {"name_pattern": "Raw All %"}
    
    results = await db_backend.fetch_all_raw(query, params)
    
    assert len(results) == 2
    assert results[0]['name'] == "Raw All 1"
    assert results[0]['value'] == 800
    assert results[0]['is_active'] == 1 # SQLite devuelve 1/0 para booleanos en raw
    assert results[1]['name'] == "Raw All 2"
    assert results[1]['value'] == 801
    assert results[1]['is_active'] == 0 # SQLite devuelve 1/0 para booleanos en raw

@pytest.mark.asyncio
async def test_fetch_one_raw(db_backend: SQLAlchemyBackend):
    """Prueba fetch_one_raw para obtener una sola fila o None."""
    item1 = await db_backend.create(ItemPydanticModel, {"name": "Raw One Item", "value": 802})
    
    # Caso: item encontrado
    query_found = "SELECT id, name, value FROM test_items WHERE id = :item_id"
    params_found = {"item_id": item1.id}
    result_found = await db_backend.fetch_one_raw(query_found, params_found)
    
    assert result_found is not None
    assert result_found['id'] == item1.id
    assert result_found['name'] == "Raw One Item"
    assert result_found['value'] == 802

    # Caso: item no encontrado
    query_not_found = "SELECT id, name, value FROM test_items WHERE id = :item_id"
    params_not_found = {"item_id": 99999}
    result_not_found = await db_backend.fetch_one_raw(query_not_found, params_not_found)
    assert result_not_found is None

@pytest.mark.asyncio
async def test_execute_raw_update(db_backend: SQLAlchemyBackend):
    """Prueba execute_raw para una operación que no devuelve filas (UPDATE)."""
    item_to_update = await db_backend.create(ItemPydanticModel, {"name": "Before Raw Update", "value": 803})
    
    new_name = "After Raw Update"
    new_value = 804
    query = "UPDATE test_items SET name = :new_name, value = :new_value WHERE id = :item_id"
    params = {"new_name": new_name, "new_value": new_value, "item_id": item_to_update.id}
    
    # execute_raw debe devolver el rowcount para DML como UPDATE
    rowcount = await db_backend.execute_raw(query, params)
    assert rowcount == 1

    # Verificar con get_by_id que el cambio se aplicó
    updated_item = await db_backend.get_by_id(ItemPydanticModel, item_to_update.id)
    assert updated_item is not None
    assert updated_item.name == new_name
    assert updated_item.value == new_value

@pytest.mark.asyncio
async def test_execute_raw_no_rows_affected(db_backend: SQLAlchemyBackend):
    """Prueba execute_raw cuando una operación UPDATE no afecta filas."""
    query = "UPDATE test_items SET name = 'No Change' WHERE id = :item_id"
    params = {"item_id": 87654} # ID que no existe
    
    rowcount = await db_backend.execute_raw(query, params)
    assert rowcount == 0

# Fin de las pruebas para SQLAlchemyBackend
