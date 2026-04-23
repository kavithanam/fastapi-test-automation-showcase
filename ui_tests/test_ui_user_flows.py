from uuid import uuid4

import pytest

from ui_tests.pages.user_ui_page import UserUiPage


@pytest.mark.ui
def test_ui_happy_path_login_and_load_users(driver, wait, ui_base_url):
    page = UserUiPage(driver=driver, wait=wait, base_url=ui_base_url)
    page.open()
    page.fill_login(username="alice", password="password123")
    page.click_login()

    status_text = page.wait_status_contains("Loaded")
    assert "Loaded" in status_text
    assert len(page.user_item_elements()) >= 1


@pytest.mark.ui
def test_ui_validation_error_create_user_missing_fields(driver, wait, ui_base_url):
    page = UserUiPage(driver=driver, wait=wait, base_url=ui_base_url)
    page.open()
    page.fill_login(username="alice", password="password123")
    page.click_login()
    page.wait_status_contains("Loaded")

    page.fill_create_user(name="", role="", email="")
    page.click_create_user()

    assert "Validation: all create-user fields are required" in page.wait_status_contains("Validation")


@pytest.mark.ui
def test_ui_error_state_when_users_api_fails(driver, wait, ui_base_url):
    page = UserUiPage(driver=driver, wait=wait, base_url=ui_base_url)
    page.open()
    page.set_simulate_api_failure(True)
    page.fill_login(username="alice", password="password123")
    page.click_login()

    assert "Failed to load users" in page.wait_status_contains("Failed to load users")


@pytest.mark.ui
@pytest.mark.e2e
def test_ui_e2e_create_and_delete_user(driver, wait, ui_base_url):
    page = UserUiPage(driver=driver, wait=wait, base_url=ui_base_url)
    unique_email = f"ui-{uuid4().hex[:8]}@example.com"
    unique_name = f"UiUser{uuid4().hex[:6]}"

    page.open()
    page.fill_login(username="alice", password="password123")
    page.click_login()
    page.wait_status_contains("Loaded")

    page.fill_create_user(name=unique_name, role="viewer", email=unique_email)
    page.click_create_user()
    page.wait_status_contains("Loaded")
    page.wait_until_user_present(unique_email)
    assert any(unique_email in text for text in page.user_rows_text())

    page.delete_user_row_containing(unique_email)
    page.wait_status_contains("Loaded")
    page.wait_until_user_absent(unique_email)
    assert all(unique_email not in text for text in page.user_rows_text())
