# Contribuir a TauseStack SDK

¡Gracias por tu interés en contribuir a TauseStack SDK! Este documento te guiará sobre cómo contribuir al proyecto.

## 🚀 Cómo Empezar

### Configuración del Entorno

1. **Fork del repositorio**
   ```bash
   git clone https://github.com/tu-usuario/tausestack-sdk.git
   cd tausestack-sdk
   ```

2. **Configurar entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -e .[dev]
   ```

4. **Ejecutar tests**
   ```bash
   pytest
   ```

## 📋 Tipos de Contribuciones

### 🐛 Reportar Bugs
- Usa el template de issue para bugs
- Incluye pasos para reproducir
- Especifica versión de Python y OS
- Adjunta logs si es posible

### 💡 Nuevas Funcionalidades
- Abre un issue primero para discutir
- Sigue los patrones de arquitectura existentes
- Incluye tests y documentación
- Mantén compatibilidad con multi-tenant

### 📚 Documentación
- Mejoras en README, docstrings
- Ejemplos de uso
- Guías de deployment
- Traducciones

### 🔧 Mejoras de Código
- Optimizaciones de performance
- Refactoring
- Mejoras de seguridad
- Compatibilidad con nuevas versiones

## 🏗️ Proceso de Desarrollo

### 1. Crear Branch
```bash
git checkout -b feature/nueva-funcionalidad
# o
git checkout -b bugfix/arreglar-problema
```

### 2. Hacer Cambios
- Sigue las convenciones de código
- Escribe tests para nuevas funcionalidades
- Actualiza documentación si es necesario

### 3. Ejecutar Tests
```bash
# Tests unitarios
pytest tests/unit/

# Tests de integración
pytest tests/integration/

# Tests completos
pytest

# Coverage
pytest --cov=tausestack
```

### 4. Verificar Calidad
```bash
# Formateo
black tausestack/
isort tausestack/

# Linting
flake8 tausestack/
mypy tausestack/
```

### 5. Commit y Push
```bash
git add .
git commit -m "feat: agregar nueva funcionalidad X"
git push origin feature/nueva-funcionalidad
```

### 6. Crear Pull Request
- Usa el template de PR
- Describe qué cambios hiciste
- Referencia issues relacionados
- Incluye screenshots si aplica

## 📝 Convenciones de Código

### Estilo de Código
- **Formateo**: Black (line-length=88)
- **Imports**: isort
- **Linting**: flake8
- **Type hints**: mypy

### Naming Conventions
```python
# Variables y funciones: snake_case
user_name = "juan"
def get_user_data():
    pass

# Clases: PascalCase
class UserManager:
    pass

# Constantes: UPPER_CASE
MAX_RETRIES = 3
```

### Docstrings
```python
def create_payment(amount: int, currency: str) -> dict:
    """
    Crear un pago con la pasarela configurada.
    
    Args:
        amount: Monto en centavos
        currency: Código de moneda (COP, USD, etc.)
        
    Returns:
        dict: Datos del pago creado
        
    Raises:
        PaymentError: Si el pago falla
        
    Example:
        >>> payment = create_payment(50000, "COP")
        >>> print(payment["status"])
        "pending"
    """
```

### Estructura de Tests
```python
# tests/test_payments.py
import pytest
from tausestack.payments import create_payment

class TestPayments:
    def test_create_payment_success(self):
        """Test crear pago exitoso."""
        payment = create_payment(50000, "COP")
        assert payment["status"] == "pending"
        assert payment["amount"] == 50000
    
    def test_create_payment_invalid_amount(self):
        """Test crear pago con monto inválido."""
        with pytest.raises(ValueError):
            create_payment(-100, "COP")
```

## 🔄 Mensajes de Commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<scope>): <descripción>

[cuerpo opcional]

[footer opcional]
```

### Tipos
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo, punto y coma faltante, etc.
- `refactor`: Refactoring de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

### Ejemplos
```
feat(auth): agregar autenticación con Firebase
fix(storage): corregir error de conexión S3
docs(readme): actualizar instrucciones de instalación
test(billing): agregar tests para facturación
```

## 🧪 Testing

### Estructura de Tests
```
tests/
├── unit/           # Tests unitarios
├── integration/    # Tests de integración
├── fixtures/       # Datos de prueba
└── conftest.py     # Configuración pytest
```

### Categorías de Tests
- **Unit**: Tests aislados de funciones/clases
- **Integration**: Tests de componentes trabajando juntos
- **E2E**: Tests completos de extremo a extremo

### Marcadores de Tests
```python
@pytest.mark.unit
def test_function():
    pass

@pytest.mark.integration
def test_service_integration():
    pass

@pytest.mark.slow
def test_heavy_operation():
    pass
```

## 📦 Releases

### Versionado
Seguimos [Semantic Versioning](https://semver.org/):
- **MAJOR**: Cambios incompatibles
- **MINOR**: Nueva funcionalidad compatible
- **PATCH**: Correcciones compatibles

### Proceso de Release
1. Actualizar CHANGELOG.md
2. Bump version en pyproject.toml
3. Crear tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. GitHub Actions construye y publica automáticamente

## 🏷️ Labels en Issues/PRs

- `bug`: Reportes de bugs
- `enhancement`: Nuevas funcionalidades
- `documentation`: Mejoras en docs
- `good first issue`: Ideal para nuevos contribuidores
- `help wanted`: Necesita ayuda de la comunidad
- `priority-high`: Alta prioridad
- `colombia`: Funcionalidades específicas para Colombia

## 🤝 Código de Conducta

### Nuestros Valores
- **Respeto**: Trata a todos con respeto y profesionalismo
- **Inclusión**: Todos son bienvenidos, sin importar experiencia
- **Colaboración**: Trabajamos juntos hacia objetivos comunes
- **Calidad**: Nos esforzamos por código de alta calidad

### Comportamiento Esperado
- Usa lenguaje inclusivo y profesional
- Acepta críticas constructivas
- Enfócate en lo que es mejor para la comunidad
- Muestra empatía hacia otros miembros

### Comportamiento Inaceptable
- Lenguaje ofensivo o discriminatorio
- Ataques personales o políticos
- Acoso público o privado
- Spam o contenido inapropiado

## 📞 Contacto

- **Issues**: [GitHub Issues](https://github.com/tausestack/tausestack-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tausestack/tausestack-sdk/discussions)
- **Email**: support@tausestack.dev
- **Discord**: [TauseStack Community](https://discord.gg/tausestack)

## 🙏 Reconocimientos

¡Gracias a todos los contribuidores que hacen posible TauseStack SDK!

---

**¿Tienes dudas?** No dudes en abrir un issue o contactarnos. ¡Estamos aquí para ayudar!
