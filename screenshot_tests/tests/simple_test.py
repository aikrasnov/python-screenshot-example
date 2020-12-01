from screenshot_tests.utils.screenshots import TestCase
from selenium.webdriver.common.by import By


class TestExample(TestCase):
    """Tests for https://go.mail.ru"""

    def test_main_page(self):
        self.driver.get("https://go.mail.ru/")

        def action():
            # Убираем фокус с инпута, чтобы тест не флакал из-за курсора
            self.driver.find_element_by_xpath("//*[text()='найти']").click()

        self.check_by_screenshot(None, action=action, full_page=True)

    def test_main_page_flaky(self):
        self.driver.get("https://go.mail.ru/")
        # Чтобы посмотреть как выглядит сломанный тест в отчетe
        self.driver.find_element_by_xpath("//input[not(@type='hidden')]").send_keys("foo")
        self.check_by_screenshot(None, full_page=True)

    def test_search_result(self):
        self.driver.get("https://go.mail.ru/")

        def action():
            self.driver.find_element_by_xpath("//span[contains(text(), 'Соцсети')]").click()

        self.check_by_screenshot((By.CSS_SELECTOR, ".MainPage-verticalLinksWrapper"), action=action)
