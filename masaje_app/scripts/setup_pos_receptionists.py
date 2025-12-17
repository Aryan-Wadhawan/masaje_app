"""
Setup POS Profiles and Receptionists for Masaje de Bohol
Creates POS Profiles, Receptionist role, employees, users, and branch permissions.

Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_pos_receptionists.setup_all
"""
import frappe

# Branch configuration
BRANCHES = [
    {"name": "CPG East Branch", "short": "cpgeast"},
    {"name": "Dao Branch", "short": "dao"},
    {"name": "Calceta Branch", "short": "calceta"},
    {"name": "Port Branch", "short": "port"},
    {"name": "Panglao Branch", "short": "panglao"},
]

EMAIL_DOMAIN = "masajedebohol.com"
DEFAULT_PASSWORD = "Masaje2024!"  # Change after first login


def setup_pos_profiles():
    """Create POS Profile for each branch (Cash only)."""
    print("\n1. Setting up POS Profiles...")
    
    # Check if POS Profile doctype is available
    if not frappe.db.exists("DocType", "POS Profile"):
        print("   ⚠ Skipping: POS Profile doctype not found (ERPNext may need migration)")
        print("   Run: bench --site masajedebohol.com migrate")
        return
    
    # Get company
    company = frappe.defaults.get_global_default("company") or "Masaje de Bohol"
    
    # Get warehouse (create if needed)
    warehouse = frappe.db.get_value("Warehouse", 
        {"company": company, "is_group": 0}, "name")
    if not warehouse:
        warehouse = f"Stores - {company[:3].upper()}"
    
    # Get write-off account
    wo_account = frappe.db.get_value("Account", 
        {"account_type": "Expense Account", "is_group": 0, "company": company}, "name")
    
    # Get cost center
    cost_center = frappe.db.get_value("Cost Center", 
        {"company": company, "is_group": 0}, "name")
    
    for branch in BRANCHES:
        profile_name = f"{branch['name']} POS"
        
        if frappe.db.exists("POS Profile", profile_name):
            print(f"   ✓ Exists: {profile_name}")
            continue
        
        # Determine price list (Panglao has different prices)
        price_list = "Panglao Prices" if "Panglao" in branch["name"] else "Standard Selling"
        
        try:
            pos_profile = frappe.get_doc({
                "doctype": "POS Profile",
                "name": profile_name,
                "company": company,
                "warehouse": warehouse,
                "selling_price_list": price_list,
                "currency": "PHP",
                "write_off_account": wo_account,
                "write_off_cost_center": cost_center,
                "payments": [{"mode_of_payment": "Cash", "default": 1}],
                "applicable_for_users": []
            })
            pos_profile.insert(ignore_permissions=True)
            print(f"   ✓ Created: {profile_name} (Price List: {price_list})")
        except Exception as e:
            print(f"   ❌ Failed: {profile_name} - {e}")
    
    frappe.db.commit()


def setup_receptionist_role():
    """Create Receptionist role with proper permissions."""
    print("\n2. Setting up Receptionist Role...")
    
    if frappe.db.exists("Role", "Receptionist"):
        print("   ✓ Role exists: Receptionist")
        return
    
    role = frappe.get_doc({
        "doctype": "Role",
        "role_name": "Receptionist",
        "desk_access": 1,
        "is_custom": 1
    })
    role.insert()
    print("   ✓ Created Role: Receptionist")
    
    # Define permissions
    permissions = [
        # DocType, Read, Write, Create, Delete, Submit, Cancel
        ("Service Booking", 1, 1, 1, 0, 0, 0),
        ("POS Invoice", 1, 1, 1, 0, 1, 0),
        ("Customer", 1, 1, 1, 0, 0, 0),
        ("Employee", 1, 0, 0, 0, 0, 0),  # Read-only for therapist list
        ("Branch", 1, 0, 0, 0, 0, 0),
        ("Item", 1, 0, 0, 0, 0, 0),
        ("Item Price", 1, 0, 0, 0, 0, 0),
        ("POS Profile", 1, 0, 0, 0, 0, 0),
        ("POS Opening Entry", 1, 1, 1, 0, 1, 0),
        ("POS Closing Entry", 1, 1, 1, 0, 1, 0),
        ("Mode of Payment", 1, 0, 0, 0, 0, 0),
    ]
    
    for perm in permissions:
        doctype, read, write, create, delete, submit, cancel = perm
        
        # Check if permission exists
        if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": "Receptionist"}):
            continue
        
        frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": doctype,
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": "Receptionist",
            "permlevel": 0,
            "read": read,
            "write": write,
            "create": create,
            "delete": delete,
            "submit": submit,
            "cancel": cancel,
            "if_owner": 0
        }).insert()
    
    print(f"   ✓ Added {len(permissions)} DocType permissions")
    frappe.db.commit()


def setup_designation():
    """Create Receptionist designation."""
    print("\n3. Setting up Designation...")
    try:
        # Check if Designation doctype is available
        if not frappe.db.exists("DocType", "Designation"):
            print("   ⚠ Skipping: Designation doctype not found (ERPNext may need migration)")
            return
        
        if not frappe.db.exists("Designation", "Receptionist"):
            frappe.get_doc({
                "doctype": "Designation",
                "designation_name": "Receptionist"
            }).insert()
            print("   ✓ Created: Receptionist designation")
        else:
            print("   ✓ Exists: Receptionist designation")
        frappe.db.commit()
    except Exception as e:
        print(f"   ⚠ Skipping Designation setup: {e}")
        print("   (This is OK if ERPNext hasn't been fully migrated yet)")


def setup_receptionists():
    """Create receptionist employees and users for each branch."""
    print("\n4. Setting up Receptionist Users...")
    
    for branch in BRANCHES:
        emp_name = f"{branch['name']} Receptionist"
        email = f"{branch['short']}.receptionist@{EMAIL_DOMAIN}"
        
        # Create Employee
        if not frappe.db.get_value("Employee", {"employee_name": emp_name}):
            emp = frappe.get_doc({
                "doctype": "Employee",
                "first_name": branch['name'].replace(" Branch", ""),
                "last_name": "Receptionist",
                "employee_name": emp_name,
                "gender": "Female",
                "date_of_birth": "1995-01-01",
                "date_of_joining": "2024-01-01",
                "status": "Active",
                "designation": "Receptionist",
                "branch": branch['name'],
                "company_email": email
            })
            emp.insert()
            print(f"   ✓ Created Employee: {emp_name}")
        else:
            print(f"   ✓ Employee exists: {emp_name}")
        
        # Create User
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": branch['name'].replace(" Branch", ""),
                "last_name": "Receptionist",
                "enabled": 1,
                "user_type": "System User",
                "roles": [{"role": "Receptionist"}],
                "new_password": DEFAULT_PASSWORD,
                "send_welcome_email": 0
            })
            user.insert(ignore_permissions=True)
            print(f"   ✓ Created User: {email}")
            
            # Add User Permission for branch restriction
            frappe.get_doc({
                "doctype": "User Permission",
                "user": email,
                "allow": "Branch",
                "for_value": branch['name'],
                "is_default": 1
            }).insert(ignore_permissions=True)
            print(f"      └─ Branch restricted to: {branch['name']}")
        else:
            print(f"   ✓ User exists: {email}")
    
    frappe.db.commit()


def setup_all():
    """Run complete POS and Receptionist setup."""
    print("=" * 60)
    print("SETTING UP POS PROFILES AND RECEPTIONISTS")
    print("=" * 60)
    
    setup_pos_profiles()
    setup_receptionist_role()
    setup_designation()
    setup_receptionists()
    
    print("\n" + "=" * 60)
    print("✓ SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nReceptionist Login Credentials:")
    print(f"  Password: {DEFAULT_PASSWORD}")
    print(f"  Emails:")
    for branch in BRANCHES:
        print(f"    - {branch['short']}.receptionist@{EMAIL_DOMAIN}")
    print("\n⚠️  Please change passwords after first login!")


if __name__ == "__main__":
    setup_all()
