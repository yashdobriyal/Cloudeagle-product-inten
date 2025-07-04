from playwright.sync_api import sync_playwright

def save_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.notion.so/login")
        print("Please log in manually and complete MFA...")

        page.wait_for_timeout(60000)  
        context.storage_state(path="notion_session.json")
        print("Session saved.")
        browser.close()

save_session()
