#!/usr/bin/env python3
"""
Redis setup using redis-cli commands through Python.
This approach uses raw Redis commands for better control.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv(project_root / "vigia_detect" / ".env")


class RedisCliSetup:
    """Setup Redis indexes using CLI commands."""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = os.getenv("REDIS_PORT", "6379")
        self.password = os.getenv("REDIS_PASSWORD", "")
        self.use_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
        
    def _build_cli_args(self):
        """Build redis-cli connection arguments."""
        args = ["redis-cli"]
        
        if self.host:
            args.extend(["-h", self.host])
        if self.port:
            args.extend(["-p", str(self.port)])
        if self.password:
            args.extend(["-a", self.password])
        if self.use_ssl:
            args.append("--tls")
            
        return args
        
    def execute_command(self, *command_parts):
        """Execute a Redis command using redis-cli."""
        args = self._build_cli_args()
        args.extend(command_parts)
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command_parts)}")
            print(f"Error: {e.stderr}")
            return None
            
    def test_connection(self):
        """Test Redis connection."""
        print("Testing Redis connection...")
        result = self.execute_command("ping")
        
        if result == "PONG":
            print("✅ Redis connection successful")
            return True
        else:
            print("❌ Redis connection failed")
            return False
            
    def check_redisearch(self):
        """Check if RediSearch module is loaded."""
        print("\nChecking RediSearch module...")
        result = self.execute_command("MODULE", "LIST")
        
        if result and "search" in result.lower():
            print("✅ RediSearch module found")
            return True
        else:
            print("❌ RediSearch module not found")
            print("Please install Redis Stack or load RediSearch module")
            return False
            
    def create_medical_cache_index(self):
        """Create the medical cache index."""
        print("\nCreating medical cache index...")
        
        result = self.execute_command(
            "FT.CREATE", "idx:medical_cache",
            "ON", "HASH",
            "PREFIX", "1", "cache:medical:",
            "SCHEMA",
            "query", "TEXT", "NOSTEM",
            "response", "TEXT",
            "medical_context", "TEXT", "NOSTEM",
            "timestamp", "NUMERIC",
            "ttl", "NUMERIC",
            "hit_count", "NUMERIC",
            "embedding", "VECTOR", "FLAT", "6",
            "TYPE", "FLOAT32",
            "DIM", "384",
            "DISTANCE_METRIC", "COSINE"
        )
        
        if result == "OK":
            print("✅ Medical cache index created")
        else:
            print("⚠️  Medical cache index might already exist")
            
    def create_protocols_index(self):
        """Create the medical protocols index."""
        print("\nCreating medical protocols index...")
        
        result = self.execute_command(
            "FT.CREATE", "idx:medical_protocols",
            "ON", "HASH",
            "PREFIX", "1", "protocol:",
            "SCHEMA",
            "title", "TEXT", "NOSTEM", "WEIGHT", "2.0",
            "content", "TEXT", "WEIGHT", "1.0",
            "source", "TEXT", "NOSTEM",
            "tags", "TAG",
            "lpp_grades", "TAG",
            "page_number", "NUMERIC",
            "embedding", "VECTOR", "HNSW", "8",
            "TYPE", "FLOAT32",
            "DIM", "384",
            "DISTANCE_METRIC", "COSINE",
            "M", "16",
            "EF_CONSTRUCTION", "200"
        )
        
        if result == "OK":
            print("✅ Medical protocols index created")
        else:
            print("⚠️  Medical protocols index might already exist")
            
    def load_sample_protocols(self):
        """Load sample medical protocols."""
        print("\nLoading sample medical protocols...")
        
        protocols = [
            {
                "key": "protocol:prevention_001",
                "data": {
                    "title": "Protocolo de Prevención de LPP - MINSAL",
                    "content": "Las lesiones por presión (LPP) son áreas de daño localizado en la piel. "
                              "Prevención: 1) Cambios posturales cada 2 horas 2) Superficies especiales "
                              "3) Evaluación con escala de Braden 4) Piel limpia y seca 5) Nutrición adecuada",
                    "source": "MINSAL Chile 2019",
                    "tags": "prevention,care,assessment",
                    "lpp_grades": "grade_0,grade_1",
                    "page_number": "15"
                }
            },
            {
                "key": "protocol:treatment_grade2_001",
                "data": {
                    "title": "Tratamiento LPP Grado 2",
                    "content": "Tratamiento de LPP grado 2 (pérdida parcial del espesor): "
                              "1) Limpieza con suero fisiológico 2) Apósito hidrocoloide o espuma "
                              "3) Protección de zona 4) Cambios según fabricante "
                              "5) Monitoreo de infección 6) Medidas preventivas continuas",
                    "source": "Protocolo EPUAP/NPUAP",
                    "tags": "treatment,care",
                    "lpp_grades": "grade_2",
                    "page_number": "45"
                }
            },
            {
                "key": "protocol:treatment_grade3_001",
                "data": {
                    "title": "Tratamiento LPP Grado 3",
                    "content": "Tratamiento LPP grado 3 (pérdida total del espesor): "
                              "1) Evaluación multidisciplinaria 2) Desbridamiento si necesario "
                              "3) Control bacteriano 4) Apósitos avanzados "
                              "5) Considerar presión negativa 6) Optimización nutricional con proteínas",
                    "source": "Guía Clínica MINSAL",
                    "tags": "treatment,care",
                    "lpp_grades": "grade_3",
                    "page_number": "67"
                }
            }
        ]
        
        for protocol in protocols:
            # Build HSET command
            command = ["HSET", protocol["key"]]
            for field, value in protocol["data"].items():
                command.extend([field, value])
                
            result = self.execute_command(*command)
            if result:
                print(f"✅ Loaded: {protocol['data']['title']}")
                
    def show_index_info(self):
        """Show information about the indexes."""
        print("\n📊 Index Statistics:")
        
        # Medical cache index
        print("\nMedical Cache Index:")
        info = self.execute_command("FT.INFO", "idx:medical_cache")
        if info:
            # Parse and show relevant info
            lines = info.split('\n')
            for i, line in enumerate(lines):
                if 'num_docs' in line and i+1 < len(lines):
                    print(f"  Documents: {lines[i+1]}")
                    
        # Protocols index
        print("\nMedical Protocols Index:")
        info = self.execute_command("FT.INFO", "idx:medical_protocols")
        if info:
            lines = info.split('\n')
            for i, line in enumerate(lines):
                if 'num_docs' in line and i+1 < len(lines):
                    print(f"  Documents: {lines[i+1]}")
                    
    def search_protocols(self, query):
        """Example search query."""
        print(f"\n🔍 Searching for: {query}")
        
        result = self.execute_command(
            "FT.SEARCH", "idx:medical_protocols",
            query,
            "LIMIT", "0", "3",
            "RETURN", "2", "title", "tags"
        )
        
        if result:
            lines = result.split('\n')
            if lines and lines[0].isdigit():
                count = int(lines[0])
                print(f"Found {count} results")
                
                # Parse results (simplified)
                i = 1
                while i < len(lines):
                    if lines[i].startswith("protocol:"):
                        print(f"\n  Key: {lines[i]}")
                        i += 1
                        # Skip to field values
                        while i < len(lines) and not lines[i].startswith("protocol:"):
                            if i+1 < len(lines):
                                print(f"    {lines[i]}: {lines[i+1]}")
                                i += 2
                            else:
                                i += 1
                                
    def run_full_setup(self):
        """Run the complete setup process."""
        print("🚀 Redis Setup for Vigia Medical System")
        print("======================================")
        
        # Test connection
        if not self.test_connection():
            return False
            
        # Check RediSearch
        if not self.check_redisearch():
            return False
            
        # Create indexes
        self.create_medical_cache_index()
        self.create_protocols_index()
        
        # Load sample data
        self.load_sample_protocols()
        
        # Show stats
        self.show_index_info()
        
        # Example search
        self.search_protocols("@tags:{prevention}")
        
        print("\n✨ Redis setup completed successfully!")
        print("You can now run: python examples/redis_phase2_demo.py")
        
        return True


def main():
    """Main setup function."""
    setup = RedisCliSetup()
    
    # Check if we're using default (non-configured) values
    if setup.host == "your-redis-host.redislabs.com":
        print("⚠️  Warning: Using example Redis configuration")
        print("Please update vigia_detect/.env with your Redis credentials")
        print("\nRunning in mock mode is recommended for development:")
        print("  python examples/redis_phase2_demo.py")
        return
        
    success = setup.run_full_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()