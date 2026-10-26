# Dental3D Studio

A desktop concept demo for exploring a dental CAD workflow. The app includes a built-in procedural upper and lower arch, interactive 3D controls, illustrative analysis panels, and optional STL import.

## Setup

Python 3.10 or newer is recommended. From this folder, create an environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Launch

```powershell
python app.py
```

### Run from VS Code

Open this project folder in VS Code and press **Run Python File** while `app.py` is active. The workspace is configured to use `.venv\\Scripts\\python.exe`; that environment can see the Python packages already installed for this PC. If VS Code already has a different interpreter selected for this workspace, choose `.venv` once from **Python: Select Interpreter**.

On a different computer, create a fresh environment and install `requirements.txt` using the setup steps above.

Use the mouse in the viewport to rotate, zoom, and pan. “Open Scan” accepts STL files. All analysis values and treatment/contact/comparison overlays are illustrative simulated examples, and this prototype is not clinically validated.
