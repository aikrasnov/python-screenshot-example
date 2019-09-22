from screenshot_tests.utils.screenshots import TestCase
from screenshot_tests.page_objects.pages.yandex_main_page import YandexMainPage
import random


class TestYandexMainPage(TestCase):
    """Tests for https://yandex.ru"""

    def test_news_widget(self):
        """Test for news widget."""
        page = self.get_page(YandexMainPage)
        self.check_by_screenshot(page.news_header)

    def test_search_field(self):
        words = ["foo", "bar", "lol", "kek", "cheburek", "otus", "yandex", "google"]
        page = self.get_page(YandexMainPage)

        def action():
            page.search_input.send_keys(random.choice(words))

        self.check_by_screenshot(page.search_field, action)
