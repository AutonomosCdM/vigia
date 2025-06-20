#!/usr/bin/env python3
"""
Vigia System Validation Script - Consolidated
Combines functionality from validate_post_refactor.py and validate_post_refactor_simple.py
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemValidator:
    """Comprehensive system validation for Vigia medical system."""
    
    def __init__(self, verbose: bool = False, quick: bool = False):
        """Initialize system validator."""
        self.verbose = verbose
        self.quick = quick
        self.results = {}
        self.start_time = time.time()
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def log(self, message: str, level: str = "info"):
        """Log message with appropriate level."""
        if level == "debug" and self.verbose:
            logger.debug(message)
        elif level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        
        if self.verbose:
            print(f"[{level.upper()}] {message}")
    
    def validate_imports(self) -> Dict[str, bool]:
        """Validate critical system imports."""
        self.log("🔍 Validating system imports...")
        
        import_tests = {
            "ADK Agents": [
                "vigia_detect.agents.base_agent",
                "vigia_detect.agents.image_analysis_agent", 
                "vigia_detect.agents.clinical_assessment_agent",
                "vigia_detect.agents.protocol_agent",
                "vigia_detect.agents.communication_agent"
            ],
            "Medical Systems": [
                "vigia_detect.systems.medical_decision_engine",
                "vigia_detect.systems.minsal_medical_decision_engine"
            ],
            "Core Components": [
                "vigia_detect.core.async_pipeline",
                "vigia_detect.cv_pipeline.detector",
                "vigia_detect.cv_pipeline.preprocessor"
            ],
            "AI Integration": [
                "vigia_detect.ai.medgemma_client"
            ],
            "Messaging": [
                "vigia_detect.api.mcp_twilio",
                "vigia_detect.webhook.server"
            ]
        }
        
        results = {}
        
        for category, modules in import_tests.items():
            self.log(f"  Testing {category}...")
            category_results = {}
            
            for module in modules:
                try:
                    __import__(module)
                    category_results[module] = True
                    self.log(f"    ✅ {module}", "debug")
                except ImportError as e:
                    category_results[module] = False
                    self.log(f"    ❌ {module}: {e}", "warning")
            
            results[category] = category_results
            success_count = sum(category_results.values())
            total_count = len(category_results)
            self.log(f"  {category}: {success_count}/{total_count} imports successful")
        
        self.results['imports'] = results
        return results
    
    def validate_medical_decision_engine(self) -> Dict[str, Any]:
        """Validate medical decision engine functionality."""
        self.log("🏥 Validating medical decision engine...")
        
        try:
            from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine
            
            engine = MedicalDecisionEngine()
            
            # Test medical decision
            test_decision = engine.make_clinical_decision(
                lpp_grade=2,
                confidence=0.85,
                anatomical_location="sacrum"
            )
            
            # Validate decision structure
            required_fields = ['urgency_level', 'evidence_level', 'clinical_recommendations']
            validation_results = {}
            
            for field in required_fields:
                has_field = hasattr(test_decision, field)
                validation_results[field] = has_field
                if has_field:
                    self.log(f"    ✅ {field}: {getattr(test_decision, field)}", "debug")
                else:
                    self.log(f"    ❌ Missing field: {field}", "warning")
            
            # Test evidence references
            has_evidence = hasattr(test_decision, 'evidence_references')
            validation_results['evidence_references'] = has_evidence
            
            if has_evidence and test_decision.evidence_references:
                self.log(f"    ✅ Evidence references: {len(test_decision.evidence_references)} found", "debug")
            else:
                self.log("    ⚠️  No evidence references found", "warning")
            
            success_rate = sum(validation_results.values()) / len(validation_results)
            self.log(f"  Medical decision engine: {success_rate:.1%} validation success")
            
            return {
                "engine_available": True,
                "validation_results": validation_results,
                "success_rate": success_rate,
                "test_decision": str(test_decision) if hasattr(test_decision, '__str__') else "Available"
            }
            
        except Exception as e:
            self.log(f"  ❌ Medical decision engine validation failed: {e}", "error")
            return {
                "engine_available": False,
                "error": str(e)
            }
    
    def validate_adk_agents(self) -> Dict[str, Any]:
        """Validate ADK agent system."""
        self.log("🤖 Validating ADK agent system...")
        
        try:
            from vigia_detect.agents.base_agent import BaseAgent, AgentMessage, AgentResponse
            
            # Test agent message structure
            test_message = AgentMessage(
                message_id="test_001",
                sender_id="validator",
                recipient_id="test_agent", 
                message_type="validation_test",
                content={"test": "data"}
            )
            
            message_validation = {
                "has_message_id": hasattr(test_message, 'message_id'),
                "has_sender_id": hasattr(test_message, 'sender_id'),
                "has_content": hasattr(test_message, 'content'),
                "content_serializable": isinstance(test_message.content, dict)
            }
            
            # Test specific agents
            agent_tests = {}
            agent_modules = [
                ("ImageAnalysisAgent", "vigia_detect.agents.image_analysis_agent"),
                ("ClinicalAssessmentAgent", "vigia_detect.agents.clinical_assessment_agent"),
                ("ProtocolAgent", "vigia_detect.agents.protocol_agent")
            ]
            
            for agent_name, module_path in agent_modules:
                try:
                    module = __import__(module_path, fromlist=[agent_name])
                    agent_class = getattr(module, agent_name)
                    
                    # Check if it inherits from BaseAgent
                    is_base_agent = issubclass(agent_class, BaseAgent)
                    agent_tests[agent_name] = {
                        "importable": True,
                        "inherits_base_agent": is_base_agent,
                        "has_process_message": hasattr(agent_class, 'process_message')
                    }
                    
                    self.log(f"    ✅ {agent_name}: Valid ADK agent", "debug")
                    
                except Exception as e:
                    agent_tests[agent_name] = {
                        "importable": False,
                        "error": str(e)
                    }
                    self.log(f"    ❌ {agent_name}: {e}", "warning")
            
            success_count = sum(1 for test in agent_tests.values() if test.get('importable', False))
            total_count = len(agent_tests)
            self.log(f"  ADK agents: {success_count}/{total_count} agents valid")
            
            return {
                "message_validation": message_validation,
                "agent_tests": agent_tests,
                "success_rate": success_count / total_count if total_count > 0 else 0
            }
            
        except Exception as e:
            self.log(f"  ❌ ADK agent validation failed: {e}", "error")
            return {
                "available": False,
                "error": str(e)
            }
    
    def validate_async_pipeline(self) -> Dict[str, Any]:
        """Validate asynchronous pipeline functionality."""
        self.log("⚡ Validating async pipeline...")
        
        try:
            from vigia_detect.core.async_pipeline import AsyncPipeline
            
            # Test pipeline creation
            pipeline = AsyncPipeline()
            
            # Basic validation
            validation_results = {
                "pipeline_created": pipeline is not None,
                "has_process_method": hasattr(pipeline, 'process'),
                "has_async_support": asyncio.iscoroutinefunction(getattr(pipeline, 'process', None))
            }
            
            success_rate = sum(validation_results.values()) / len(validation_results)
            self.log(f"  Async pipeline: {success_rate:.1%} validation success")
            
            return {
                "validation_results": validation_results,
                "success_rate": success_rate
            }
            
        except Exception as e:
            self.log(f"  ❌ Async pipeline validation failed: {e}", "error")
            return {
                "available": False,
                "error": str(e)
            }
    
    def validate_cv_pipeline(self) -> Dict[str, Any]:
        """Validate computer vision pipeline."""
        self.log("🖼️  Validating CV pipeline...")
        
        try:
            from vigia_detect.cv_pipeline.detector import LPPDetector
            from vigia_detect.cv_pipeline.preprocessor import ImagePreprocessor
            
            # Test detector
            detector_tests = {}
            try:
                detector = LPPDetector(model_type='yolov5s', conf_threshold=0.25)
                detector_tests = {
                    "detector_created": True,
                    "has_detect_method": hasattr(detector, 'detect'),
                    "has_model_info": hasattr(detector, 'get_model_info')
                }
                self.log("    ✅ LPP Detector initialized", "debug")
            except Exception as e:
                detector_tests = {"detector_created": False, "error": str(e)}
                self.log(f"    ⚠️  Detector initialization: {e}", "warning")
            
            # Test preprocessor
            preprocessor_tests = {}
            try:
                preprocessor = ImagePreprocessor(target_size=(640, 640))
                preprocessor_tests = {
                    "preprocessor_created": True,
                    "has_preprocess_method": hasattr(preprocessor, 'preprocess'),
                    "has_config_info": hasattr(preprocessor, 'get_preprocessor_info')
                }
                self.log("    ✅ Image Preprocessor initialized", "debug")
            except Exception as e:
                preprocessor_tests = {"preprocessor_created": False, "error": str(e)}
                self.log(f"    ⚠️  Preprocessor initialization: {e}", "warning")
            
            # Calculate success rates
            detector_success = sum(v for v in detector_tests.values() if isinstance(v, bool)) / max(1, len([v for v in detector_tests.values() if isinstance(v, bool)]))
            preprocessor_success = sum(v for v in preprocessor_tests.values() if isinstance(v, bool)) / max(1, len([v for v in preprocessor_tests.values() if isinstance(v, bool)]))
            
            self.log(f"  CV Pipeline: Detector {detector_success:.1%}, Preprocessor {preprocessor_success:.1%}")
            
            return {
                "detector_tests": detector_tests,
                "preprocessor_tests": preprocessor_tests,
                "detector_success_rate": detector_success,
                "preprocessor_success_rate": preprocessor_success
            }
            
        except Exception as e:
            self.log(f"  ❌ CV pipeline validation failed: {e}", "error")
            return {
                "available": False,
                "error": str(e)
            }
    
    def validate_medical_ai(self) -> Dict[str, Any]:
        """Validate medical AI integration."""
        self.log("🧠 Validating medical AI integration...")
        
        try:
            from vigia_detect.ai.medgemma_client import MedGemmaClient
            
            # Test client creation
            client_tests = {
                "client_importable": True,
                "client_instantiable": False,
                "has_analyze_method": False
            }
            
            try:
                client = MedGemmaClient()
                client_tests["client_instantiable"] = True
                client_tests["has_analyze_method"] = hasattr(client, 'analyze_lpp_findings')
                self.log("    ✅ MedGemma client created", "debug")
            except Exception as e:
                self.log(f"    ⚠️  MedGemma client creation: {e}", "warning")
            
            # Check for local vs API setup
            ollama_available = self._check_ollama_availability()
            api_key_available = self._check_api_key_availability()
            
            setup_info = {
                "ollama_available": ollama_available,
                "api_key_configured": api_key_available,
                "recommended_setup": "local" if ollama_available else "api" if api_key_available else "none"
            }
            
            success_rate = sum(client_tests.values()) / len(client_tests)
            self.log(f"  Medical AI: {success_rate:.1%} validation success")
            
            return {
                "client_tests": client_tests,
                "setup_info": setup_info,
                "success_rate": success_rate
            }
            
        except Exception as e:
            self.log(f"  ❌ Medical AI validation failed: {e}", "error")
            return {
                "available": False,
                "error": str(e)
            }
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available locally."""
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_api_key_availability(self) -> bool:
        """Check if API keys are configured."""
        import os
        return bool(os.getenv('GOOGLE_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
    
    def validate_database_connection(self) -> Dict[str, Any]:
        """Validate database connectivity."""
        self.log("🗄️  Validating database connection...")
        
        try:
            import os
            from supabase import create_client
            
            # Check environment variables
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                return {
                    "credentials_available": False,
                    "message": "Supabase credentials not configured"
                }
            
            # Test connection
            try:
                supabase = create_client(supabase_url, supabase_key)
                
                # Simple query test
                response = supabase.table('patients').select('count').limit(1).execute()
                
                return {
                    "credentials_available": True,
                    "connection_successful": True,
                    "database_accessible": True
                }
                
            except Exception as e:
                return {
                    "credentials_available": True,
                    "connection_successful": False,
                    "error": str(e)
                }
                
        except Exception as e:
            self.log(f"  ❌ Database validation failed: {e}", "error")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete system validation."""
        self.log("🚀 Starting Vigia system validation...")
        
        validation_results = {}
        
        # Core validations
        validation_results['imports'] = self.validate_imports()
        validation_results['medical_decision_engine'] = self.validate_medical_decision_engine()
        validation_results['adk_agents'] = self.validate_adk_agents()
        validation_results['cv_pipeline'] = self.validate_cv_pipeline()
        validation_results['medical_ai'] = self.validate_medical_ai()
        
        if not self.quick:
            # Extended validations
            validation_results['async_pipeline'] = self.validate_async_pipeline()
            validation_results['database'] = self.validate_database_connection()
        
        # Calculate overall health
        overall_health = self._calculate_overall_health(validation_results)
        
        elapsed_time = time.time() - self.start_time
        
        self.log(f"✅ Validation completed in {elapsed_time:.1f}s")
        self.log(f"📊 Overall system health: {overall_health:.1%}")
        
        return {
            "validation_results": validation_results,
            "overall_health": overall_health,
            "elapsed_time": elapsed_time,
            "timestamp": time.time()
        }
    
    def _calculate_overall_health(self, results: Dict[str, Any]) -> float:
        """Calculate overall system health score."""
        scores = []
        
        # Import success rate
        if 'imports' in results:
            import_scores = []
            for category, modules in results['imports'].items():
                category_score = sum(modules.values()) / len(modules) if modules else 0
                import_scores.append(category_score)
            scores.append(sum(import_scores) / len(import_scores) if import_scores else 0)
        
        # Individual component scores
        for component in ['medical_decision_engine', 'adk_agents', 'cv_pipeline', 'medical_ai']:
            if component in results and 'success_rate' in results[component]:
                scores.append(results[component]['success_rate'])
        
        return sum(scores) / len(scores) if scores else 0
    
    def print_summary(self, results: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "="*60)
        print("🏥 VIGIA SYSTEM VALIDATION SUMMARY")
        print("="*60)
        
        overall_health = results.get('overall_health', 0)
        elapsed_time = results.get('elapsed_time', 0)
        
        print(f"⏱️  Validation Time: {elapsed_time:.1f}s")
        print(f"📊 Overall Health: {overall_health:.1%}")
        
        # Health status
        if overall_health >= 0.9:
            print("✅ System Status: EXCELLENT - Ready for production")
        elif overall_health >= 0.7:
            print("✅ System Status: GOOD - Ready for development")
        elif overall_health >= 0.5:
            print("⚠️  System Status: FAIR - Some components need attention")
        else:
            print("❌ System Status: POOR - Significant issues detected")
        
        print("\n📋 Component Status:")
        validation_results = results.get('validation_results', {})
        
        for component, result in validation_results.items():
            if isinstance(result, dict):
                if 'success_rate' in result:
                    rate = result['success_rate']
                    status = "✅" if rate >= 0.8 else "⚠️ " if rate >= 0.5 else "❌"
                    print(f"  {status} {component.title().replace('_', ' ')}: {rate:.1%}")
                elif result.get('available', True):
                    print(f"  ✅ {component.title().replace('_', ' ')}: Available")
                else:
                    print(f"  ❌ {component.title().replace('_', ' ')}: Not Available")
        
        print("\n💡 Recommendations:")
        
        # Specific recommendations based on results
        medical_ai = validation_results.get('medical_ai', {})
        if medical_ai.get('setup_info', {}).get('recommended_setup') == 'none':
            print("  • Configure MedGemma (local) or API keys for medical AI")
        
        cv_pipeline = validation_results.get('cv_pipeline', {})
        if cv_pipeline.get('detector_success_rate', 1) < 0.8:
            print("  • Check YOLOv5 model installation for CV pipeline")
        
        database = validation_results.get('database', {})
        if not database.get('credentials_available', True):
            print("  • Configure Supabase credentials for database access")
        
        print(f"\n📚 For setup help: docs/SETUP_GUIDE.md")
        print("🔧 For development: docs/DEVELOPER_GUIDE.md")


async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Vigia System Validator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick validation (skip extended tests)")
    
    args = parser.parse_args()
    
    try:
        validator = SystemValidator(verbose=args.verbose, quick=args.quick)
        results = await validator.run_validation()
        validator.print_summary(results)
        
        # Exit with appropriate code
        overall_health = results.get('overall_health', 0)
        exit_code = 0 if overall_health >= 0.7 else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n👋 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        logger.exception("Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())