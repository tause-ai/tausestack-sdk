"""
AI Service Simple - Servicio básico de IA para agentes TauseStack

Este servicio proporciona respuestas simuladas mientras se configuran las APIs reales
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import random
import time


class AIRequest(BaseModel):
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    prompt: str
    tenant_id: str
    agent_id: Optional[str] = None


class AIResponse(BaseModel):
    response: str
    tokens_used: int
    model_used: str
    execution_time_ms: int
    tenant_id: str


class SimpleAIService:
    """Servicio de IA simple para desarrollo y testing"""
    
    def __init__(self):
        self.app = FastAPI(title="TauseStack Simple AI Service", version="1.0.0")
        self._setup_routes()
        
        # Plantillas de respuestas por tipo de prompt
        self.response_templates = {
            'explain': [
                "**{topic}** es un concepto importante que se caracteriza por {details}. \n\nEn el contexto de TauseStack, esto significa que podemos aprovechar {benefits} para crear soluciones más eficientes. Los principales beneficios incluyen:\n\n1. **Escalabilidad**: Capacidad de manejar múltiples tenants\n2. **Flexibilidad**: Adaptación a diferentes casos de uso\n3. **Eficiencia**: Optimización de recursos y costos\n\nEsto permite a los desarrolladores crear aplicaciones robustas que satisfacen las necesidades específicas de cada cliente.",
                
                "Para entender **{topic}**, es fundamental reconocer que {details}. \n\nEn el ecosistema TauseStack, esta tecnología se integra perfectamente con nuestros microservicios existentes, proporcionando {benefits}. Las ventajas clave son:\n\n• **Multi-tenancy nativo**: Aislamiento completo por cliente\n• **Integración perfecta**: Compatible con todas las APIs existentes\n• **Monitoreo avanzado**: Métricas detalladas en tiempo real\n\nEsto resulta en una plataforma más potente y versátil."
            ],
            
            'analyze': [
                "**Análisis detallado de {topic}:**\n\n**Fortalezas identificadas:**\n• {benefits}\n• Arquitectura escalable y modular\n• Integración nativa con sistemas existentes\n\n**Consideraciones importantes:**\n• Requiere configuración inicial cuidadosa\n• Necesita monitoreo continuo de rendimiento\n• Importante mantener actualización de dependencias\n\n**Recomendaciones:**\n1. Implementar en fases progresivas\n2. Establecer métricas de éxito claras\n3. Mantener documentación actualizada\n\n**Conclusión:** Esta implementación ofrece ventajas significativas para aplicaciones multi-tenant empresariales.",
                
                "**Evaluación técnica de {topic}:**\n\n**Aspectos positivos:**\n• {benefits}\n• Compatibilidad con estándares de la industria\n• Facilidad de mantenimiento y actualización\n\n**Áreas de mejora potencial:**\n• Optimización de memoria en cargas altas\n• Implementación de cache más agresivo\n• Mejora en el manejo de errores\n\n**Impacto en el negocio:**\n• Reducción de costos operativos\n• Mejor experiencia del usuario final\n• Mayor flexibilidad para nuevos clientes\n\n**Recomendación final:** Implementación recomendada con monitoreo proactivo."
            ],
            
            'describe': [
                "**{topic}** funciona mediante un sistema de {details} que permite {benefits}.\n\n**Componentes principales:**\n\n1. **Motor de procesamiento**: Maneja las solicitudes de manera asíncrona\n2. **Sistema de memoria**: Almacena contexto para cada tenant por separado\n3. **Gestor de herramientas**: Integra con las APIs y servicios existentes\n4. **Monitor de rendimiento**: Rastrea métricas y optimiza automaticamente\n\n**Flujo de funcionamiento:**\n• El sistema recibe una solicitud del tenant\n• Valida permisos y carga el contexto relevante\n• Procesa la información usando el modelo apropiado\n• Almacena los resultados en memoria persistente\n• Retorna la respuesta formateada\n\nEste diseño garantiza aislamiento completo entre tenants y máximo rendimiento.",
                
                "El funcionamiento de **{topic}** se basa en una arquitectura distribuida que {details} para lograr {benefits}.\n\n**Características técnicas:**\n\n• **Aislamiento por tenant**: Cada cliente tiene su propio espacio de trabajo\n• **Escalabilidad horizontal**: Puede crecer según la demanda\n• **Tolerancia a fallos**: Recuperación automática de errores\n• **Integración nativa**: Compatible con el ecosistema TauseStack\n\n**Proceso de ejecución:**\n1. **Inicialización**: Carga configuración específica del tenant\n2. **Validación**: Verifica permisos y recursos disponibles\n3. **Procesamiento**: Ejecuta la lógica de negocio\n4. **Persistencia**: Guarda resultados y actualiza métricas\n5. **Respuesta**: Formatea y envía el resultado final\n\nEsta implementación asegura rendimiento óptimo y seguridad empresarial."
            ]
        }
    
    def _setup_routes(self):
        """Configurar rutas del API"""
        
        @self.app.post("/ai/completion", response_model=AIResponse)
        async def generic_completion(request: AIRequest):
            """Endpoint genérico de completion"""
            return await self._process_request(request)
        
        @self.app.post("/ai/openai/completion", response_model=AIResponse)
        async def openai_completion(request: AIRequest):
            """Endpoint específico para OpenAI"""
            request.model = "gpt-4" if not request.model else request.model
            return await self._process_request(request)
        
        @self.app.post("/ai/claude/completion", response_model=AIResponse)
        async def claude_completion(request: AIRequest):
            """Endpoint específico para Claude"""
            request.model = "claude-3-sonnet-20240229" if not request.model else request.model
            return await self._process_request(request)
        
        @self.app.get("/ai/health")
        async def health_check():
            """Health check del servicio"""
            return {"status": "healthy", "service": "simple_ai", "version": "1.0.0"}
        
        @self.app.get("/ai/models")
        async def list_models():
            """Listar modelos disponibles"""
            return {
                "models": [
                    {"id": "gpt-4", "provider": "openai", "status": "available"},
                    {"id": "gpt-3.5-turbo", "provider": "openai", "status": "available"},
                    {"id": "claude-3-sonnet-20240229", "provider": "anthropic", "status": "available"},
                    {"id": "claude-3-haiku-20240307", "provider": "anthropic", "status": "available"}
                ]
            }
    
    async def _process_request(self, request: AIRequest) -> AIResponse:
        """Procesar solicitud de IA"""
        
        start_time = time.time()
        
        try:
            # Simular latencia realista
            await self._simulate_processing_time(request)
            
            # Generar respuesta basada en el prompt
            response_text = self._generate_response(request.prompt)
            
            # Calcular métricas simuladas
            tokens_used = self._calculate_tokens(request.prompt, response_text)
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                response=response_text,
                tokens_used=tokens_used,
                model_used=request.model,
                execution_time_ms=execution_time,
                tenant_id=request.tenant_id
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing AI request: {str(e)}")
    
    async def _simulate_processing_time(self, request: AIRequest):
        """Simular tiempo de procesamiento realista"""
        import asyncio
        
        # Tiempo base según modelo
        base_time = 0.5 if "gpt" in request.model.lower() else 0.8
        
        # Ajustar según longitud del prompt
        prompt_factor = min(len(request.prompt) / 1000, 2.0)
        
        # Añadir variabilidad
        random_factor = random.uniform(0.8, 1.2)
        
        total_time = base_time * (1 + prompt_factor) * random_factor
        
        await asyncio.sleep(total_time)
    
    def _generate_response(self, prompt: str) -> str:
        """Generar respuesta inteligente basada en el prompt"""
        
        prompt_lower = prompt.lower()
        
        # Detectar tipo de solicitud
        if any(word in prompt_lower for word in ['qué es', 'what is', 'explica', 'explain']):
            response_type = 'explain'
        elif any(word in prompt_lower for word in ['analiza', 'analyze', 'evalúa', 'evaluate']):
            response_type = 'analyze'
        elif any(word in prompt_lower for word in ['describe', 'cómo funciona', 'how does']):
            response_type = 'describe'
        else:
            response_type = 'explain'  # Por defecto
        
        # Extraer tema principal
        topic = self._extract_topic(prompt)
        details = self._generate_details(topic)
        benefits = self._generate_benefits(topic)
        
        # Seleccionar plantilla
        templates = self.response_templates[response_type]
        template = random.choice(templates)
        
        # Formatear respuesta
        response = template.format(
            topic=topic,
            details=details,
            benefits=benefits
        )
        
        # Agregar firma del agente
        response += f"\n\n---\n*Respuesta generada por TauseStack Agent Engine*"
        
        return response
    
    def _extract_topic(self, prompt: str) -> str:
        """Extraer tema principal del prompt"""
        
        # Buscar palabras clave comunes
        keywords = {
            'tausestack': 'TauseStack',
            'agente': 'Agentes de IA',
            'agent': 'AI Agents',
            'multi-tenant': 'Arquitectura Multi-tenant',
            'memoria': 'Sistema de Memoria',
            'memory': 'Memory System',
            'api': 'APIs y Servicios',
            'microservicio': 'Microservicios',
            'microservice': 'Microservices',
            'ecommerce': 'Plataforma E-commerce',
            'payment': 'Sistema de Pagos',
            'wompi': 'Integración Wompi',
            'saleor': 'Integración Saleor'
        }
        
        prompt_lower = prompt.lower()
        
        for keyword, topic in keywords.items():
            if keyword in prompt_lower:
                return topic
        
        # Si no encuentra nada específico, usar un término genérico
        return "Sistema TauseStack"
    
    def _generate_details(self, topic: str) -> str:
        """Generar detalles específicos del tema"""
        
        details_map = {
            'TauseStack': 'una plataforma de desarrollo multi-tenant que integra servicios de IA, analytics y gestión de datos',
            'Agentes de IA': 'entidades autónomas que pueden ejecutar tareas complejas usando modelos de lenguaje avanzados',
            'Arquitectura Multi-tenant': 'un diseño que permite aislar completamente los datos y configuraciones de cada cliente',
            'Sistema de Memoria': 'un mecanismo de persistencia que mantiene el contexto de las conversaciones por tenant',
            'APIs y Servicios': 'interfaces programáticas que facilitan la integración con sistemas externos',
            'Microservicios': 'componentes independientes que se comunican mediante APIs REST bien definidas',
            'Plataforma E-commerce': 'un conjunto de servicios especializados en comercio electrónico y gestión de inventarios',
            'Sistema de Pagos': 'una infraestructura segura para procesar transacciones financieras',
            'Integración Wompi': 'conectividad nativa con la pasarela de pagos líder en Colombia',
            'Integración Saleor': 'compatibilidad completa con la plataforma de e-commerce de código abierto'
        }
        
        return details_map.get(topic, 'un componente avanzado del ecosistema TauseStack')
    
    def _generate_benefits(self, topic: str) -> str:
        """Generar beneficios específicos del tema"""
        
        benefits_map = {
            'TauseStack': 'escalabilidad automática, reducción de costos de desarrollo y tiempo de comercialización acelerado',
            'Agentes de IA': 'automatización inteligente, procesamiento de lenguaje natural y aprendizaje continuo',
            'Arquitectura Multi-tenant': 'aislamiento de datos, optimización de recursos y gestión centralizada',
            'Sistema de Memoria': 'contexto persistente, experiencias personalizadas y aprendizaje adaptativo',
            'APIs y Servicios': 'integración flexible, interoperabilidad y escalabilidad modular',
            'Microservicios': 'independencia de despliegue, escalabilidad granular y mantenimiento simplificado',
            'Plataforma E-commerce': 'gestión de inventarios en tiempo real, experiencia de compra optimizada y analytics avanzados',
            'Sistema de Pagos': 'transacciones seguras, soporte multi-moneda y reconciliación automática',
            'Integración Wompi': 'procesamiento local de pagos, cumplimiento regulatorio colombiano y tarifas competitivas',
            'Integración Saleor': 'flexibilidad de personalización, escalabilidad empresarial y ecosistema de plugins'
        }
        
        return benefits_map.get(topic, 'eficiencia mejorada, escalabilidad y facilidad de uso')
    
    def _calculate_tokens(self, prompt: str, response: str) -> int:
        """Calcular tokens aproximados"""
        # Aproximación: 1 token ≈ 4 caracteres en español
        total_chars = len(prompt) + len(response)
        return int(total_chars / 4)


# Instancia global del servicio
ai_service = SimpleAIService()

# Exportar la app para uso en el servidor principal
app = ai_service.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 