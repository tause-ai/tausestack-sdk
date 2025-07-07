# QA y pruebas automatizadas para WompiService

## Estructura recomendada

- Ejecuta los tests desde el directorio `backend/` para que Python reconozca los paquetes correctamente.
- El archivo de pruebas está en: `app/payments/test_wompi_service.py`
- El servicio a probar está en: `app/payments/wompi_service.py`

## Comando recomendado

```bash
cd /Users/tause/Documents/proyectos/tausestack/templates/website/backend/
pytest -v app/payments/test_wompi_service.py
```

Esto garantiza que la importación `from payments.wompi_service import WompiService` funcione correctamente.

## Requisitos
- Python >= 3.8
- pytest
- requests
- Las llaves de sandbox deben estar en variables de entorno `WOMPI_PUBLIC_KEY` y `WOMPI_PRIVATE_KEY` (o se usarán valores dummy de prueba).

## Notas
- No modifiques la importación en el archivo de test salvo que cambies la estructura del proyecto.
- Si agregas más servicios o módulos, sigue esta estructura para asegurar compatibilidad y mantenibilidad.
