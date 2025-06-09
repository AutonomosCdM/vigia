#!/usr/bin/env python3
"""
Setup Redis Simple - Configuración básica para desarrollo
Configura Redis con funcionalidades básicas sin dependencias complejas.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import redis.asyncio as redis

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings


class SimpleRedisSetup:
    """Configurador simple de Redis para desarrollo."""
    
    def __init__(self):
        self.redis_client = None
        
        # Protocolos médicos básicos
        self.medical_protocols = {
            "lpp_prevention": {
                "title": "Protocolo de Prevención de LPP",
                "content": """
                Protocolo estándar para prevención de lesiones por presión:
                
                1. Evaluación de riesgo cada 8 horas con escala de Braden
                2. Cambios posturales cada 2 horas
                3. Superficies de redistribución de presión
                4. Cuidado de la piel con productos específicos
                5. Monitoreo de zonas de riesgo: sacro, talones, trocánteres
                """,
                "category": "prevention",
                "urgency": "routine"
            },
            "lpp_grade2_treatment": {
                "title": "Tratamiento de LPP Grado 2",
                "content": """
                Protocolo de tratamiento para lesiones por presión grado 2:
                
                1. Evaluación y medición de la lesión
                2. Limpieza con suero fisiológico
                3. Aplicación de apósito apropiado
                4. Manejo del dolor
                5. Seguimiento cada 24 horas
                6. Escalamiento si no mejora en 72h
                """,
                "category": "treatment",
                "urgency": "urgent"
            },
            "lpp_emergency": {
                "title": "Protocolo de Emergencia LPP",
                "content": """
                Para lesiones con signos de alarma:
                
                1. Signos: celulitis, fiebre, dolor intenso, exudado purulento
                2. Evaluación médica urgente
                3. Cultivo de la lesión
                4. Antibióticos sistémicos si indicado
                5. Interconsulta especializada
                """,
                "category": "emergency",
                "urgency": "emergency"
            }
        }
    
    async def initialize(self):
        """Inicializar cliente Redis."""
        try:
            print("🔗 Conectando a Redis...")
            
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                ssl=settings.redis_ssl,
                decode_responses=True,
                db=settings.redis_db
            )
            
            # Test conexión
            await self.redis_client.ping()
            print("✅ Conexión a Redis establecida")
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            return False
    
    async def check_redis_status(self):
        """Verificar estado de Redis."""
        try:
            info = await self.redis_client.info()
            
            print("\n📊 Estado de Redis:")
            print(f"   Versión: {info.get('redis_version', 'N/A')}")
            print(f"   Uptime: {info.get('uptime_in_seconds', 0)} segundos")
            print(f"   Memoria usada: {info.get('used_memory_human', 'N/A')}")
            print(f"   Conexiones: {info.get('connected_clients', 0)}")
            print(f"   Base de datos: {settings.redis_db}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verificando estado: {e}")
            return False
    
    async def load_medical_protocols(self):
        """Cargar protocolos médicos básicos."""
        try:
            print("\n📚 Cargando protocolos médicos...")
            
            loaded_count = 0
            for protocol_id, protocol_data in self.medical_protocols.items():
                # Clave en Redis
                key = f"medical_protocol:{protocol_id}"
                
                # Verificar si ya existe
                exists = await self.redis_client.exists(key)
                if exists:
                    print(f"   ⏭️ Protocolo '{protocol_data['title']}' ya existe")
                    continue
                
                # Almacenar protocolo
                await self.redis_client.hset(key, mapping={
                    "title": protocol_data["title"],
                    "content": protocol_data["content"],
                    "category": protocol_data["category"],
                    "urgency": protocol_data["urgency"],
                    "created_at": "2025-01-09"
                })
                
                # Agregar a índice por categoría
                category_key = f"medical_protocols:category:{protocol_data['category']}"
                await self.redis_client.sadd(category_key, protocol_id)
                
                # Agregar a índice por urgencia
                urgency_key = f"medical_protocols:urgency:{protocol_data['urgency']}"
                await self.redis_client.sadd(urgency_key, protocol_id)
                
                loaded_count += 1
                print(f"   ✅ Cargado: {protocol_data['title']}")
            
            print(f"\n📊 Protocolos cargados: {loaded_count}")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando protocolos: {e}")
            return False
    
    async def setup_cache_structure(self):
        """Configurar estructura de cache."""
        try:
            print("\n💾 Configurando cache semántico...")
            
            # Configurar TTL por defecto para cache médico
            cache_ttl = settings.redis_cache_ttl
            
            # Crear índices para cache
            cache_indices = [
                "medical_cache:queries",
                "medical_cache:responses", 
                "medical_cache:stats"
            ]
            
            for index in cache_indices:
                # Verificar si existe
                exists = await self.redis_client.exists(index)
                if not exists:
                    # Inicializar con metadata
                    await self.redis_client.hset(index, mapping={
                        "created_at": "2025-01-09",
                        "ttl_default": str(cache_ttl),
                        "type": "medical_cache_index"
                    })
                    print(f"   ✅ Índice creado: {index}")
            
            # Configurar estadísticas de cache
            stats_key = "medical_cache:stats"
            await self.redis_client.hset(stats_key, mapping={
                "total_queries": "0",
                "cache_hits": "0",
                "cache_misses": "0",
                "last_reset": "2025-01-09"
            })
            
            print("   ✅ Estructura de cache configurada")
            return True
            
        except Exception as e:
            print(f"❌ Error configurando cache: {e}")
            return False
    
    async def test_basic_operations(self):
        """Probar operaciones básicas."""
        try:
            print("\n🧪 Probando operaciones básicas...")
            
            # 1. Test de búsqueda de protocolos
            print("   1. Búsqueda de protocolos por categoría...")
            treatment_protocols = await self.redis_client.smembers("medical_protocols:category:treatment")
            print(f"      Protocolos de tratamiento: {len(treatment_protocols)}")
            
            # 2. Test de recuperación de protocolo específico
            print("   2. Recuperación de protocolo específico...")
            protocol_data = await self.redis_client.hgetall("medical_protocol:lpp_grade2_treatment")
            if protocol_data:
                print(f"      Protocolo recuperado: {protocol_data.get('title', 'N/A')}")
            
            # 3. Test de cache simple
            print("   3. Test de cache...")
            test_query = "¿Cuáles son los signos de LPP grado 2?"
            test_response = {
                "signs": ["eritema no blanqueable", "pérdida de dermis", "úlcera superficial"],
                "recommendations": ["cambios posturales", "apósitos húmedos"],
                "cached_at": "2025-01-09"
            }
            
            # Guardar en cache
            cache_key = f"medical_cache:query:{hash(test_query) % 100000}"
            await self.redis_client.hset(cache_key, mapping={
                "query": test_query,
                "response": json.dumps(test_response),
                "created_at": "2025-01-09"
            })
            await self.redis_client.expire(cache_key, settings.redis_cache_ttl)
            
            # Recuperar de cache
            cached_data = await self.redis_client.hgetall(cache_key)
            if cached_data:
                print("      ✅ Cache funcionando correctamente")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en pruebas: {e}")
            return False
    
    async def test_medical_workflow(self):
        """Probar flujo médico completo."""
        try:
            print("\n🏥 Probando flujo médico...")
            
            # Simular consulta médica
            patient_query = "Paciente con eritema en sacro que no blanquea"
            
            print(f"   Consulta: {patient_query}")
            
            # 1. Buscar protocolos relevantes
            print("   1. Buscando protocolos relevantes...")
            
            # Buscar por categoría
            prevention_protocols = await self.redis_client.smembers("medical_protocols:category:prevention")
            treatment_protocols = await self.redis_client.smembers("medical_protocols:category:treatment")
            
            relevant_protocols = []
            
            # Obtener datos de protocolos de prevención y tratamiento
            for protocol_id in list(prevention_protocols) + list(treatment_protocols):
                protocol_data = await self.redis_client.hgetall(f"medical_protocol:{protocol_id}")
                if protocol_data:
                    relevant_protocols.append({
                        "id": protocol_id,
                        "title": protocol_data.get("title"),
                        "category": protocol_data.get("category")
                    })
            
            print(f"      Protocolos encontrados: {len(relevant_protocols)}")
            for protocol in relevant_protocols[:3]:
                print(f"      - {protocol['title']} ({protocol['category']})")
            
            # 2. Generar respuesta médica
            medical_response = {
                "assessment": "Posible LPP grado 1-2 en zona de riesgo",
                "protocols_consulted": len(relevant_protocols),
                "recommendations": [
                    "Evaluación inmediata con escala de Braden",
                    "Implementar cambios posturales cada 2 horas",
                    "Aplicar superficie de redistribución de presión"
                ],
                "urgency_level": "moderate",
                "follow_up": "24 horas"
            }
            
            # 3. Guardar en cache
            print("   2. Guardando respuesta en cache...")
            cache_key = f"medical_cache:query:{hash(patient_query) % 100000}"
            await self.redis_client.hset(cache_key, mapping={
                "query": patient_query,
                "response": json.dumps(medical_response),
                "protocols_used": json.dumps([p["id"] for p in relevant_protocols]),
                "created_at": "2025-01-09"
            })
            await self.redis_client.expire(cache_key, 1800)  # 30 minutos
            
            # 4. Actualizar estadísticas
            await self.redis_client.hincrby("medical_cache:stats", "total_queries", 1)
            
            print("   ✅ Flujo médico completado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error en flujo médico: {e}")
            return False
    
    async def get_system_stats(self):
        """Obtener estadísticas del sistema."""
        try:
            print("\n📊 Estadísticas del sistema:")
            
            # Stats de Redis
            info = await self.redis_client.info()
            print(f"   Memoria Redis: {info.get('used_memory_human', 'N/A')}")
            print(f"   Comandos ejecutados: {info.get('total_commands_processed', 'N/A')}")
            
            # Stats de protocolos
            protocol_keys = await self.redis_client.keys("medical_protocol:*")
            print(f"   Protocolos médicos: {len(protocol_keys)}")
            
            # Stats de cache
            cache_keys = await self.redis_client.keys("medical_cache:query:*")
            print(f"   Entradas en cache: {len(cache_keys)}")
            
            # Stats específicas de cache médico
            cache_stats = await self.redis_client.hgetall("medical_cache:stats")
            if cache_stats:
                print(f"   Consultas totales: {cache_stats.get('total_queries', 0)}")
                print(f"   Cache hits: {cache_stats.get('cache_hits', 0)}")
                print(f"   Cache misses: {cache_stats.get('cache_misses', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return False
    
    async def cleanup(self):
        """Limpiar recursos."""
        try:
            if self.redis_client:
                await self.redis_client.aclose()
            print("🧹 Recursos liberados")
        except Exception as e:
            print(f"⚠️ Error en cleanup: {e}")


async def main():
    """Función principal."""
    print("🚀 Redis Simple Setup")
    print("=" * 50)
    
    setup = SimpleRedisSetup()
    
    try:
        # Inicializar
        if not await setup.initialize():
            return
        
        # Verificar estado
        await setup.check_redis_status()
        
        # Configurar estructura
        await setup.setup_cache_structure()
        
        # Cargar protocolos
        await setup.load_medical_protocols()
        
        # Probar operaciones
        await setup.test_basic_operations()
        await setup.test_medical_workflow()
        
        # Estadísticas finales
        await setup.get_system_stats()
        
        print("\n" + "=" * 50)
        print("✅ Configuración de Redis completada exitosamente")
        print("\n💡 Servicios disponibles:")
        print("   - Almacenamiento de protocolos médicos")
        print("   - Cache de consultas médicas")
        print("   - Búsqueda por categoría y urgencia")
        print("   - Estadísticas de uso")
        
        print("\n🔧 Claves de Redis disponibles:")
        print("   medical_protocol:{id} - Protocolos médicos")
        print("   medical_cache:query:{hash} - Cache de consultas")
        print("   medical_protocols:category:{cat} - Índice por categoría")
        print("   medical_protocols:urgency:{urg} - Índice por urgencia")
        
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error en setup: {e}")
    finally:
        await setup.cleanup()


if __name__ == "__main__":
    asyncio.run(main())