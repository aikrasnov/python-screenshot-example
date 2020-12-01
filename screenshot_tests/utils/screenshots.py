"""Screenshot TestCase."""

import logging
import allure
import pytest
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse
from screenshot_tests.utils import common
from screenshot_tests.image_proccessing.image_processor import ImageProcessor
from typing import Tuple
from PIL import Image

# noinspection PyAttributeOutsideInit
# аннотируем все классы всех скриншот тестов для работы плагина
# https://github.com/allure-framework/allure2/tree/master/plugins/screen-diff-plugin
@allure.label('testType', 'screenshotDiff')
class TestCase(common.TestCase):
    """Screenshot TestCase."""

    # Для мобильных устройств и хрома в режиме эмуляции плотность пикселей будет отличаться.
    pixel_ratio = 1

    @pytest.fixture(autouse=True)
    def screenshot_prepare(self):
        self.image_processor = ImageProcessor()

    def _scroll(self, x: int, y: int):
        scroll_string = f"window.scrollTo({x}, {y})"
        self.driver.execute_script(scroll_string)
        time.sleep(0.2)
        logging.info(f"Scroll to «{scroll_string}»")

    def _make_screenshot_whole_page(self, locator_type, query_string):
        scroll_time = 0.2

        # Нужно заставить отработать все что есть с автоподгрузкой, чтобы получить настоящую длину страницы
        x, y, width, height = self._get_raw_coords_by_locator(locator_type, query_string)
        total_height = self.driver.execute_script("return document.body.parentNode.scrollHeight")
        logging.info(f"total height: {total_height}")

        while True:
            old_total_height = total_height
            self._scroll(0, total_height + 9999)
            time.sleep(scroll_time)
            total_height = self.driver.execute_script("return document.body.parentNode.scrollHeight")
            logging.info(f"new total height: {total_height}")
            logging.info(f"y: {y}")
            # Если высота перестала изменяться, или элемент уже попал на скриншот.
            # Второе условие позволяет не скролить до конца на стрницах с "бесконечной" длинной (выдача видео, картинок)
            if (old_total_height == total_height) or (total_height > y):
                break

        total_width = self.driver.execute_script("return document.body.offsetWidth")
        viewport_width = self.driver.execute_script("return document.body.clientWidth")
        viewport_height = self.driver.execute_script("return window.innerHeight")
        screenshots = []
        offset = 0
        assert viewport_width == total_width, "Ширина вьюпорта, и ширина экрана должны совпадать"

        self._scroll(0, 0)
        while offset <= total_height or offset <= y:
            logging.info(f"offset: {offset}, total height: {total_height}")
            screenshots.append(self.driver.get_screenshot_as_png())
            offset += viewport_height
            self._scroll(0, offset)

        # эта часть последнего скриншота, которая дублирует предпоследний скриншот
        # так просходит потому что не всегда страница делится на целое количество вьюпортов
        over_height = offset - total_height
        logging.info(f"offset: {offset}, total height: {total_height}, over height: {over_height}, pixel density: {self.pixel_ratio}")
        return self.image_processor.paste(screenshots, over_height * self.pixel_ratio)

    def _use_full_screen(self):
        # хак чтобы снять целиком элемент который не помещается на страницу
        # https://stackoverflow.com/questions/44085722/how-to-get-screenshot-of-full-webpage-using-selenium-and-java
        # https://gist.github.com/elcamino/5f562564ecd2fb86f559
        self.driver.set_window_size(1425, 2900)

    def _get_raw_coords_by_locator(self, locator_type, query_string):
        """Без учета плотности пикселей."""
        wait = WebDriverWait(self.driver, timeout=10, ignored_exceptions=Exception)
        wait.until(lambda _: self.driver.find_element(locator_type, query_string).is_displayed(),
                        message="Невозможно получить размеры элемента, элемент не отображается")
        # После того, как дождались видимости элемента, ждем еще 2 секунды, чтобы точно завершились разные анимации
        time.sleep(2)
        el = self.driver.find_element(locator_type, query_string)
        location = el.location
        size = el.size
        x = location["x"]
        y = location["y"]
        width = location["x"] + size['width']
        height = location["y"] + size['height']
        # (312, 691, 1112, 691)
        return x, y, width, height

    def _get_coords_by_locator(self, locator_type, query_string) -> Tuple[int, int, int, int]:
        x, y, width, height = self._get_raw_coords_by_locator(locator_type, query_string)
        return x * self.pixel_ratio, y * self.pixel_ratio, width * self.pixel_ratio, height * self.pixel_ratio

    def _get_element_screenshot(self,
                                locator_type,
                                query_string,
                                action,
                                finalize,
                                scroll_and_screen) \
     -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        """Сделать скриншот страницы и кропнуть до скриншота элемента.

        Не получится использовать метод session/{sessionId}/element/{elementId}/screenshot
        Потому что он имплементирован только в эдж.
        https://stackoverflow.com/questions/36084257/im-trying-to-take-a-screenshot-of-an-element-with-selenium-webdriver-but-unsup
        """
        if not scroll_and_screen:
            # Иногда страница по дефолту открыта посередине, чтобы не ползли координаты
            # элемента с scroll_and_screen=False, скролим до начала. Это нужно делать до вызова action, на случай если
            # в action страницу нужно проскролить до определенной точки.
            self._scroll(0, 0)

        # Тут готовим страницу к снятию скриншота
        if callable(action):
            action()

        if scroll_and_screen:
            screen = self._make_screenshot_whole_page(locator_type, query_string)
        else:
            screen = self.image_processor.load_image_from_bytes(self.driver.get_screenshot_as_png())

        coordinates = self._get_coords_by_locator(locator_type, query_string)
        logging.info(f"element: {query_string}, coordinates: {coordinates}")

        # Тут можно выполнить дополнительные проверки после снятия скрина
        if callable(finalize):
            finalize()

        return screen.crop(coordinates), coordinates

    def _get_diff(self, element, action=None, full_screen=True, full_page=False, finalize=None, scroll_and_screen=True):
        """Получит скриншоты с текущей страницы, и с эталонной.

        Поблочно сравнит их, и вернет количество отличающихся блоков.
        :param element: тюпл с типом локатора и локатором
        :param action: функция которая подготовит страницу к снятию скриншота
        :param full_screen: ресайзить ли браузер до максимума
        :param full_page: скринить всю страницу, а не только переданный элемент
        :param finalize: финализация после сравнения скриншотов
        :param scroll_and_screen: скролить страницу (сверху к низу) и склеивать участки в один скриншот
        """
        if full_screen:
            self._use_full_screen()

        if full_page:
            locator_type, query_string = (By.XPATH, "//body")
            scroll_and_screen = False
        else:
            locator_type, query_string = element[0], element[1]

        saved_url = urlparse(self.driver.current_url)
        # noinspection PyProtectedMember
        prod_url = saved_url._replace(netloc=self.staging)

        # На текущей странице делаем первый скриншот
        first_image, coords_test = self._get_element_screenshot(locator_type, query_string, action, finalize,
                                                                scroll_and_screen)
        logging.info('Done screen on test stand')
        # Теперь делаем скриншот в проде
        self.driver.get(prod_url.geturl())
        second_image, coords_prod = self._get_element_screenshot(locator_type, query_string, action, finalize,
                                                                 scroll_and_screen)
        logging.info('Done screen on stage stand')

        # Возращаемся на тестовый стенд. Всегда нужно возвращаться на тестовый стенд. На это завязаны тесты и отчеты
        self.driver.get(saved_url.geturl())

        # Для добавления в отчет (https://github.com/allure-framework/allure2/tree/master/plugins/screen-diff-plugin)
        # noinspection PyUnboundLocalVariable
        allure.attach(self.image_processor.image_to_bytes(first_image), 'actual', allure.attachment_type.PNG)
        # noinspection PyUnboundLocalVariable
        allure.attach(self.image_processor.image_to_bytes(second_image), 'expected', allure.attachment_type.PNG)

        # noinspection PyUnboundLocalVariable
        diff, result = self.image_processor.get_images_diff(first_image, second_image)
        allure.attach(result, 'diff', allure.attachment_type.PNG)

        return diff, saved_url, prod_url

    def get_diff(self, *args, **kwargs):
        diff, _, _ = self._get_diff(*args, **kwargs)
        return diff

    def check_by_screenshot(self, element, *args, **kwargs):
        diff, saved_url, prod_url = self._get_diff(element, *args, **kwargs)
        assert diff == 0, f"Элемент отличается на страницах:\n{saved_url.geturl()}\nи\n{prod_url.geturl()}"
