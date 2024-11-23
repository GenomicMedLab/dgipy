import pytest

from dgipy.graph_app import generate_app


def test_generate_app():
    app = generate_app()
    if __name__ == "__main__":
        app.run_server()
