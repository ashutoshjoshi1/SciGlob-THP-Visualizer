# THP Visualizer

## Building the Executable

### Prerequisites
- Python 3.6 or higher
- PyInstaller (`pip install pyinstaller`)
- All dependencies listed in requirements.txt

### Steps to Build

1. Install PyInstaller if you haven't already:
   ```
   pip install pyinstaller
   ```

2. Install all required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the build script:
   ```
   build_exe.bat
   ```

4. The executable will be created in the `dist\THP_Visualizer` folder.

### Running the Application

Simply double-click on `THP_Visualizer.exe` in the `dist\THP_Visualizer` folder.

## Troubleshooting

If you encounter any issues:

1. Make sure all dependencies are installed
2. Check that you have the correct version of Python (3.6+)
3. Try running the application from the command line to see any error messages:
   ```
   dist\THP_Visualizer\THP_Visualizer.exe
   ```

## Notes

- The executable includes all necessary dependencies
- No installation is required - it's a portable application
- The logs folder will be created in the same directory as the executable
- This application uses run_app.py as the entry point, which then launches main_gui.py