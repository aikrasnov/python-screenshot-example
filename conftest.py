import pytest
import logging
import allure
from selenium.webdriver import Chrome, ChromeOptions


class Config:
    BASE_URL = "baseurl"
    STAGING = "staging"


@pytest.fixture()
def driver():
    options = ChromeOptions()
    options.add_argument("--headless")
    webdriver = Chrome(desired_capabilities=options.to_capabilities())
    webdriver.implicitly_wait(5)
    yield webdriver
    allure.attach(webdriver.current_url, "last url", allure.attachment_type.URI_LIST)
    webdriver.quit()


def pytest_addoption(parser):
    """Command line parser."""
    parser.addoption(f'--{Config.BASE_URL}',
                     default='https://yandex.ru',
                     dest=Config.BASE_URL,
                     action='store',
                     metavar='str',
                     help='Environment for run tests.')
    parser.addoption(f'--{Config.STAGING}',
                     default='https://yandex.ru',
                     dest=Config.STAGING,
                     action='store',
                     metavar='str',
                     help='Environment for compare with testing.')
    parser.addoption('--log_level',
                     default='INFO',
                     dest='log_level',
                     action='store',
                     metavar='str',
                     help='Logging level.')


def pytest_configure(config):
    """Configure test run."""
    logging.basicConfig(level=config.getoption('log_level'),
                        format='%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)',
                        datefmt='%Y-%m-%d %H:%M:%S')
