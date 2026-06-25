import os
import sys

def check_dependencies():
    try:
        import PySide6
    except ImportError:
        print("Fehler: PySide6 wurde nicht gefunden.")
        print("Bitte starte die Anwendung mit 'uv run':")
        print("\n    uv run python main.py\n")
        sys.exit(1)

# Add src directory to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    check_dependencies()
    from silkroad_companion.main import main
    main()
