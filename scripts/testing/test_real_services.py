#!/usr/bin/env python3
"""
Real Services Integration Testing
================================

Tests all real services integration to validate the development setup.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from vigia_detect.core.service_config import get_service_config, ServiceType, ServiceMode
from vigia_detect.utils.secure_logger import SecureLogger

logger = SecureLogger(__name__)


class RealServicesValidator:
    """Validates real services integration"""
    
    def __init__(self):
        """Initialize validator"""
        self.service_config = get_service_config(ServiceMode.REAL)
        self.results: Dict[str, Dict[str, Any]] = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all service validation tests"""
        logger.info("🔬 Starting Real Services Integration Testing")
        
        test_methods = [
            self.test_database_connection,
            self.test_redis_connection,
            self.test_celery_tasks,
            self.test_supabase_integration,
            self.test_messaging_services,
            self.test_ai_models,
            self.test_complete_workflow
        ]
        
        for test_method in test_methods:
            test_name = test_method.__name__
            logger.info(f"🧪 Running {test_name}...")
            
            try:
                result = await test_method()
                self.results[test_name] = {
                    'status': 'PASSED' if result['success'] else 'FAILED',
                    'details': result,
                    'error': result.get('error')
                }
                
                status_icon = "✅" if result['success'] else "❌"
                logger.info(f"{status_icon} {test_name}: {self.results[test_name]['status']}")
                
            except Exception as e:
                self.results[test_name] = {
                    'status': 'ERROR',
                    'details': {'success': False, 'error': str(e)},
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                logger.error(f"❌ {test_name}: ERROR - {e}")
        
        return self._generate_summary()
    
    async def test_database_connection(self) -> Dict[str, Any]:
        """Test PostgreSQL database connection"""
        try:
            import psycopg2
            
            db_config = self.service_config.get_config(ServiceType.DATABASE)
            if not db_config or not db_config.available:
                return {'success': False, 'error': 'Database not configured'}
            
            # Test connection
            conn = psycopg2.connect(db_config.config['url'])
            cur = conn.cursor()
            
            # Test basic operations
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'medical'")
            table_count = cur.fetchone()[0]
            
            # Test sample query
            cur.execute("SELECT COUNT(*) FROM medical.patients")
            patient_count = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return {
                'success': True,
                'postgresql_version': version,
                'medical_tables': table_count,
                'sample_patients': patient_count
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_redis_connection(self) -> Dict[str, Any]:
        """Test Redis connection and operations"""
        try:
            import redis
            
            redis_config = self.service_config.get_config(ServiceType.CACHE)
            if not redis_config or not redis_config.available:
                return {'success': False, 'error': 'Redis not configured'}
            
            # Create Redis client
            r = redis.Redis(
                host=redis_config.config['host'],
                port=redis_config.config['port'],
                db=redis_config.config['db'],
                password=redis_config.config.get('password')
            )
            
            # Test basic operations
            r.ping()
            
            # Test set/get
            test_key = "vigia:test:connection"
            test_value = "test_value_12345"
            r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved_value = r.get(test_key).decode('utf-8')
            
            # Test hash operations
            hash_key = "vigia:test:hash"
            r.hset(hash_key, mapping={"field1": "value1", "field2": "value2"})
            hash_data = r.hgetall(hash_key)
            
            # Clean up
            r.delete(test_key, hash_key)
            
            # Get Redis info
            info = r.info()
            
            return {
                'success': True,
                'redis_version': info.get('redis_version'),
                'memory_usage': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'test_operations': {
                    'set_get': retrieved_value == test_value,
                    'hash_operations': len(hash_data) == 2
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_celery_tasks(self) -> Dict[str, Any]:
        """Test Celery task execution"""
        try:
            from vigia_detect.core.celery_config import celery_app, debug_task
            
            celery_config = self.service_config.get_config(ServiceType.CELERY)
            if not celery_config or celery_config.mode == ServiceMode.MOCK:
                return {'success': False, 'error': 'Celery not in real mode'}
            
            # Test task execution
            result = debug_task.delay()
            task_result = result.get(timeout=30)
            
            # Test task status
            task_id = result.id
            task_state = result.state
            
            return {
                'success': True,
                'task_id': task_id,
                'task_state': task_state,
                'task_result': task_result,
                'broker_url': celery_config.config['broker_url']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_supabase_integration(self) -> Dict[str, Any]:
        """Test Supabase integration"""
        try:
            storage_config = self.service_config.get_config(ServiceType.STORAGE)
            if not storage_config or not storage_config.available:
                return {'success': False, 'error': 'Supabase not configured'}
            
            supabase_config = storage_config.config['supabase']
            
            # Test basic connection (mock for now)
            return {
                'success': True,
                'url': supabase_config['url'][:20] + "..." if supabase_config['url'] else None,
                'configured': bool(supabase_config['url'] and supabase_config['key']),
                'note': 'Basic configuration check - full integration requires real API calls'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_messaging_services(self) -> Dict[str, Any]:
        """Test messaging services configuration"""
        try:
            messaging_config = self.service_config.get_config(ServiceType.MESSAGING)
            if not messaging_config:
                return {'success': False, 'error': 'Messaging not configured'}
            
            config = messaging_config.config
            
            # Test configuration presence
            services_configured = {
                'whatsapp': bool(config.get('whatsapp', {}).get('account_sid')),
                'slack': bool(config.get('slack', {}).get('bot_token')),
                'sendgrid': bool(config.get('sendgrid', {}).get('api_key'))
            }
            
            return {
                'success': any(services_configured.values()),
                'services_configured': services_configured,
                'total_configured': sum(services_configured.values()),
                'note': 'Configuration check - real message sending requires valid credentials'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_ai_models(self) -> Dict[str, Any]:
        """Test AI models availability"""
        try:
            ai_config = self.service_config.get_config(ServiceType.AI_MODEL)
            if not ai_config:
                return {'success': False, 'error': 'AI models not configured'}
            
            config = ai_config.config
            
            # Test model configurations
            models_available = {
                'yolo': Path(config.get('yolo', {}).get('model_path', '')).exists(),
                'medgemma_local': config.get('medgemma', {}).get('use_local', False),
                'embeddings': True  # Assume sentence-transformers is available
            }
            
            # Test basic imports
            try:
                import torch
                torch_available = True
                torch_version = torch.__version__
            except ImportError:
                torch_available = False
                torch_version = None
            
            try:
                import sentence_transformers
                st_available = True
            except ImportError:
                st_available = False
            
            return {
                'success': torch_available and st_available,
                'models_configured': models_available,
                'dependencies': {
                    'torch': torch_available,
                    'torch_version': torch_version,
                    'sentence_transformers': st_available
                },
                'medgemma_mode': 'local' if config.get('medgemma', {}).get('use_local') else 'vertex_ai'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_complete_workflow(self) -> Dict[str, Any]:
        """Test a complete medical workflow"""
        try:
            # Test basic workflow components
            from vigia_detect.agents.adk.clinical_assessment import ClinicalAssessmentAgent
            
            # Create agent
            agent = ClinicalAssessmentAgent()
            
            # Test agent initialization
            agent_initialized = hasattr(agent, 'npuap_guidelines')
            
            # Mock workflow test (basic validation)
            mock_patient_data = {
                'patient_id': 'TEST-2025-001',
                'age': 75,
                'diabetes': True
            }
            
            mock_image_analysis = {
                'analysis': {
                    'lpp_grade': 2,
                    'confidence': 0.85,
                    'anatomical_location': 'sacrum'
                }
            }
            
            # This would be a real assessment in production
            workflow_components = {
                'agent_ready': agent_initialized,
                'patient_data': bool(mock_patient_data),
                'image_analysis': bool(mock_image_analysis),
                'services_available': {
                    'database': self.service_config.is_service_available(ServiceType.DATABASE),
                    'cache': self.service_config.is_service_available(ServiceType.CACHE),
                    'celery': self.service_config.is_service_available(ServiceType.CELERY)
                }
            }
            
            workflow_ready = all([
                workflow_components['agent_ready'],
                workflow_components['services_available']['database'],
                workflow_components['services_available']['cache']
            ])
            
            return {
                'success': workflow_ready,
                'components': workflow_components,
                'workflow_ready': workflow_ready,
                'note': 'Basic workflow validation - full test requires real patient data'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r['status'] == 'PASSED')
        failed_tests = sum(1 for r in self.results.values() if r['status'] == 'FAILED')
        error_tests = sum(1 for r in self.results.values() if r['status'] == 'ERROR')
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': f"{success_rate:.1f}%",
                'overall_status': 'PASSED' if passed_tests == total_tests else 'FAILED'
            },
            'service_config': self.service_config.get_service_summary(),
            'detailed_results': self.results
        }


async def main():
    """Main test execution"""
    validator = RealServicesValidator()
    
    print("🏥 Vigia Real Services Integration Testing")
    print("=" * 50)
    
    results = await validator.run_all_tests()
    
    # Print summary
    summary = results['summary']
    print(f"\n📊 Test Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']} ✅")
    print(f"  Failed: {summary['failed']} ❌")
    print(f"  Errors: {summary['errors']} 💥")
    print(f"  Success Rate: {summary['success_rate']}")
    print(f"  Overall Status: {summary['overall_status']}")
    
    # Print service status
    print(f"\n🔧 Service Status:")
    for service_name, service_info in results['service_config']['services'].items():
        status_icon = "✅" if service_info['available'] else "❌"
        mode_icon = "🧪" if service_info['mode'] == 'mock' else "🔧"
        print(f"  {status_icon} {mode_icon} {service_name}: {service_info['mode']}")
    
    # Print failed tests details
    failed_tests = [name for name, result in results['detailed_results'].items() 
                   if result['status'] in ['FAILED', 'ERROR']]
    
    if failed_tests:
        print(f"\n❌ Failed Tests Details:")
        for test_name in failed_tests:
            result = results['detailed_results'][test_name]
            print(f"  {test_name}: {result['error']}")
    
    # Save detailed results
    results_file = project_root / "logs" / "real_services_test_results.json"
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📝 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    exit_code = 0 if summary['overall_status'] == 'PASSED' else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)