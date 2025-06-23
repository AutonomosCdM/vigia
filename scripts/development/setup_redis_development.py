#!/usr/bin/env python3
"""
Setup Redis para desarrollo - Configuración completa de vector search y cache
Configura Redis con índices vectoriales y cache semántico para el sistema Vigia.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import redis
import time

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from vigia_detect.redis_layer.client_v2 import MedicalRedisClient
from vigia_detect.redis_layer.vector_service import VectorService
from vigia_detect.redis_layer.cache_service_v2 import CacheServiceV2
from vigia_detect.utils.secure_logger import SecureLogger
from config.settings import settings

logger = SecureLogger("redis_setup")


class RedisDevSetup:
    """Configurador de Redis para desarrollo."""
    
    def __init__(self):
        self.medical_client = None
        self.vector_service = None
        self.cache_service = None
        
        # Protocolos médicos de prueba
        self.medical_protocols = [
            {
                "id": "lpp_prevention_001",
                "title": "Protocolo de Prevención de LPP en UCI",
                "content": """
                Protocolo estándar para prevención de lesiones por presión en UCI:
                
                1. Evaluación de riesgo:
                   - Escala de Braden cada 8 horas
                   - Factores de riesgo: movilidad, humedad, fricción
                   
                2. Intervenciones preventivas:
                   - Cambios posturales cada 2 horas
                   - Superficies de redistribución de presión
                   - Cuidado de la piel con productos específicos
                   
                3. Zonas de riesgo prioritarias:
                   - Sacro y cóccix
                   - Talones
                   - Trocánteres
                   - Prominencias óseas
                """,
                "category": "prevention",
                "urgency": "routine",
                "evidence_level": "A"
            },
            {
                "id": "lpp_grade2_treatment_001", 
                "title": "Tratamiento de LPP Grado 2",
                "content": """
                Protocolo de tratamiento para lesiones por presión grado 2:
                
                1. Evaluación inicial:
                   - Medición y fotografía de la lesión
                   - Evaluación del lecho de la herida
                   - Descarte de infección
                   
                2. Limpieza y cuidado:
                   - Limpieza con suero fisiológico
                   - Desbridamiento si es necesario
                   - Aplicación de apósito apropiado
                   
                3. Manejo del dolor:
                   - Analgésicos sistémicos si es necesario
                   - Técnicas de aplicación de apósitos sin dolor
                   
                4. Seguimiento:
                   - Evaluación diaria
                   - Documentación de progreso
                   - Escalamiento si no hay mejoría en 72h
                """,
                "category": "treatment",
                "urgency": "urgent", 
                "evidence_level": "A"
            },
            {
                "id": "lpp_emergency_protocol",
                "title": "Protocolo de Emergencia LPP",
                "content": """
                Protocolo para lesiones por presión con signos de alarma:
                
                1. Signos de alarma:
                   - Celulitis perilesional
                   - Fiebre o signos sistémicos
                   - Dolor desproporcional
                   - Olor fétido o exudado purulento
                   
                2. Acciones inmediatas:
                   - Evaluación médica urgente
                   - Cultivo de la lesión
                   - Antibióticos sistémicos si indicado
                   - Consideración de hospitalización
                   
                3. Manejo especializado:
                   - Interconsulta a cirugía plástica
                   - Evaluación nutricional
                   - Optimización de comorbilidades
                """,
                "category": "emergency",
                "urgency": "emergency",
                "evidence_level": "B"
            },
            {
                "id": "lpp_nutrition_protocol",
                "title": "Protocolo Nutricional para LPP",
                "content": """
                Soporte nutricional en pacientes con lesiones por presión:
                
                1. Evaluación nutricional:
                   - Índice de masa corporal
                   - Albúmina sérica
                   - Valoración del estado nutricional
                   
                2. Requerimientos específicos:
                   - Proteínas: 1.2-1.5 g/kg/día
                   - Vitamina C: 500-1000 mg/día
                   - Zinc: 8-11 mg/día
                   - Vitamina A: si deficiencia
                   
                3. Monitoreo:
                   - Peso corporal semanal
                   - Laboratorios nutricionales mensuales
                   - Evaluación de cicatrización
                """,
                "category": "nutrition",
                "urgency": "routine",
                "evidence_level": "B"
            }
        ]
    
    async def initialize_clients(self):
        """Inicializar clientes Redis."""
        try:
            logger.info("Initializing Redis clients...")
            
            # Cliente médico principal
            self.medical_client = MedicalRedisClient()
            
            # Verificar conexión básica usando redis directo
            import redis.asyncio as redis
            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                ssl=settings.redis_ssl,
                decode_responses=True
            )
            
            # Test conexión
            await redis_client.ping()
            
            # Servicios especializados con cliente directo para setup
            from vigia_detect.redis_layer.vector_service import VectorService
            from vigia_detect.redis_layer.cache_service_v2 import CacheServiceV2
            
            self.vector_service = VectorService()
            self.cache_service = CacheServiceV2()
            
            logger.info("Redis clients initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis clients: {e}")
            return False
    
    async def check_redis_status(self):
        """Verificar estado de Redis."""
        try:
            info = await self.redis_client.info()
            
            print("📊 Estado de Redis:")
            print(f"   Versión: {info.get('redis_version', 'N/A')}")
            print(f"   Modo: {info.get('redis_mode', 'N/A')}")
            print(f"   Uptime: {info.get('uptime_in_seconds', 0)} segundos")
            print(f"   Memoria usada: {info.get('used_memory_human', 'N/A')}")
            print(f"   Conexiones: {info.get('connected_clients', 0)}")
            
            # Verificar bases de datos
            dbs = [k for k in info.keys() if k.startswith('db')]
            if dbs:
                print(f"   Bases de datos: {dbs}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check Redis status: {e}")
            return False
    
    async def setup_vector_indices(self):
        """Configurar índices vectoriales."""
        try:
            print("\n🔍 Configurando índices vectoriales...")
            
            # Crear índice para protocolos médicos
            index_name = settings.redis_vector_index
            vector_dim = settings.redis_vector_dim
            
            # Verificar si el índice ya existe
            try:
                await self.vector_service.get_index_info(index_name)
                print(f"   ✅ Índice {index_name} ya existe")
            except:
                # Crear nuevo índice
                await self.vector_service.create_index(
                    index_name=index_name,
                    vector_dim=vector_dim,
                    distance_metric="COSINE"
                )
                print(f"   ✅ Índice {index_name} creado exitosamente")
            
            # Crear índice para cache semántico
            cache_index = settings.redis_cache_index
            try:
                await self.vector_service.get_index_info(cache_index)
                print(f"   ✅ Índice de cache {cache_index} ya existe")
            except:
                await self.vector_service.create_index(
                    index_name=cache_index,
                    vector_dim=vector_dim,
                    distance_metric="COSINE"
                )
                print(f"   ✅ Índice de cache {cache_index} creado")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup vector indices: {e}")
            return False
    
    async def load_medical_protocols(self):
        """Cargar protocolos médicos de prueba."""
        try:
            print("\n📚 Cargando protocolos médicos...")
            
            loaded_count = 0
            for protocol in self.medical_protocols:
                # Verificar si ya existe
                existing = await self.vector_service.search_similar(
                    query_text=protocol["title"],
                    index_name=settings.redis_vector_index,
                    top_k=1,
                    threshold=0.95
                )
                
                if existing and len(existing) > 0:
                    print(f"   ⏭️ Protocolo '{protocol['title']}' ya existe")
                    continue
                
                # Almacenar protocolo
                await self.vector_service.store_document(
                    doc_id=protocol["id"],
                    content=protocol["content"],
                    metadata={
                        "title": protocol["title"],
                        "category": protocol["category"],
                        "urgency": protocol["urgency"],
                        "evidence_level": protocol["evidence_level"],
                        "type": "medical_protocol"
                    },
                    index_name=settings.redis_vector_index
                )
                
                loaded_count += 1
                print(f"   ✅ Cargado: {protocol['title']}")
            
            print(f"\n📊 Protocolos cargados: {loaded_count}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load medical protocols: {e}")
            return False
    
    async def test_vector_search(self):
        """Probar búsqueda vectorial."""
        try:
            print("\n🔍 Probando búsqueda vectorial...")
            
            test_queries = [
                "prevención de lesiones por presión",
                "tratamiento de LPP grado 2", 
                "signos de infección en heridas",
                "nutrición para cicatrización"
            ]
            
            for query in test_queries:
                print(f"\n   🔎 Consulta: '{query}'")
                
                results = await self.vector_service.search_similar(
                    query_text=query,
                    index_name=settings.redis_vector_index,
                    top_k=2,
                    threshold=0.7
                )
                
                if results:
                    for i, result in enumerate(results, 1):
                        score = result.get('score', 0)
                        title = result.get('metadata', {}).get('title', 'N/A')
                        category = result.get('metadata', {}).get('category', 'N/A')
                        print(f"      {i}. {title} (categoría: {category}, score: {score:.3f})")
                else:
                    print("      No se encontraron resultados relevantes")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to test vector search: {e}")
            return False
    
    async def test_semantic_cache(self):
        """Probar cache semántico."""
        try:
            print("\n💾 Probando cache semántico...")
            
            # Almacenar consulta en cache
            test_query = "¿Cuáles son los signos de una LPP grado 2?"
            test_response = {
                "diagnosis": "LPP grado 2",
                "signs": ["eritema no blanqueable", "pérdida de dermis", "úlcera superficial"],
                "recommendations": ["cambios posturales", "apósitos húmedos", "evaluación médica"],
                "urgency": "moderate"
            }
            
            # Guardar en cache
            await self.cache_service.set_semantic_cache(
                query=test_query,
                response=test_response,
                ttl=3600
            )
            print(f"   ✅ Consulta guardada en cache: '{test_query}'")
            
            # Probar recuperación exacta
            cached_exact = await self.cache_service.get_semantic_cache(test_query)
            if cached_exact:
                print(f"   ✅ Recuperación exacta exitosa")
            
            # Probar recuperación semántica
            similar_query = "¿Qué signos presenta una lesión por presión de segundo grado?"
            cached_semantic = await self.cache_service.get_semantic_cache(similar_query)
            if cached_semantic:
                print(f"   ✅ Recuperación semántica exitosa para query similar")
            else:
                print(f"   ⚠️ No se encontró match semántico para query similar")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to test semantic cache: {e}")
            return False
    
    async def test_integration_workflow(self):
        """Probar flujo de trabajo integrado."""
        try:
            print("\n🔄 Probando flujo integrado...")
            
            # Simular consulta médica completa
            patient_query = "Paciente de 75 años con eritema no blanqueable en sacro"
            
            # 1. Buscar en cache semántico
            print("   1. Buscando en cache semántico...")
            cached_response = await self.cache_service.get_semantic_cache(patient_query)
            
            if cached_response:
                print("   ✅ Respuesta encontrada en cache")
                return True
            
            # 2. Buscar protocolos relevantes
            print("   2. Buscando protocolos relevantes...")
            protocols = await self.vector_service.search_similar(
                query_text=patient_query,
                index_name=settings.redis_vector_index,
                top_k=3,
                threshold=0.6
            )
            
            if protocols:
                print(f"   ✅ Encontrados {len(protocols)} protocolos relevantes")
                for protocol in protocols:
                    title = protocol.get('metadata', {}).get('title', 'N/A')
                    category = protocol.get('metadata', {}).get('category', 'N/A')
                    score = protocol.get('score', 0)
                    print(f"      - {title} ({category}) - Score: {score:.3f}")
            
            # 3. Simular respuesta médica generada
            medical_response = {
                "assessment": "Posible LPP grado 1-2 en zona de riesgo",
                "protocols_found": len(protocols) if protocols else 0,
                "recommendations": [
                    "Evaluación inmediata con escala de Braden",
                    "Implementar cambios posturales cada 2 horas", 
                    "Aplicar superficie de redistribución de presión",
                    "Documentar evolución cada 8 horas"
                ],
                "urgency_level": "moderate",
                "follow_up": "24 horas"
            }
            
            # 4. Guardar respuesta en cache
            print("   3. Guardando respuesta en cache...")
            await self.cache_service.set_semantic_cache(
                query=patient_query,
                response=medical_response,
                ttl=1800  # 30 minutos para consultas clínicas
            )
            
            print("   ✅ Flujo integrado completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Failed to test integration workflow: {e}")
            return False
    
    async def get_system_stats(self):
        """Obtener estadísticas del sistema."""
        try:
            print("\n📊 Estadísticas del sistema:")
            
            # Stats de Redis
            info = await self.redis_client.info()
            print(f"   Memoria Redis: {info.get('used_memory_human', 'N/A')}")
            print(f"   Comandos ejecutados: {info.get('total_commands_processed', 'N/A')}")
            
            # Stats de índices vectoriales
            try:
                index_info = await self.vector_service.get_index_info(settings.redis_vector_index)
                print(f"   Documentos en índice vectorial: {index_info.get('num_docs', 0)}")
            except:
                print("   Índice vectorial: No disponible")
            
            # Stats de cache
            cache_keys = await self.redis_client.keys(f"{settings.redis_cache_index}:*")
            print(f"   Entradas en cache semántico: {len(cache_keys)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return False
    
    async def cleanup(self):
        """Limpiar recursos."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            logger.info("Redis setup cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


async def main():
    """Función principal."""
    print("🚀 Redis Development Setup")
    print("=" * 50)
    
    setup = RedisDevSetup()
    
    try:
        # Inicializar
        if not await setup.initialize_clients():
            print("❌ Error al inicializar clientes Redis")
            return
        
        # Verificar estado
        await setup.check_redis_status()
        
        # Configurar índices
        if not await setup.setup_vector_indices():
            print("❌ Error al configurar índices vectoriales")
            return
        
        # Cargar protocolos
        if not await setup.load_medical_protocols():
            print("❌ Error al cargar protocolos médicos")
            return
        
        # Probar funcionalidades
        await setup.test_vector_search()
        await setup.test_semantic_cache()
        await setup.test_integration_workflow()
        
        # Estadísticas finales
        await setup.get_system_stats()
        
        print("\n" + "=" * 50)
        print("✅ Configuración de Redis completada exitosamente")
        print("\n💡 Servicios disponibles:")
        print("   - Búsqueda vectorial de protocolos médicos")
        print("   - Cache semántico para consultas")
        print("   - Integración completa para flujos clínicos")
        
        print("\n🔧 Para usar en el sistema:")
        print("   from vigia_detect.redis_layer.client_v2 import RedisClientV2")
        print("   from vigia_detect.redis_layer.vector_service import VectorService")
        print("   from vigia_detect.redis_layer.cache_service_v2 import CacheServiceV2")
        
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error en setup: {e}")
        logger.error(f"Setup failed: {e}")
    finally:
        await setup.cleanup()


if __name__ == "__main__":
    asyncio.run(main())