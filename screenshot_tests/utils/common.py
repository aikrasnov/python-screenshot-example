import pytest
import os
from conftest import Config
from typing import Type


class TestCase:
    """Base class for all tests."""

    @pytest.fixture(autouse=True)
    def set_driver(self, driver):
        self.driver = driver

    @pytest.fixture(autouse=True)
    def configure(self, request):
        self.base_url = request.config.getoption(Config.BASE_URL)
        self.staging = request.config.getoption(Config.STAGING)
