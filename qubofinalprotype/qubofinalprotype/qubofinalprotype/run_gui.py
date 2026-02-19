#!/usr/bin/env python3
"""Simple launcher for the qubo GUI (restored).
Starts the Quantum IDE (includes API Hub features inside gui.py).
Optional flags:
  --no-api-dock   Skip AI/API docks
"""
import sys, os, argparse

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--no-api-dock', action='store_true', help='Skip AI/API docks (sets QUBO_SKIP_AI_DOCK=1)')
    return p.parse_args()


def main():
    args = parse_args()
    if args.no_api_dock:
        os.environ['QUBO_SKIP_AI_DOCK'] = '1'
    print('Starting Quantum IDE...')
    print('Loading quantum computing framework (GUI + API Hub + Visual Designer)...')
    from qubo.gui import main as gui_main
    print('Framework loaded.')
    gui_main()


if __name__ == '__main__':  # pragma: no cover
    try:
        main()
    except ImportError as e:
        print(f'Import Error: {e}')
        print('Run: pip install -r requirements.txt')
        raise
    except Exception as e:
        print(f'Error launching GUI: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)
