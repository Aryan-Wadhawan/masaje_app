"""
Setup Branch-Based Restrictions for Receptionist
Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_branch_restrictions.setup

This script:
1. Creates User Permissions to restrict Receptionist users to their assigned branch
2. The branch is taken from the Employee linked to the User

To assign a receptionist to a branch:
1. Create/edit the Employee record
2. Set the "Branch" field on the Employee
3. Link the User to the Employee
4. Run this script or manually add User Permission
"""
import frappe


def setup():
    """Set up branch restrictions for all Receptionist users"""
    print("Setting up branch-based restrictions...")
    
    # Find all users with Receptionist role
    receptionist_users = frappe.db.sql("""
        SELECT DISTINCT hr.parent
        FROM `tabHas Role` hr
        JOIN `tabUser` u ON hr.parent = u.name
        WHERE hr.role = 'Receptionist'
        AND u.enabled = 1
    """, as_dict=True)
    
    if not receptionist_users:
        print("  No active Receptionist users found")
        return
    
    for user_row in receptionist_users:
        user = user_row.parent
        setup_branch_restriction_for_user(user)
    
    frappe.db.commit()
    print("✓ Branch restrictions setup complete!")
    
    print("\n📋 To assign a receptionist to a branch:")
    print("   1. Go to Employee > Edit the receptionist's Employee record")
    print("   2. Set the 'Branch' field")
    print("   3. Run this script again OR add User Permission manually")


def setup_branch_restriction_for_user(user):
    """Set up branch restriction for a specific user"""
    # Get the Employee linked to this user
    employee = frappe.db.get_value("Employee", {"user_id": user}, ["name", "branch"], as_dict=True)
    
    if not employee:
        print(f"  ! {user}: No linked Employee found")
        return
    
    if not employee.branch:
        print(f"  ! {user}: Employee has no branch assigned")
        return
    
    branch = employee.branch
    
    # Check if User Permission already exists
    existing = frappe.db.exists("User Permission", {
        "user": user,
        "allow": "Branch",
        "for_value": branch
    })
    
    if existing:
        print(f"  - {user}: Already restricted to {branch}")
        return
    
    # Create User Permission
    user_perm = frappe.new_doc("User Permission")
    user_perm.user = user
    user_perm.allow = "Branch"
    user_perm.for_value = branch
    user_perm.apply_to_all_doctypes = 1
    user_perm.insert(ignore_permissions=True)
    
    print(f"  + {user}: Restricted to {branch}")


def remove_branch_restriction(user):
    """Remove branch restrictions for a user (if needed)"""
    frappe.db.delete("User Permission", {
        "user": user,
        "allow": "Branch"
    })
    frappe.db.commit()
    print(f"Removed branch restrictions for {user}")


if __name__ == "__main__":
    setup()
