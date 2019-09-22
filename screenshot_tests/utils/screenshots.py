import pytest
import time
import logging
import allure

from screenshot_tests.page_objects.custom_web_element import CustomWebElement
from urllib.parse import urlparse
from screenshot_tests.page_objects.elements import Locators
from screenshot_tests.utils import common
from screenshot_tests.image_proccessing.image_processor import ImageProcessor
from typing import Tuple
from PIL import Image


# https://github.com/allure-framework/allure2/tree/master/plugins/screen-diff-plugin
@allure.label('testType', 'screenshotDiff')
class TestCase(common.TestCase):
    """Base class for all screenshot tests."""

    BODY_LOCATOR = (Locators.CSS_SELECTOR, "body")

    @pytest.fixture(autouse=True)
    def screenshot_prepare(self):
        self.image_processor = ImageProcessor()
        # количество попыток для снятия скриншота
        self.attempts = 5

    def _scroll(self, x: int, y: int):
        scroll_string = f"window.scrollTo({x}, {y})"
        self.driver.execute_script(scroll_string)
        time.sleep(0.2)
        logging.info(f"Scroll to «{scroll_string}»")

    def _make_screenshot_whole_page(self):
        total_width = self.driver.execute_script("return document.body.offsetWidth")
        total_height = self.driver.execute_script("return document.body.parentNode.scrollHeight")
        viewport_width = self.driver.execute_script("return document.body.clientWidth")
        viewport_height = self.driver.execute_script("return window.innerHeight")
        screenshots = []
        offset = 0
        assert viewport_width == total_width, "Ширина вьюпорта, и ширина экрана должны совпадать"

        self._scroll(0, 0)
        while offset <= total_height:
            screenshots.append(self.driver.get_screenshot_as_png())
            offset += viewport_height
            self._scroll(0, offset)

        return self.image_processor.paste(screenshots)

    def _get_coords_by_locator(self, by, locator) -> Tuple[int, int, int, int]:
        # После того, как дождались видимости элемента, ждем еще 2 секунды, чтобы точно завершились разные анимации
        time.sleep(2)
        el = self.driver.find_element(by, locator)
        location = el.location
        size = el.size
        x = location["x"]
        y = location["y"]
        width = location["x"] + size['width']
        height = location["y"] + size['height']
        return x, y, width, height

    def _get_element_screenshot(self, by, locator, action, finalize) \
            -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        """Get screenshot of element.

        Can't use session/{sessionId}/element/{elementId}/screenshot because it's available only in Edge
        https://stackoverflow.com/questions/36084257/im-trying-to-take-a-screenshot-of-an-element-with-selenium-webdriver-but-unsup
        """
        if callable(action):
            action()

        coordinates = self._get_coords_by_locator(by, locator)
        screen = self._make_screenshot_whole_page()
        logging.info(f"element: {locator}, coordinates: {coordinates}")

        if callable(finalize):
            finalize()

        return screen.crop(coordinates), coordinates

    def _get_diff(self, element: CustomWebElement, action=None, full_page=False, finalize=None):
        """Get screenshot from test environment and compare with production.

        :param element: element for check (instance of CustomWebElement)
        :param action: callback executed before making screenshot. Use it when need prepare page for screenshot.
        :param full_page: ignore element, and compare whole page.
        :param finalize: callback executed after screenshot.
        """
        if full_page:
            by, locator = self.BODY_LOCATOR
        else:
            by, locator = element.by, element.locator

        saved_url = urlparse(self.driver.current_url)
        # noinspection PyProtectedMember
        prod_url = saved_url._replace(netloc=urlparse(self.staging).netloc)

        # Открываем странички пока размеры элементов на них не совпадут
        coords_equal = False
        attempts = 0
        while not coords_equal and attempts < self.attempts:
            logging.info(f'Try make screenshots. Attempts: {attempts}')

            # На текущей странице делаем первый скриншот
            first_image, coords_test = self._get_element_screenshot(by, locator, action, finalize)

            # Теперь делаем скриншот в проде
            self.driver.get(prod_url.geturl())
            second_image, coords_prod = self._get_element_screenshot(by, locator, action, finalize)

            # Возращаемся на тестовый стенд. Всегда нужно возвращаться на тестовый стенд. На это завязаны тесты и отчеты
            self.driver.get(saved_url.geturl())

            # Если размеры элементов на странице не совпали, и выбраны не все попытки, пробуем снова
            attempts += 1
            # По размеру блока, оставим на случай, если по координатам способ будет не работать не очень
            x1, y1, x2, y2 = coords_test
            x_1, y_1, x_2, y_2 = coords_prod
            size_test = round(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
            size_prod = round(((x_2 - x_1) ** 2 + (y_2 - y_1) ** 2) ** 0.5)
            logging.info(f"Coords test: {coords_test}, coords prod: {coords_prod}")
            logging.info(f"Size test: {size_test}, size prod: {size_prod}")
            coords_equal = size_prod == size_test

        # noinspection PyUnboundLocalVariable
        diff, result, first, second = self.image_processor.get_images_diff(first_image, second_image)

        # Для добавления в отчет (https://github.com/allure-framework/allure2/tree/master/plugins/screen-diff-plugin)
        allure.attach(result, "diff", allure.attachment_type.PNG)
        allure.attach(first, "actual", allure.attachment_type.PNG)
        allure.attach(second, "expected", allure.attachment_type.PNG)

        return diff, saved_url, prod_url

    def get_diff(self, *args, **kwargs):
        diff, _, _ = self._get_diff(*args, **kwargs)
        return diff

    def check_by_screenshot(self, element: CustomWebElement, *args, **kwargs):
        diff, saved_url, prod_url = self._get_diff(element, *args, **kwargs)
        info = element.description
        assert diff == 0, f"{info} отличается на страницах:\n{saved_url.geturl()}\nи\n{prod_url.geturl()}"
