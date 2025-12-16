"""
Update Masaje Reception workspace content with custom POS HTML button
Run: bench --site erpnext.localhost execute masaje_app.scripts.add_pos_html_button.setup
"""
import frappe
import json


def setup():
    """Add custom HTML block with POS button to workspace content"""
    print("Adding POS button to workspace...")
    
    workspace = frappe.get_doc("Workspace", "Masaje Reception")
    content = json.loads(workspace.content or "[]")
    
    # Check if POS HTML block already exists
    has_pos_html = any(item.get("id") == "pos_button" for item in content)
    
    if has_pos_html:
        print("  - POS button already exists")
        return
    
    # Find the Quick Access header and insert POS button after it
    for i, item in enumerate(content):
        if item.get("id") == "header_1":  # Quick Access header
            # Insert POS button HTML after the header
            pos_button = {
                "id": "pos_button",
                "type": "onboarding",
                "data": {
                    "onboarding_name": "Open Point of Sale",
                    "col": 12
                }
            }
            # Actually, let's use a paragraph type with HTML link
            pos_block = {
                "id": "pos_button",
                "type": "paragraph",
                "data": {
                    "text": "<div style='margin-bottom: 15px;'><a href='/app/point-of-sale' class='btn btn-primary btn-lg' style='font-size: 16px; padding: 12px 30px;'><i class='fa fa-shopping-cart'></i> Open Point of Sale</a></div>",
                    "col": 12
                }
            }
            content.insert(i + 1, pos_block)
            break
    
    workspace.content = json.dumps(content)
    workspace.save()
    frappe.db.commit()
    
    print("  + Added POS button to workspace!")
    print("✓ Done! Refresh browser to see the button.")


if __name__ == "__main__":
    setup()
