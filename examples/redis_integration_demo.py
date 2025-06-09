#!/usr/bin/env python3
"""
Demo de Integración Redis + MedGemma
Demuestra el flujo completo: Redis cache + protocolos + MedGemma local analysis.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import redis.asyncio as redis
import subprocess

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings


class RedisGemmaIntegrationDemo:
    """Demo de integración completa Redis + MedGemma."""
    
    def __init__(self):
        self.redis_client = None
        self.medgemma_model = "alibayram/medgemma"
    
    async def initialize(self):
        """Inicializar servicios."""
        try:
            print("🚀 Inicializando servicios...")
            
            # Conectar a Redis
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                ssl=settings.redis_ssl,
                decode_responses=True,
                db=settings.redis_db
            )
            
            await self.redis_client.ping()
            print("   ✅ Redis conectado")
            
            # Verificar MedGemma via Ollama
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                if self.medgemma_model in result.stdout:
                    print("   ✅ MedGemma disponible")
                else:
                    print("   ⚠️ MedGemma no disponible, usando respuestas simuladas")
                    self.medgemma_model = None
            except:
                print("   ⚠️ Ollama no disponible, usando respuestas simuladas")
                self.medgemma_model = None
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error en inicialización: {e}")
            return False
    
    async def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Buscar respuesta en cache."""
        try:
            cache_key = f"medical_cache:query:{hash(query) % 100000}"
            cached_data = await self.redis_client.hgetall(cache_key)
            
            if cached_data and cached_data.get("response"):
                response = json.loads(cached_data["response"])
                response["cache_hit"] = True
                response["cached_at"] = cached_data.get("created_at")
                return response
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error buscando en cache: {e}")
            return None
    
    async def get_relevant_protocols(self, query: str, category: str = None) -> list:
        """Obtener protocolos relevantes de Redis."""
        try:
            protocols = []
            
            if category:
                # Buscar por categoría específica
                protocol_ids = await self.redis_client.smembers(f"medical_protocols:category:{category}")
            else:
                # Buscar en todas las categorías
                treatment_ids = await self.redis_client.smembers("medical_protocols:category:treatment")
                prevention_ids = await self.redis_client.smembers("medical_protocols:category:prevention")
                emergency_ids = await self.redis_client.smembers("medical_protocols:category:emergency")
                protocol_ids = list(treatment_ids) + list(prevention_ids) + list(emergency_ids)
            
            # Obtener datos de cada protocolo
            for protocol_id in protocol_ids:
                protocol_data = await self.redis_client.hgetall(f"medical_protocol:{protocol_id}")
                if protocol_data:
                    protocols.append({
                        "id": protocol_id,
                        "title": protocol_data.get("title"),
                        "content": protocol_data.get("content"),
                        "category": protocol_data.get("category"),
                        "urgency": protocol_data.get("urgency")
                    })
            
            return protocols
            
        except Exception as e:
            print(f"   ⚠️ Error obteniendo protocolos: {e}")
            return []
    
    async def analyze_with_medgemma(self, query: str, protocols: list) -> Dict[str, Any]:
        """Analizar con MedGemma usando protocolos como contexto."""
        try:
            if not self.medgemma_model:
                # Respuesta simulada
                return {
                    "analysis": "Análisis simulado: Posible LPP grado 1-2 basado en descripción",
                    "recommendations": [
                        "Evaluación inmediata con escala de Braden",
                        "Cambios posturales cada 2 horas",
                        "Documentar evolución"
                    ],
                    "urgency": "moderate",
                    "confidence": 0.85,
                    "source": "simulated"
                }
            
            # Construir prompt con contexto de protocolos
            protocol_context = "\\n\\n".join([
                f"**{p['title']}** ({p['category']}):\\n{p['content'][:500]}..."
                for p in protocols[:2]  # Usar máximo 2 protocolos para no sobrecargar
            ])
            
            full_prompt = f"""
Basándote en los siguientes protocolos médicos, analiza esta consulta:

=== PROTOCOLOS MÉDICOS ===
{protocol_context}

=== CONSULTA MÉDICA ===
{query}

=== INSTRUCCIONES ===
Proporciona un análisis médico que incluya:
1. Evaluación del caso
2. Recomendaciones específicas basadas en los protocolos
3. Nivel de urgencia
4. Seguimiento necesario

Responde de manera profesional y estructurada.
"""
            
            # Ejecutar MedGemma
            result = subprocess.run([
                "ollama", "run", self.medgemma_model, full_prompt
            ], capture_output=True, text=True, timeout=45)
            
            if result.returncode == 0:
                analysis_text = result.stdout.strip()
                
                # Extraer información estructurada (análisis básico)
                urgency = "routine"
                if any(word in analysis_text.lower() for word in ["urgente", "emergencia", "inmediato"]):
                    urgency = "urgent"
                elif any(word in analysis_text.lower() for word in ["moderado", "pronto"]):
                    urgency = "moderate"
                
                return {
                    "analysis": analysis_text,
                    "recommendations": self._extract_recommendations(analysis_text),
                    "urgency": urgency,
                    "confidence": 0.9,
                    "source": "medgemma",
                    "protocols_used": len(protocols)
                }
            else:
                raise Exception(f"MedGemma error: {result.stderr}")
                
        except Exception as e:
            print(f"   ⚠️ Error en análisis MedGemma: {e}")
            # Fallback a respuesta simulada
            return {
                "analysis": f"Análisis basado en {len(protocols)} protocolos médicos disponibles",
                "recommendations": [
                    "Evaluación clínica completa",
                    "Seguimiento según protocolos estándar"
                ],
                "urgency": "routine",
                "confidence": 0.7,
                "source": "fallback"
            }
    
    def _extract_recommendations(self, text: str) -> list:
        """Extraer recomendaciones del texto de análisis."""
        recommendations = []
        lines = text.split('\\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                # Limpiar el texto
                clean_line = line.lstrip('-•123456789. ').strip()
                if clean_line and len(clean_line) > 10:
                    recommendations.append(clean_line)
        
        # Si no se encontraron recomendaciones estructuradas, extraer frases relevantes
        if not recommendations:
            sentences = text.split('.')
            for sentence in sentences:
                if any(word in sentence.lower() for word in ["recomienda", "debe", "evaluar", "aplicar"]):
                    clean_sentence = sentence.strip()
                    if clean_sentence and len(clean_sentence) > 20:
                        recommendations.append(clean_sentence)
        
        return recommendations[:5]  # Máximo 5 recomendaciones
    
    async def cache_response(self, query: str, response: Dict[str, Any]):
        """Guardar respuesta en cache."""
        try:
            cache_key = f"medical_cache:query:{hash(query) % 100000}"
            
            await self.redis_client.hset(cache_key, mapping={
                "query": query,
                "response": json.dumps(response),
                "created_at": "2025-01-09"
            })
            
            # TTL más corto para consultas clínicas (30 min)
            await self.redis_client.expire(cache_key, 1800)
            
            # Actualizar estadísticas
            await self.redis_client.hincrby("medical_cache:stats", "total_queries", 1)
            
        except Exception as e:
            print(f"   ⚠️ Error guardando en cache: {e}")
    
    async def process_medical_query(self, query: str) -> Dict[str, Any]:
        """Procesar consulta médica completa."""
        print(f"\\n🔍 Procesando: '{query}'")
        
        # 1. Buscar en cache
        print("   1. Buscando en cache...")
        cached_response = await self.get_cached_response(query)
        if cached_response:
            print("   ✅ Respuesta encontrada en cache")
            return cached_response
        
        print("   ❌ No encontrado en cache")
        
        # 2. Obtener protocolos relevantes
        print("   2. Obteniendo protocolos relevantes...")
        protocols = await self.get_relevant_protocols(query)
        print(f"   ✅ Encontrados {len(protocols)} protocolos")
        
        # 3. Analizar con MedGemma
        print("   3. Analizando con MedGemma...")
        analysis = await self.analyze_with_medgemma(query, protocols)
        print(f"   ✅ Análisis completado (fuente: {analysis['source']})")
        
        # 4. Preparar respuesta completa
        response = {
            "query": query,
            "analysis": analysis["analysis"],
            "recommendations": analysis["recommendations"],
            "urgency": analysis["urgency"],
            "confidence": analysis["confidence"],
            "protocols_consulted": len(protocols),
            "protocols_used": analysis.get("protocols_used", 0),
            "source": analysis["source"],
            "cache_hit": False,
            "processing_steps": ["cache_lookup", "protocol_search", "medgemma_analysis"]
        }
        
        # 5. Guardar en cache
        print("   4. Guardando en cache...")
        await self.cache_response(query, response)
        
        return response
    
    async def run_demo_scenarios(self):
        """Ejecutar escenarios de demostración."""
        
        scenarios = [
            {
                "name": "Consulta de Prevención",
                "query": "¿Cómo prevenir lesiones por presión en paciente encamado?",
                "expected_category": "prevention"
            },
            {
                "name": "Consulta de Tratamiento",
                "query": "Paciente de 75 años con eritema no blanqueable en sacro de 3x2 cm",
                "expected_category": "treatment"
            },
            {
                "name": "Consulta de Emergencia",
                "query": "LPP con exudado purulento y fiebre, signos de celulitis perilesional",
                "expected_category": "emergency"
            },
            {
                "name": "Consulta Repetida (Cache Test)",
                "query": "¿Cómo prevenir lesiones por presión en paciente encamado?",  # Misma que la primera
                "expected_category": "prevention"
            }
        ]
        
        print("\\n" + "="*70)
        print("🏥 DEMO DE INTEGRACIÓN REDIS + MEDGEMMA")
        print("="*70)
        
        results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\\n📋 ESCENARIO {i}: {scenario['name']}")
            print("-" * 50)
            
            result = await self.process_medical_query(scenario["query"])
            results.append(result)
            
            # Mostrar resultado
            print(f"\\n🔎 Resultado:")
            print(f"   Urgencia: {result['urgency']}")
            print(f"   Confianza: {result['confidence']}")
            print(f"   Protocolos consultados: {result['protocols_consulted']}")
            print(f"   Cache hit: {result['cache_hit']}")
            print(f"   Fuente: {result['source']}")
            
            if result['recommendations']:
                print("   Recomendaciones:")
                for rec in result['recommendations'][:3]:
                    print(f"     • {rec[:80]}...")
            
            print("\\n" + "="*50)
        
        return results
    
    async def show_final_stats(self):
        """Mostrar estadísticas finales."""
        try:
            print("\\n📊 ESTADÍSTICAS FINALES")
            print("-" * 30)
            
            # Stats de Redis
            info = await self.redis_client.info()
            print(f"Memoria Redis: {info.get('used_memory_human', 'N/A')}")
            
            # Stats de cache
            cache_stats = await self.redis_client.hgetall("medical_cache:stats")
            if cache_stats:
                print(f"Consultas totales: {cache_stats.get('total_queries', 0)}")
            
            # Protocolos disponibles
            protocol_keys = await self.redis_client.keys("medical_protocol:*")
            print(f"Protocolos médicos: {len(protocol_keys)}")
            
            # Entradas en cache
            cache_entries = await self.redis_client.keys("medical_cache:query:*")
            print(f"Entradas en cache: {len(cache_entries)}")
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
    
    async def cleanup(self):
        """Limpiar recursos."""
        try:
            if self.redis_client:
                await self.redis_client.aclose()
        except Exception as e:
            print(f"Error en cleanup: {e}")


async def main():
    """Función principal."""
    demo = RedisGemmaIntegrationDemo()
    
    try:
        if not await demo.initialize():
            return
        
        # Ejecutar escenarios de demo
        results = await demo.run_demo_scenarios()
        
        # Estadísticas finales
        await demo.show_final_stats()
        
        print("\\n✅ Demo de integración completado exitosamente")
        print("\\n💡 Flujo demostrado:")
        print("   1. Búsqueda en cache semántico")
        print("   2. Consulta de protocolos médicos en Redis")
        print("   3. Análisis con MedGemma local")
        print("   4. Cache de respuestas para consultas futuras")
        
    except KeyboardInterrupt:
        print("\\n⏹️ Demo interrumpida por usuario")
    except Exception as e:
        print(f"\\n❌ Error en demo: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    print("🔬 Iniciando demo de integración Redis + MedGemma...")
    print("Presiona Ctrl+C para interrumpir\\n")
    
    asyncio.run(main())