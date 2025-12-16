import frappe
from frappe.permissions import add_permission, update_permission_property

def setup_permissions():
    role = "Receptionist"
    doctypes = ["Service Booking", "Therapist Schedule", "POS Profile", "POS Invoice", "Sales Invoice"]
    
    for dt in doctypes:
        # Ensure minimal permission exists
        perm_exists = frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role})
        if not perm_exists:
            add_permission(dt, role, 0) # Level 0
            print(f"Added Permission for {dt}")
            
            # In this version, apply_user_permissions/user_permission_doctypes columns appear missing.
            # We assume User Permissions are applied by default if User Permission documents exist.
            pass
            
    frappe.db.commit()
    print("Permissions Updated.")

if __name__ == "__main__":
    frappe.connect()
    setup_permissions()
