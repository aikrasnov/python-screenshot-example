from screenshot_tests.page_objects.elements import Page, Element, Locators


class YandexMainPage(Page):
    """https://yandex.ru"""

    path = ""

    news_header = Element(Locators.CSS_SELECTOR, ".news__header", "Хэдер с новостями")
    search_field = Element(Locators.CSS_SELECTOR, ".search2", "Поисковый блок")
    search_input = Element(Locators.CSS_SELECTOR, ".input__control", "Поисковый инпут")
