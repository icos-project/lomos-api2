import pytest
from lomos_api2.lomos_api2 import app

@pytest.fixture
def app():
    # app = create_app()
    return app
