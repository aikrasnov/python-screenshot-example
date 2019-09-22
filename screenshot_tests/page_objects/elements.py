from selenium.webdriver import Remote
from selenium.webdriver.common import by as selenium_by
from screenshot_tests.page_objects.custom_web_element import CustomWebElement
from typing import Union, TypeVar, Type

Locators = selenium_by.By


class Page:
    """Base page for all pages in PO."""

    path = None

    def __init__(self, driver: Remote):
        self.driver = driver


PageBoundGeneric = TypeVar("PageBoundGeneric", bound=Page)


class Element:
    """Element descriptor for WebElement lazy init."""

    def __init__(self, by: str, locator: str, description: str):
        self.by = by
        self.locator = locator
        self.description = description

    def __get__(self,
                instance: PageBoundGeneric,
                owner: Type[PageBoundGeneric]) -> Union[CustomWebElement, 'Element']:
        """
        https://docs.python.org/3/howto/descriptor.html
        :param instance: instance of owner
        :param owner: type of owner
        :return: self or WebElement instance
        """
        if isinstance(instance, Element):
            return self

        return CustomWebElement(self.by, self.locator, instance.driver.find_element(self.by, self.locator),
                                self.description)
