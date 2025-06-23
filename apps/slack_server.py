"""
Refactored Slack server using the new centralized architecture.
This replaces apps/slack_server.py with proper configuration management.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vigia_detect.interfaces import SlackInterface


def main():
    """Run the Slack interface server"""
    try:
        # Initialize Slack interface
        slack_interface = SlackInterface()
        
        # Run server
        slack_interface.run_server(
            host="0.0.0.0",
            port=3000,
            debug=False
        )
        
    except Exception as e:
        print(f"Failed to start Slack server: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())