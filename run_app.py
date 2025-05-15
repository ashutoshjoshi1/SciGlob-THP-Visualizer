import sys
import os
import importlib.util
import traceback

def main():
    try:
        print("Running THP Visualizer...")
        
        # Get the directory where the executable is located
        if getattr(sys, 'frozen', False):
            # We're running in a bundle
            bundle_dir = sys._MEIPASS
            # Make sure the current working directory is set correctly
            os.chdir(os.path.dirname(sys.executable))
        else:
            # We're running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else bundle_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        print(f"Looking for main_gui.py in {bundle_dir}...")
        main_gui_path = os.path.join(bundle_dir, "main_gui.py")
        
        if os.path.exists(main_gui_path):
            print(f"Found main_gui.py at {main_gui_path}")
            
            # Instead of running as a subprocess, import and run directly
            spec = importlib.util.spec_from_file_location("main_gui", main_gui_path)
            main_gui = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_gui)
            
            # If main_gui has a main function, call it
            if hasattr(main_gui, "main"):
                print("Calling main_gui.main()")
                main_gui.main()
            else:
                # Check if it has a MainWindow class
                if hasattr(main_gui, "MainWindow"):
                    print("Creating MainWindow instance")
                    from PyQt5.QtWidgets import QApplication
                    app = QApplication(sys.argv)
                    window = main_gui.MainWindow()
                    window.show()
                    sys.exit(app.exec_())
                else:
                    print("No main() function or MainWindow class found in main_gui.py")
                    print("Available attributes in main_gui:")
                    for attr in dir(main_gui):
                        if not attr.startswith("__"):
                            print(f"  - {attr}")
                    input("Press Enter to exit...")
        else:
            print(f"Error: Could not find main_gui.py at {main_gui_path}")
            print("Current directory contents:")
            for item in os.listdir(bundle_dir):
                print(f"  - {item}")
            input("Press Enter to exit...")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Detailed traceback:")
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
