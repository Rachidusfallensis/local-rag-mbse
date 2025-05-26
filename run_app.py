#!/usr/bin/env python3
"""
MBSE Local RAG Assistant Runner
Enhanced version with Arcadia methodology support and context-aware AI responses.
"""

import subprocess
import sys
import os

def main():
    print("🏗️ Starting MBSE Local RAG Assistant...")
    print("Enhanced with Arcadia methodology support!")
    print("-" * 60)
    
    # Make sure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if virtual environment exists
    venv_path = os.path.join(script_dir, "venv")
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found!")
        print("Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        sys.exit(1)
    
    # Run streamlit with the enhanced app
    try:
        # Activate venv and run streamlit
        activate_script = os.path.join(venv_path, "bin", "activate")
        cmd = f"source {activate_script} && streamlit run app.py --server.headless false --server.port 8501"
        
        print("🚀 Launching enhanced MBSE RAG Assistant on http://localhost:8501")
        print("\nFeatures included:")
        print("• 📚 Arcadia methodology references")
        print("• 🎯 MBSE context-aware analysis")
        print("• 🔍 Phase-organized sample queries")
        print("• 📄 Enhanced file processing (.capella support)")
        print("• 💬 Improved AI responses with context")
        print("-" * 60)
        
        # Run the command
        subprocess.run(cmd, shell=True, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down MBSE RAG Assistant...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 