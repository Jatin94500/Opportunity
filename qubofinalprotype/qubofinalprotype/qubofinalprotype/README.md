# Qubo — Minimal Quantum Simulator (MVP)

Quickstart
----------
Requirements:
- Python 3.8+ (virtualenv recommended)

1) Create and activate a virtualenv (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install required packages:

```powershell
pip install -r requirements.txt
```

3) Run the GUI (PyQt5):

```powershell
python -m qubo.gui
```

4) Run example or CLI:

```powershell
# Run example via CLI (prints counts or probabilities)
python -m qubo.cli examples/hello_world.ipynb --shots 1024 --json

# Or run tests
python -m pytest -q
```

Modules and features
- `qubo.circuit` — Python-first circuit API (QuantumCircuit, Gate)
- `qubo.gates` — convenience gate factories (H, X, CNOT, RZ, RX, RY, SWAP, Measure)
- `qubo.simulator` — statevector simulator (H, X, RX, RY, RZ, CNOT, SWAP, measurement sampling) with noise hook
- `qubo.noise` — simple noise channels and a noise_hook adapter
- `qubo.visualizer` — matplotlib-based plotting helper
- `qubo.gui` — minimal VS Code-like UI (dark purple theme) with editor, simulator, visualizer
- `qubo.ai` — optional AI code review / correction suggestions (Gemini or static fallback)
- `qubo.builder` — drag-and-drop circuit builder (GUI tab) that exports code

Notes
- Noise channels in `qubo/noise.py` are statevector approximations; full density-matrix/Kraus channels are planned for phase 2.
- Simulator is acceptable for small circuits and demonstration; further optimizations are planned for >12 qubits.

Contributing
- Tests live in `/tests` and CI runs via GitHub Actions on push/PR.
- Add examples to `/examples` and keep notebooks runnable.

License
- MIT

AI Code Suggestions (Optional)
------------------------------
You can get AI code review / correction suggestions inside the GUI:

1. Install optional dependency (if you want Gemini):
	```powershell
	pip install google-generativeai
	```
2. Set your API key (PowerShell):
	```powershell
	$Env:GEMINI_API_KEY = "your_key_here"
	```
3. (Optional) Pick a different model:
	```powershell
	$Env:QUBO_GEMINI_MODEL = "gemini-1.5-pro"
	```
4. Launch the GUI and click `AI Suggest` to see bullet-point suggestions.

If the key or library is missing, a lightweight static analyzer provides basic hints (unused imports, missing measurement, etc.).

Drag-and-Drop Circuit Builder
-----------------------------
Open the GUI (`python -m qubo.gui`) and switch to the `Builder` tab:

1. Adjust qubit count.
2. Drag a gate from the palette onto the wire (drop over a qubit lane).
3. For two-qubit gates (CNOT, SWAP) you'll be prompted for the second qubit.
4. Click `Simulate` for an immediate statevector / distribution summary.
5. Click `Export to Editor` to push generated code back into the main editor tab.

The generated code can then be further edited or run with noise / shots controls.
