"""
Add POS Page Access for Receptionist Role
Run: bench --site erpnext.localhost execute masaje_app.scripts.add_pos_page_access.setup
"""
import frappe


def setup():
    """Add Receptionist role to POS Page permissions"""
    print("Adding Receptionist access to POS page...")
    
    page_name = "point-of-sale"
    role = "Receptionist"
    
    # Check if already added
    existing = frappe.db.exists("Has Role", {
        "parent": page_name,
        "parenttype": "Page",
        "role": role
    })
    
    if existing:
        print(f"  - {role} already has access to POS page")
        return
    
    # Get the Page doc
    page = frappe.get_doc("Page", page_name)
    page.append("roles", {"role": role})
    page.save()
    
    frappe.db.commit()
    print(f"  + Added {role} to POS page")
    print("✓ Done! Receptionist can now access Point of Sale.")


if __name__ == "__main__":
    setup()
