"""CLI commands for the qubo API server."""
import click
from .api import run_api_server

@click.group()
def api():
    """API server commands."""
    pass

@api.command()
@click.option('--host', default='localhost', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug/--no-debug', default=True, help='Enable debug mode')
def serve(host, port, debug):
    """Start the API server."""
    run_api_server(host=host, port=port, debug=debug)

if __name__ == '__main__':
    api()
