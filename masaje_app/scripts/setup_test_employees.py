"""
Setup Test Employee Data for Receptionist
Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_test_employees.setup
"""
import frappe


def setup():
    """Create designations and test employee records"""
    print("Setting up test employee data...")
    
    # 1. Create Designations
    create_designations()
    
    # 2. Create test receptionist employee
    create_receptionist_employee()
    
    # 3. Run branch restrictions
    from masaje_app.scripts.setup_branch_restrictions import setup as setup_restrictions
    setup_restrictions()
    
    frappe.db.commit()
    print("\n✓ Test employee setup complete!")


def create_designations():
    """Create Therapist and Receptionist designations"""
    designations = ["Therapist", "Receptionist", "Manager"]
    
    for name in designations:
        if not frappe.db.exists("Designation", name):
            doc = frappe.new_doc("Designation")
            doc.designation_name = name
            doc.insert()
            print(f"  + Created Designation: {name}")
        else:
            print(f"  - Designation exists: {name}")


def create_receptionist_employee():
    """Create an Employee record for the receptionist user"""
    user_email = "receptionist_main@masaje.com"
    employee_name = "Test Receptionist"
    
    # Check if employee already exists for this user
    existing = frappe.db.get_value("Employee", {"user_id": user_email}, "name")
    if existing:
        print(f"  - Employee already exists for {user_email}: {existing}")
        # Update branch if not set
        frappe.db.set_value("Employee", existing, {
            "branch": "Bohol Main",
            "designation": "Receptionist"
        })
        print(f"  - Updated {existing} with branch and designation")
        return
    
    # Get the default company
    company = frappe.defaults.get_global_default("company")
    
    # Create new employee
    emp = frappe.new_doc("Employee")
    emp.first_name = "Test"
    emp.last_name = "Receptionist"
    emp.employee_name = employee_name
    emp.company = company
    emp.status = "Active"
    emp.gender = "Female"  # Required field
    emp.date_of_birth = "1990-01-01"  # Required field
    emp.date_of_joining = "2025-01-01"  # Required field
    emp.designation = "Receptionist"
    emp.branch = "Bohol Main"
    emp.user_id = user_email
    emp.commission_rate = 0  # Receptionists don't get commission
    
    try:
        emp.insert(ignore_permissions=True)
        print(f"  + Created Employee: {emp.name} ({employee_name})")
        print(f"    - Designation: Receptionist")
        print(f"    - Branch: Bohol Main")
        print(f"    - User ID: {user_email}")
    except Exception as e:
        print(f"  ! Error creating employee: {e}")


if __name__ == "__main__":
    setup()
