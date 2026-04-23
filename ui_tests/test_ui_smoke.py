import pytest

from ui_tests.pages.user_ui_page import UserUiPage


@pytest.mark.ui
def test_ui_smoke_page_loads_and_core_controls_visible(driver, wait, ui_base_url):
    page = UserUiPage(driver=driver, wait=wait, base_url=ui_base_url)
    page.open()

    assert "User Administration" in driver.page_source
    assert page.visible("username-input").is_displayed()
    assert page.visible("password-input").is_displayed()
    assert page.visible("login-btn").is_displayed()
    assert "Not logged in" in page.text("status-message")
