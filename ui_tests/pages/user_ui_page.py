from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class UserUiPage:
    def __init__(self, driver, wait, base_url):
        self.driver = driver
        self.wait = wait
        self.base_url = base_url

    def open(self):
        self.driver.get(self.base_url)

    def _by_testid(self, testid):
        return (By.CSS_SELECTOR, f'[data-testid="{testid}"]')

    def visible(self, testid):
        return self.wait.until(EC.visibility_of_element_located(self._by_testid(testid)))

    def text(self, testid):
        return self.visible(testid).text

    def fill_login(self, username, password):
        username_input = self.visible("username-input")
        password_input = self.visible("password-input")
        username_input.clear()
        username_input.send_keys(username)
        password_input.clear()
        password_input.send_keys(password)

    def click_login(self):
        self.visible("login-btn").click()

    def wait_status_contains(self, expected_text):
        self.wait.until(EC.text_to_be_present_in_element(self._by_testid("status-message"), expected_text))
        return self.text("status-message")

    def set_simulate_api_failure(self, enabled):
        checkbox = self.visible("simulate-api-failure")
        if checkbox.is_selected() != enabled:
            checkbox.click()

    def user_item_elements(self):
        return self.driver.find_elements(By.CSS_SELECTOR, '[data-testid^="user-item-"]')

    def user_rows_text(self):
        return [element.text for element in self.user_item_elements()]

    def fill_create_user(self, name, role, email):
        name_input = self.visible("new-name-input")
        role_input = self.visible("new-role-input")
        email_input = self.visible("new-email-input")
        name_input.clear()
        role_input.clear()
        email_input.clear()
        name_input.send_keys(name)
        role_input.send_keys(role)
        email_input.send_keys(email)

    def click_create_user(self):
        self.visible("create-user-btn").click()

    def wait_until_user_present(self, expected_text):
        self.wait.until(lambda driver: any(expected_text in row.text for row in self.user_item_elements()))

    def wait_until_user_absent(self, expected_text):
        self.wait.until(lambda driver: all(expected_text not in row.text for row in self.user_item_elements()))

    def delete_user_row_containing(self, expected_text):
        for row in self.user_item_elements():
            if expected_text in row.text:
                delete_button = row.find_element(By.CSS_SELECTOR, '[data-testid^="delete-user-btn-"]')
                delete_button.click()
                return
        raise AssertionError(f"Could not find user row containing '{expected_text}'")
