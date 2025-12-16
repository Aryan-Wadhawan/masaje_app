"""
Setup Receptionist Role Permissions
Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_receptionist_permissions.setup
"""
import frappe


def setup():
    """Set up complete permissions for Receptionist role"""
    print("Setting up Receptionist role permissions...")
    
    # DocTypes that Receptionist needs access to
    permissions = [
        # Core Operations
        {"doctype": "Service Booking", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 0, "cancel": 0},
        {"doctype": "POS Invoice", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1, "cancel": 0},
        {"doctype": "Customer", "read": 1, "write": 1, "create": 1, "delete": 0},
        
        # Scheduling
        {"doctype": "Therapist Schedule", "read": 1, "write": 0, "create": 0, "delete": 0},
        
        # Reference Data (read-only)
        {"doctype": "Employee", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"doctype": "Item", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"doctype": "Branch", "read": 1, "write": 0, "create": 0, "delete": 0},
        {"doctype": "POS Profile", "read": 1, "write": 0, "create": 0, "delete": 0},
        
        # POS Operations
        {"doctype": "POS Opening Entry", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
        {"doctype": "POS Closing Entry", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
        {"doctype": "Mode of Payment", "read": 1, "write": 0, "create": 0, "delete": 0},
    ]
    
    for perm in permissions:
        add_permission(perm)
    
    frappe.db.commit()
    print("✓ Receptionist permissions setup complete!")


def add_permission(perm_data):
    """Add or update permission for Receptionist role"""
    doctype = perm_data.pop("doctype")
    role = "Receptionist"
    
    # Check if permission exists
    existing = frappe.db.exists("DocPerm", {
        "parent": doctype,
        "role": role,
        "permlevel": 0
    })
    
    if existing:
        frappe.db.set_value("DocPerm", existing, perm_data)
        print(f"  - Updated: {doctype}")
    else:
        # Get DocType to add custom permission
        try:
            doc = frappe.get_doc("DocType", doctype)
            doc.append("permissions", {
                "role": role,
                "permlevel": 0,
                **perm_data
            })
            doc.save()
            print(f"  + Added: {doctype}")
        except Exception as e:
            print(f"  ! Error on {doctype}: {e}")


if __name__ == "__main__":
    setup()
