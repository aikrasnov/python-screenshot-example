import pytest
import os
from screenshot_tests.page_objects.elements import PageBoundGeneric
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

    def get_page(self, page_class: Type[PageBoundGeneric]) -> PageBoundGeneric:
        """Create instance of web page and return it."""
        path = page_class.path

        if path is None:
            raise TypeError(f"Path in {page_class} is None!")

        page = page_class(self.driver)
        self.driver.get(os.path.join(self.base_url, path))
        return page
