"""
Update Masaje Reception workspace to include Number Cards
Run: bench --site erpnext.localhost execute masaje_app.scripts.update_workspace_cards.setup
"""
import frappe
import json


def setup():
    """Update the Masaje Reception workspace with Number Cards"""
    print("Updating Masaje Reception workspace...")
    
    workspace_name = "Masaje Reception"
    
    if not frappe.db.exists("Workspace", workspace_name):
        print(f"Workspace '{workspace_name}' not found")
        return
    
    workspace = frappe.get_doc("Workspace", workspace_name)
    
    # Add Number Cards to the workspace
    number_cards = [
        {"number_card_name": "Today's Sales"},
        {"number_card_name": "Bookings Today"},
        {"number_card_name": "Pending Bookings"},
        {"number_card_name": "Completed Today"}
    ]

    
    # Clear existing and add new
    workspace.number_cards = []
    for card in number_cards:
        workspace.append("number_cards", card)
    
    # Update content to show Number Cards at the top
    content = json.loads(workspace.content or "[]")
    
    # Add Number Cards section at the beginning
    new_content = [
        {"id": "nc_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Dashboard</b></span>", "col": 12}},
        {"id": "nc_1", "type": "number_card", "data": {"number_card_name": "Today's Sales", "col": 3}},
        {"id": "nc_2", "type": "number_card", "data": {"number_card_name": "Bookings Today", "col": 3}},
        {"id": "nc_3", "type": "number_card", "data": {"number_card_name": "Pending Bookings", "col": 3}},
        {"id": "nc_4", "type": "number_card", "data": {"number_card_name": "Completed Today", "col": 3}},
        {"id": "spacer_nc", "type": "spacer", "data": {"col": 12}}
    ]

    
    # Find if header already exists
    has_nc_header = any(item.get("id") == "nc_header" for item in content)
    
    if not has_nc_header:
        # Insert at the beginning
        content = new_content + content
        workspace.content = json.dumps(content)
    
    workspace.save()
    frappe.db.commit()
    
    print("✓ Workspace updated with Number Cards!")


if __name__ == "__main__":
    setup()
