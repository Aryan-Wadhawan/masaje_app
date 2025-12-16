"""
Reload Masaje Reception workspace to sync shortcuts
Run: bench --site erpnext.localhost execute masaje_app.scripts.reload_workspace.setup
"""
import frappe
import json


def setup():
    """Reload the Masaje Reception workspace from file"""
    print("Reloading Masaje Reception workspace...")
    
    ws = frappe.get_doc("Workspace", "Masaje Reception")
    
    # Ensure POS shortcut is in content
    content = json.loads(ws.content or "[]")
    
    # Check if sc_pos shortcut exists in content
    has_pos_shortcut = any(
        item.get("id") == "sc_pos" or 
        (item.get("type") == "shortcut" and item.get("data", {}).get("shortcut_name") == "Point of Sale")
        for item in content
    )
    
    if not has_pos_shortcut:
        # Find Quick Access header and insert after it
        for i, item in enumerate(content):
            if item.get("id") == "header_1" or "Quick Access" in str(item.get("data", {})):
                # Insert shortcuts after header
                insert_idx = i + 1
                # Add POS shortcut
                content.insert(insert_idx + 1, {
                    "id": "sc_pos",
                    "type": "shortcut",
                    "data": {"shortcut_name": "Point of Sale", "col": 3}
                })
                ws.content = json.dumps(content)
                print("  + Added POS shortcut to content")
                break
    else:
        print("  - POS shortcut already in content")
    
    # Ensure shortcut record exists
    has_shortcut_record = any(s.label == "Point of Sale" for s in ws.shortcuts)
    if not has_shortcut_record:
        ws.append("shortcuts", {
            "label": "Point of Sale",
            "link_to": "point-of-sale",
            "type": "Page",
            "color": "Blue"
        })
        print("  + Added POS shortcut record")
    else:
        print("  - POS shortcut record exists")
    
    ws.save()
    frappe.db.commit()
    
    print("✓ Workspace reloaded!")


if __name__ == "__main__":
    setup()
