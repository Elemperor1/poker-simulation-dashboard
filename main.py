import streamlit as st
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.app import PokerApp

def main():
    app = PokerApp()
    app.render()

if __name__ == "__main__":
    main()