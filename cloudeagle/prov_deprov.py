from playwright.sync_api import sync_playwright

def provision_user(email, role="Member"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="notion_session.json")
        page = context.new_page()

        page.goto("https://www.notion.so", timeout=60000)
        page.wait_for_timeout(8000)

        page.locator("text=Settings").first.click()
        page.wait_for_timeout(2000)
        page.locator("text=People").first.click()
        page.wait_for_timeout(2000)

        # ⬇️ Click "Add members"
# Locate and click the "Add members" button in horizontal layout
        try:
            add_members_btn = page.locator("div[role='button']", has_text="Add members").first
            add_members_btn.wait_for(state="visible", timeout=5000)
            add_members_btn.click()
            page.wait_for_timeout(1000)
            print("[info] Clicked Add members")
        except Exception as e:
            print(f"[error] Failed to click Add members: {e}")
            page.screenshot(path="add_members_click_error.png")
            return



        # ⬇️ Fill email field
        email_input = page.locator("input[type='email']").first
        email_input.wait_for(timeout=10000)
        email_input.fill(email)

        page.wait_for_timeout(500)

        # Wait for the dropdown overlay to appear with the email
        try:
            suggestion = page.locator(f"div:visible >> text={email}").first
            suggestion.wait_for(timeout=5000)
            suggestion.click()
            print(f"[info] Selected user suggestion: {email}")
        except Exception as e:
            print(f"[warn] Could not find or click email suggestion: {e}")
            page.screenshot(path="suggestion_not_found.png")
            return

        try:
            send_button = page.locator("div[role='button']", has_text="Send invite").first
            send_button.wait_for(state="visible", timeout=5000)
            send_button.scroll_into_view_if_needed()
            page.wait_for_timeout(500)

            # Retry click until aria-disabled is false
            for attempt in range(5):
                disabled = send_button.get_attribute("aria-disabled")
                if disabled == "true":
                    print(f"[warn] Send invite still disabled (attempt {attempt + 1})")
                    page.wait_for_timeout(1000)
                else:
                    send_button.click(force=True)
                    print("[info] Send invite clicked successfully.")
                    page.wait_for_timeout(3000)  # Wait to observe UI change
                    break
            else:
                print("[error] Send invite button never became enabled.")
                page.screenshot(path="send_invite_failed.png")
                return
        except Exception as e:
            print(f"[error] Failed to click Send invite: {e}")
            page.screenshot(path="send_invite_exception.png")
            return








def deprovision_user(email):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="notion_session.json")
        page = context.new_page()

        try:
            # Navigate to Notion and Members tab
            page.goto("https://www.notion.so", timeout=60000)
            page.wait_for_timeout(8000)
            page.locator("text=Settings").first.click()
            page.wait_for_timeout(2000)
            page.locator("text=People").first.click()
            page.wait_for_timeout(2000)
            page.locator("div[role='tab']").filter(has_text="Members").first.click()
            page.wait_for_timeout(2000)

            # Locate user rows by data-index
            user_rows = page.locator("div[data-index]")
            count = user_rows.count()
            print(f"[debug] Found {count} user rows.")

            found = False
            for i in range(count):
                row = user_rows.nth(i)
                row_text = row.inner_text().strip()

                if email in row_text:
                    print(f"[info] Found user row for {email} at index {i}")
                    try:
                        # Click dropdown (use working method)
                        dropdown = row.locator("div[role='button']").filter(has_text="Workspace owner").first
                        dropdown.wait_for(timeout=3000)
                        dropdown.scroll_into_view_if_needed()
                        dropdown.click()
                        print(f"[info] Opened role dropdown for {email}")
                        page.wait_for_timeout(1000)

                        # Click 'Remove from workspace'
                        remove_option = page.locator("div[role='menuitem']").filter(has_text="Remove from workspace").first
                        remove_option.wait_for(timeout=3000)
                        remove_option.click()
                        print(f"[info] Selected 'Remove from workspace' for {email}")
                        page.wait_for_timeout(1000)

                        # Confirm modal
                        confirm_button = page.locator("div[role='button']").filter(has_text="Remove").first
                        confirm_button.wait_for(timeout=5000)
                        confirm_button.scroll_into_view_if_needed()
                        confirm_button.click()
                        print(f"[info] Confirmed removal of {email}")
                        found = True
                        break
                    except Exception as e:
                        print(f"[error] Failed to deprovision user at index {i}: {e}")
                        page.screenshot(path="deprovision_error.png")
                        break

            if not found:
                print(f"[warn] Could not find or remove user with email {email}")
                page.screenshot(path="user_not_found.png")

        except Exception as e:
            print(f"[error] Unexpected error: {e}")
            page.screenshot(path="deprovision_unexpected_error.png")
        finally:
            browser.close()

# Entry point: Ask user for input
if __name__ == "__main__":
    action = input("Do you want to add or remove a user? (add/remove): ").strip().lower()

    if action not in ["add", "remove"]:
        print("❌ Invalid input. Please type 'add' or 'remove'.")
    else:
        email = input("Enter the user's email: ").strip()
        if action == "add":
            provision_user(email)
        else:
            deprovision_user(email)
