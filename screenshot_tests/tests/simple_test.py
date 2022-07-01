from selenium.webdriver.common.by import By

from screenshot_tests.utils.screenshots import TestCase


class TestExample(TestCase):
    """Tests for https://go.mail.ru"""

    def test_main_page(self):
        self.driver.get("https://go.mail.ru/")

        def action():
            # Убираем фокус с инпута, чтобы тест не флакал из-за курсора
            self.driver.find_element(By.XPATH, "//*[text()='найти']").click()

        self.check_by_screenshot(None, action=action, full_page=True)

    def test_main_page_flaky(self):
        self.driver.get("https://go.mail.ru/")
        # Чтобы посмотреть как выглядит сломанный тeест в отчетe
        self.driver.find_element(By.XPATH, "//input[not(@type='hidden')]").send_keys("foo")
        self.check_by_screenshot(None, full_page=True)

    def test_search_block(self):
        self.driver.get("https://go.mail.ru/")

        def action():
            # Тестируем подсветку таба после переключения на другую вертикаль
            self.driver.find_element(By.XPATH, "//span[contains(text(), 'Соцсети')]").click()

        self.check_by_screenshot((By.CSS_SELECTOR, ".MainVerticalsNav-listItemActive"), action=action)
