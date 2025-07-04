from playwright.sync_api import sync_playwright
import json

def scrape_notion_users():
    def is_valid_name(name):
        name = name.strip()
        lower = name.lower()
        invalid_phrases = [
            "copy link", "invite", "permission", "generate", "contacts",
            "role", "only people", "teamspaces", "groups", "account",
            "user", "guests", "members", "unknown", "people", "admin",
            "view", "email", "workspace", "settings", "search"
        ]
        if "'s notion" in lower:
            return False
        if len(name) < 2 or len(name) > 40 or name.isdigit():
            return False
        return not any(phrase in lower for phrase in invalid_phrases)


    def extract_role(lines):
        known_roles = ["admin", "member", "viewer", "guest", "workspace owner", "owner"]
        for l in lines:
            l_lower = l.lower()
            for r in known_roles:
                if r in l_lower:
                    return r.title()
        return "Unknown"
    
    def deduplicate_by_email_keep_best(users):
        best_users = {}
        for user in users:
            print("\n[debug] Block lines:")
            for i, l in enumerate(lines):
                print(f"{i}: {l}")

            email = user['email']
          
            if email not in best_users or len(user['name']) > len(best_users[email]['name']):
                best_users[email] = user
        return list(best_users.values())


    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="notion_session.json")
        page = context.new_page()

        page.goto("https://www.notion.so", timeout=60000)
        page.wait_for_timeout(8000)
        page.screenshot(path="1_dashboard_loaded.png")

        page.locator("text=Settings").first.wait_for(timeout=10000)
        page.locator("text=Settings").first.click()
        page.wait_for_timeout(3000)
        page.screenshot(path="2_settings_clicked.png")

        page.locator("text=People").first.wait_for(timeout=8000)
        page.locator("text=People").first.click()
        page.wait_for_timeout(3000)
        page.screenshot(path="3_people_tab.png")


        tab = page.locator("div[role='tab']").filter(has_text="Members").first
        tab.wait_for(timeout=5000)
        tab.click()
        print("[info] Clicked Members tab.")
        page.wait_for_timeout(4000)
        page.screenshot(path="4_members_tab.png")

       
        blocks = page.locator("div:has-text('@')").all()
        print(f"[debug] Found {len(blocks)} blocks containing '@'")

        users = []

        for block in blocks:
            try:
                text = block.inner_text().strip()
                lines = text.splitlines()

                for i in range(len(lines) - 1):
                    line = lines[i].strip()
                    next_line = lines[i + 1].strip()

                 
                    if is_valid_name(line) and "@" in next_line:
                        name = line
                        email = next_line
                        role = "Unknown"

                     
                        for j in range(i + 2, min(i + 5, len(lines))):
                            role_candidate = lines[j].strip().lower()
                            if "workspace owner" in role_candidate:
                                role = "Workspace Owner"
                                break
                            elif "member" in role_candidate:
                                role = "Member"
                                break
                            elif "admin" in role_candidate:
                                role = "Admin"
                                break
                            elif "guest" in role_candidate:
                                role = "Guest"
                                break

                        users.append({
                            "name": name.strip(),
                            "email": email.strip(),
                            "role": role
                        })

            except Exception as e:
                print(f"[warn] Error parsing block: {e}")
                continue


        final_users = deduplicate_by_email_keep_best(users)
        print(json.dumps(final_users, indent=2))
        page.screenshot(path="5_final_output.png")
        browser.close()

scrape_notion_users()
