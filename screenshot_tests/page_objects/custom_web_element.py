import allure
from selenium.webdriver.remote.webelement import WebElement


class CustomWebElement:
    """Custom web element with allure logging."""

    def __init__(self, by: str, locator: str, element: WebElement, description: str = None):
        self.by = by
        self.locator = locator
        self.element = element
        self.description = f"«{description}»" if description else "element"

    def _execute_action(self, action, step):
        """Execute action with allure logging.

        :param action: Function to execute. Click, send_keys, etc
        :param step: Step description.
        """
        @allure.step(step)
        def execute_action(locator_type=self.by, locator=self.locator):
            """All arguments will be available in report."""
            return action()

        return execute_action()

    def click(self):
        self._execute_action(self.element.click,
                             f"Click at {self.description}")

    def send_keys(self, *value):
        self._execute_action(lambda: self.element.send_keys(*value),
                             f"Send text {[v for v in value]} to {self.description}")

    def __eq__(self, element):
        return self.element.__eq__(element)

    def __ne__(self, element):
        return self.element.__ne__(element)

    def __hash__(self):
        return self.element.__hash__()

    def __getattr__(self, item):
        """Missing methods will be executed from WebElement."""
        return getattr(self.element, item)
