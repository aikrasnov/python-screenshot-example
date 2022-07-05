import pytest

from conftest import Config


# noinspection PyAttributeOutsideInit
class TestCase:
    """Base class for all tests."""

    @pytest.fixture(autouse=True)
    def set_driver(self, driver):
        self.driver = driver

    @pytest.fixture(autouse=True)
    def configure(self, request):
        self.base_url = request.config.getoption(Config.BASE_URL)
        self.staging = request.config.getoption(Config.STAGING)
