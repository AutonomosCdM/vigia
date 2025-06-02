#!/usr/bin/env python3
"""
Interactive Redis setup with step-by-step CLI commands.
Shows the exact commands to run for manual setup.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / "vigia_detect" / ".env")


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    """Interactive Redis setup guide."""
    print("🚀 Redis CLI Setup Guide for Vigia")
    print("This guide will show you the exact Redis CLI commands to run")
    
    # Get connection info
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    password = os.getenv("REDIS_PASSWORD", "")
    use_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
    
    print_section("1. Connect to Redis")
    
    if host == "your-redis-host.redislabs.com":
        print("⚠️  You're using example configuration!")
        print("Update vigia_detect/.env with your real Redis credentials\n")
        
    # Build connection command
    connect_cmd = "redis-cli"
    if host != "localhost":
        connect_cmd += f" -h {host}"
    if port != "6379":
        connect_cmd += f" -p {port}"
    if password:
        connect_cmd += f" -a {password}"
    if use_ssl:
        connect_cmd += " --tls"
        
    print("Run this command to connect:")
    print(f"\n  {connect_cmd}\n")
    
    print("Or set an alias for easier access:")
    print(f"\n  alias vigia-redis='{connect_cmd}'\n")
    
    input("Press Enter when connected to Redis...")
    
    print_section("2. Test Connection")
    
    print("Test your connection with:")
    print("\n  PING\n")
    print("Expected response: PONG")
    
    input("Press Enter after testing connection...")
    
    print_section("3. Check RediSearch Module")
    
    print("Check if RediSearch is installed:")
    print("\n  MODULE LIST\n")
    print("Look for 'search' in the output")
    
    input("Press Enter if RediSearch is available...")
    
    print_section("4. Create Medical Cache Index")
    
    print("Copy and paste this command:")
    print("""
FT.CREATE idx:medical_cache 
  ON HASH 
  PREFIX 1 "cache:medical:" 
  SCHEMA 
    query TEXT NOSTEM 
    response TEXT 
    medical_context TEXT NOSTEM 
    timestamp NUMERIC 
    ttl NUMERIC 
    hit_count NUMERIC 
    embedding VECTOR FLAT 6 
      TYPE FLOAT32 
      DIM 384 
      DISTANCE_METRIC COSINE
""")
    
    input("Press Enter after creating cache index...")
    
    print_section("5. Create Medical Protocols Index")
    
    print("Copy and paste this command:")
    print("""
FT.CREATE idx:medical_protocols 
  ON HASH 
  PREFIX 1 "protocol:" 
  SCHEMA 
    title TEXT NOSTEM WEIGHT 2.0 
    content TEXT WEIGHT 1.0 
    source TEXT NOSTEM 
    tags TAG 
    lpp_grades TAG 
    page_number NUMERIC 
    embedding VECTOR HNSW 8 
      TYPE FLOAT32 
      DIM 384 
      DISTANCE_METRIC COSINE 
      M 16 
      EF_CONSTRUCTION 200
""")
    
    input("Press Enter after creating protocols index...")
    
    print_section("6. Load Sample Protocol")
    
    print("Load a sample prevention protocol:")
    print("""
HSET protocol:prevention_001 
  title "Protocolo de Prevención de LPP - MINSAL" 
  content "Las lesiones por presión (LPP) son áreas de daño localizado en la piel y tejidos subyacentes. La prevención incluye: 1) Cambios posturales cada 2 horas 2) Uso de superficies especiales de apoyo 3) Evaluación regular del riesgo con escala de Braden 4) Mantener la piel limpia y seca 5) Nutrición e hidratación adecuadas" 
  source "MINSAL Chile 2019" 
  tags "prevention,care,assessment" 
  lpp_grades "grade_0,grade_1" 
  page_number 15
""")
    
    input("Press Enter after loading sample protocol...")
    
    print_section("7. Test Search")
    
    print("Test searching for prevention protocols:")
    print("""
FT.SEARCH idx:medical_protocols "@tags:{prevention}" LIMIT 0 5
""")
    
    print("\nYou should see the protocol you just added!")
    
    input("Press Enter after testing search...")
    
    print_section("8. Verify Setup")
    
    print("Check index statistics:")
    print("\n  FT.INFO idx:medical_cache")
    print("  FT.INFO idx:medical_protocols\n")
    
    print("Look for 'num_docs' to see document count")
    
    print_section("✅ Setup Complete!")
    
    print("Your Redis indexes are now ready!")
    print("\nYou can now run:")
    print("  python examples/redis_phase2_demo.py")
    print("\nUseful commands:")
    print("  FT._LIST                    # List all indexes")
    print("  FT.SEARCH idx:medical_protocols *    # See all protocols")
    print("  KEYS protocol:*             # List all protocol keys")
    
    print("\n📚 Full command reference: scripts/redis_cli_commands.md")


if __name__ == "__main__":
    main()