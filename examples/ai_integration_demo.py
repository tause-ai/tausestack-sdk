#!/usr/bin/env python3
"""
Demo de AI Integration - TauseStack v0.9.0

Demuestra las capacidades de integración con IA:
- Generación de componentes React
- Debugging de código
- Mejora de templates
- Chat con IA
- Múltiples opciones de generación
"""
import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tausestack.sdk.ai.clients.ai_client import AIClient, GenerationStrategy


class AIIntegrationDemo:
    """Demo de integración con IA"""
    
    def __init__(self):
        self.ai_client = None
        self.session_id = "demo_session_2024"
        self.results = {}
    
    async def setup(self):
        """Configuración inicial"""
        print("🤖 TauseStack AI Integration Demo v0.9.0")
        print("=" * 60)
        
        # Inicializar cliente de IA
        self.ai_client = AIClient("http://localhost:8005")
        
        # Verificar que el servicio esté disponible
        health = await self.ai_client.health_check()
        if health.get("status") != "healthy":
            print("❌ AI Services no está disponible")
            print("   Ejecuta: python scripts/start_ai_services.py")
            return False
        
        print("✅ AI Services conectado")
        
        # Configurar sesión
        self.ai_client.set_session_id(self.session_id)
        
        return True
    
    async def demo_component_generation(self):
        """Demo: Generación de componentes React"""
        print("\n🎨 Demo 1: Generación de Componentes React")
        print("-" * 40)
        
        # Ejemplo 1: Botón con loading
        print("\n📝 Generando: Botón moderno con loading state...")
        
        try:
            result = await self.ai_client.generate_component(
                description="Un botón moderno con estado de loading y variantes de color",
                component_type="button",
                required_props=["children", "onClick"],
                features=["loading state", "color variants", "size variants", "disabled state"],
                styling_preferences="modern tailwind with shadcn/ui",
                strategy=GenerationStrategy.QUALITY
            )
            
            print(f"✅ Generado con {result.provider} ({result.model})")
            print(f"   Tokens: {result.tokens_used}, Tiempo: {result.response_time:.2f}s")
            print(f"   Calidad: {result.quality_score:.1f}/10")
            
            if result.suggestions:
                print(f"   Sugerencias: {len(result.suggestions)}")
                for i, suggestion in enumerate(result.suggestions[:2], 1):
                    print(f"     {i}. {suggestion}")
            
            self.results["button_component"] = {
                "code": result.code,
                "provider": result.provider,
                "quality": result.quality_score
            }
            
            # Mostrar código generado (primeras líneas)
            lines = result.code.split('\n')[:10]
            print("\n📄 Código generado (preview):")
            for line in lines:
                print(f"   {line}")
            if len(result.code.split('\n')) > 10:
                print("   ...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Ejemplo 2: Dashboard component
        print("\n📝 Generando: Dashboard de métricas...")
        
        try:
            result = await self.ai_client.generate_component(
                description="Dashboard de métricas con gráficos y KPIs",
                component_type="dashboard",
                required_props=["data", "timeRange"],
                features=["responsive design", "interactive charts", "export functionality"],
                styling_preferences="professional dark theme",
                strategy=GenerationStrategy.BALANCED
            )
            
            print(f"✅ Generado con {result.provider}")
            print(f"   Tokens: {result.tokens_used}, Calidad: {result.quality_score:.1f}/10")
            
            self.results["dashboard_component"] = {
                "code": result.code,
                "provider": result.provider,
                "quality": result.quality_score
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_api_generation(self):
        """Demo: Generación de endpoints API"""
        print("\n🔗 Demo 2: Generación de APIs")
        print("-" * 40)
        
        print("\n📝 Generando: API de gestión de usuarios...")
        
        try:
            result = await self.ai_client.generate_api_endpoint(
                description="Endpoint para crear un nuevo usuario con validación",
                http_method="POST",
                route="/api/users",
                parameters=["name", "email", "password", "role"]
            )
            
            print(f"✅ API generada con {result.provider}")
            print(f"   Tokens: {result.tokens_used}, Tiempo: {result.response_time:.2f}s")
            
            # Mostrar código generado (preview)
            lines = result.code.split('\n')[:15]
            print("\n📄 Código de API generado (preview):")
            for line in lines:
                print(f"   {line}")
            
            self.results["user_api"] = {
                "code": result.code,
                "provider": result.provider
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_code_debugging(self):
        """Demo: Debugging de código"""
        print("\n🐛 Demo 3: Debugging de Código")
        print("-" * 40)
        
        # Código con error típico
        buggy_code = """
const UserList = ({ users }) => {
    return (
        <div>
            {users.map(user => (
                <div key={user.id}>
                    <h3>{user.name}</h3>
                    <p>{user.email}</p>
                </div>
            )}
        </div>
    );
};

// Error: users puede ser undefined
UserList({ users: undefined });
"""
        
        error_message = "TypeError: Cannot read properties of undefined (reading 'map')"
        
        print("📝 Debuggeando código con error...")
        print(f"   Error: {error_message}")
        
        try:
            result = await self.ai_client.debug_code(
                error_code=buggy_code,
                error_message=error_message,
                context="React component that renders a list of users"
            )
            
            print(f"✅ Debuggeado con {result.provider}")
            print(f"   Tokens: {result.tokens_used}")
            
            if result.explanation:
                print(f"\n💡 Explicación del problema:")
                print(f"   {result.explanation}")
            
            if result.suggestions:
                print(f"\n🔧 Sugerencias de mejora:")
                for i, suggestion in enumerate(result.suggestions, 1):
                    print(f"   {i}. {suggestion}")
            
            # Mostrar código corregido (preview)
            if result.code:
                lines = result.code.split('\n')[:10]
                print("\n📄 Código corregido (preview):")
                for line in lines:
                    print(f"   {line}")
            
            self.results["debugged_code"] = {
                "code": result.code,
                "explanation": result.explanation,
                "suggestions": result.suggestions
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_template_enhancement(self):
        """Demo: Mejora de templates"""
        print("\n⚡ Demo 4: Mejora de Templates")
        print("-" * 40)
        
        # Template básico para mejorar
        basic_template = """
import React from 'react';

const Card = ({ title, content }) => {
    return (
        <div className="card">
            <h2>{title}</h2>
            <p>{content}</p>
        </div>
    );
};

export default Card;
"""
        
        improvement_goals = [
            "Add TypeScript support",
            "Improve accessibility",
            "Add responsive design",
            "Include loading and error states",
            "Add animation support"
        ]
        
        print("📝 Mejorando template básico...")
        print(f"   Objetivos: {len(improvement_goals)} mejoras")
        
        try:
            result = await self.ai_client.enhance_template(
                template_code=basic_template,
                improvement_goals=improvement_goals
            )
            
            print(f"✅ Template mejorado con {result.provider}")
            print(f"   Tokens: {result.tokens_used}, Tiempo: {result.response_time:.2f}s")
            
            if result.suggestions:
                print(f"\n📋 Recomendaciones adicionales:")
                for i, suggestion in enumerate(result.suggestions[:3], 1):
                    print(f"   {i}. {suggestion}")
            
            # Mostrar código mejorado (preview)
            lines = result.code.split('\n')[:15]
            print("\n📄 Template mejorado (preview):")
            for line in lines:
                print(f"   {line}")
            
            self.results["enhanced_template"] = {
                "code": result.code,
                "provider": result.provider,
                "improvements": improvement_goals
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_multiple_options(self):
        """Demo: Generación de múltiples opciones"""
        print("\n🎯 Demo 5: Múltiples Opciones de Generación")
        print("-" * 40)
        
        print("📝 Generando 3 opciones de modal component...")
        
        try:
            result = await self.ai_client.generate_multiple_options(
                description="Modal component with overlay and close functionality",
                component_type="modal",
                required_props=["isOpen", "onClose", "children"],
                features=["overlay", "close button", "escape key", "click outside"],
                styling_preferences="modern and accessible",
                num_options=3,
                strategy=GenerationStrategy.MULTI_PROVIDER
            )
            
            if result["success"]:
                options = result["options"]
                best_index = result["best_option_index"]
                
                print(f"✅ {len(options)} opciones generadas")
                print(f"   Mejor opción: #{best_index + 1}")
                print(f"   Costo total: ${result['total_cost']:.4f}")
                
                for i, option in enumerate(options):
                    print(f"\n   Opción {i + 1}: {option['provider']} "
                          f"(Calidad: {option['quality_score']:.1f}/10)")
                    if i == best_index:
                        print("     ⭐ MEJOR OPCIÓN")
                
                self.results["multiple_options"] = {
                    "options_count": len(options),
                    "best_option": best_index,
                    "total_cost": result["total_cost"],
                    "comparison": result["comparison_notes"]
                }
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_ai_chat(self):
        """Demo: Chat con IA"""
        print("\n💬 Demo 6: Chat con IA")
        print("-" * 40)
        
        questions = [
            "¿Cuáles son las mejores prácticas para React hooks?",
            "¿Cómo optimizar el rendimiento de una aplicación React?",
            "¿Qué es el patrón compound component?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n❓ Pregunta {i}: {question}")
            
            try:
                result = await self.ai_client.chat(
                    message=question,
                    context_type="react_development"
                )
                
                print(f"🤖 Respuesta ({result['provider']}):")
                # Mostrar solo las primeras líneas de la respuesta
                response_lines = result["response"].split('\n')[:5]
                for line in response_lines:
                    if line.strip():
                        print(f"   {line}")
                
                print(f"   Tokens: {result['tokens_used']}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def demo_performance_test(self):
        """Demo: Test de rendimiento"""
        print("\n⚡ Demo 7: Test de Rendimiento")
        print("-" * 40)
        
        # Test de múltiples requests concurrentes
        print("📝 Ejecutando 5 generaciones concurrentes...")
        
        tasks = []
        start_time = time.time()
        
        for i in range(5):
            task = self.ai_client.generate_component(
                description=f"Simple component #{i+1}",
                component_type="component",
                strategy=GenerationStrategy.FAST
            )
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful = [r for r in results if not isinstance(r, Exception)]
            failed = [r for r in results if isinstance(r, Exception)]
            
            print(f"✅ Completado en {end_time - start_time:.2f}s")
            print(f"   Exitosos: {len(successful)}/{len(tasks)}")
            print(f"   Fallidos: {len(failed)}")
            
            if successful:
                avg_tokens = sum(r.tokens_used for r in successful) / len(successful)
                avg_time = sum(r.response_time for r in successful) / len(successful)
                total_cost = sum(r.cost_estimate for r in successful)
                
                print(f"   Promedio tokens: {avg_tokens:.0f}")
                print(f"   Promedio tiempo: {avg_time:.2f}s")
                print(f"   Costo total: ${total_cost:.4f}")
            
            self.results["performance_test"] = {
                "concurrent_requests": len(tasks),
                "successful": len(successful),
                "failed": len(failed),
                "total_time": end_time - start_time
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def show_service_stats(self):
        """Muestra estadísticas del servicio"""
        print("\n📊 Estadísticas del Servicio")
        print("-" * 40)
        
        try:
            stats = await self.ai_client.get_stats()
            providers = await self.ai_client.get_providers()
            
            print(f"Total requests: {stats.get('total_requests', 0)}")
            print(f"Successful: {stats.get('successful_generations', 0)}")
            print(f"Success rate: {stats.get('success_rate', 0):.1f}%")
            print(f"Avg response time: {stats.get('avg_response_time', 0):.2f}s")
            print(f"Total cost: ${stats.get('total_cost', 0):.4f}")
            
            print(f"\nProveedores activos:")
            for provider, info in providers.get("providers", {}).items():
                status = info.get("status", "unknown")
                print(f"   {provider}: {status}")
            
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
    
    async def show_demo_summary(self):
        """Muestra resumen del demo"""
        print("\n🎉 Resumen del Demo")
        print("=" * 60)
        
        demos_completed = len(self.results)
        print(f"✅ Demos completados: {demos_completed}")
        
        if "button_component" in self.results:
            print(f"🎨 Componente generado: Calidad {self.results['button_component']['quality']:.1f}/10")
        
        if "multiple_options" in self.results:
            options = self.results["multiple_options"]
            print(f"🎯 Opciones múltiples: {options['options_count']} generadas")
        
        if "performance_test" in self.results:
            perf = self.results["performance_test"]
            print(f"⚡ Performance: {perf['successful']}/{perf['concurrent_requests']} exitosos")
        
        print("\n🚀 TauseStack AI Integration está listo para:")
        print("   • Generación de componentes React/TypeScript")
        print("   • Debugging inteligente de código")
        print("   • Mejora automática de templates")
        print("   • Chat asistido por IA")
        print("   • Múltiples proveedores de IA")
        print("   • Procesamiento concurrente")
        
        print("\n📚 Próximos pasos:")
        print("   1. Integrar con Visual Builder")
        print("   2. Implementar generación de proyectos completos")
        print("   3. Agregar más proveedores de IA")
        print("   4. Optimizar prompts para casos específicos")
        
        print(f"\n💰 Estimación de costos para este demo: ~$0.10-0.50")
        print("🔗 Documentación: http://localhost:8005/docs")
    
    async def cleanup(self):
        """Limpieza final"""
        if self.ai_client:
            await self.ai_client.close()
    
    async def run_demo(self):
        """Ejecuta el demo completo"""
        try:
            # Setup
            if not await self.setup():
                return
            
            # Ejecutar demos
            await self.demo_component_generation()
            await self.demo_api_generation()
            await self.demo_code_debugging()
            await self.demo_template_enhancement()
            await self.demo_multiple_options()
            await self.demo_ai_chat()
            await self.demo_performance_test()
            
            # Estadísticas y resumen
            await self.show_service_stats()
            await self.show_demo_summary()
            
        except KeyboardInterrupt:
            print("\n🛑 Demo interrumpido por el usuario")
        except Exception as e:
            print(f"\n❌ Error en demo: {e}")
        finally:
            await self.cleanup()


async def main():
    """Función principal"""
    demo = AIIntegrationDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())