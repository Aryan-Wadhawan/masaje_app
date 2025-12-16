"""
Setup script to add custom fields and configure POS Settings
for therapist selection and commission calculation.

Run via: bench --site erpnext.localhost execute masaje_app.scripts.setup_therapist_commission.setup
"""
import frappe


def setup():
    """
    Main setup function:
    1. Add commission_rate field to Employee
    2. Add therapist field to POS Invoice
    3. Configure POS Settings to show therapist field at checkout
    """
    print("Setting up Therapist Commission...")
    
    # 1. Add commission_rate to Employee
    add_employee_commission_field()
    
    # 2. Add therapist to POS Invoice
    add_pos_invoice_therapist_field()
    
    # 3. Add therapist to POS Settings Invoice Fields
    add_therapist_to_pos_settings()
    
    frappe.db.commit()
    print("✓ Therapist Commission setup complete!")
    print("\nNext steps:")
    print("1. Set 'Commission Rate' on Employee records (e.g., 10 for 10%)")
    print("2. In POS, select Therapist before checkout")
    print("3. Commission will be calculated automatically on invoice submit")


def add_employee_commission_field():
    """Add commission_rate custom field to Employee doctype"""
    if frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "commission_rate"}):
        print("  - Employee.commission_rate already exists")
        return
    
    cf = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Employee",
        "fieldname": "commission_rate",
        "fieldtype": "Percent",
        "label": "Commission Rate",
        "insert_after": "grade",
        "description": "Commission percentage for services performed"
    })
    cf.insert()
    print("  + Added Employee.commission_rate field")


def add_pos_invoice_therapist_field():
    """Add therapist custom field to POS Invoice doctype"""
    if frappe.db.exists("Custom Field", {"dt": "POS Invoice", "fieldname": "therapist"}):
        print("  - POS Invoice.therapist already exists")
        return
    
    cf = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "POS Invoice",
        "fieldname": "therapist",
        "fieldtype": "Link",
        "label": "Therapist",
        "options": "Employee",
        "insert_after": "customer_name",
        "description": "Therapist who performed the service"
    })
    cf.insert()
    print("  + Added POS Invoice.therapist field")


def add_therapist_to_pos_settings():
    """Add therapist field to POS Settings for checkout screen"""
    # Get or create POS Settings
    if not frappe.db.exists("POS Settings", "POS Settings"):
        pos_settings = frappe.get_doc({"doctype": "POS Settings"})
        pos_settings.insert()
    else:
        pos_settings = frappe.get_doc("POS Settings")
    
    # Check if therapist already in invoice_fields
    existing_fields = [f.fieldname for f in pos_settings.invoice_fields]
    
    if "therapist" in existing_fields:
        print("  - Therapist already in POS Settings")
        return
    
    # Add therapist field
    pos_settings.append("invoice_fields", {
        "fieldname": "therapist",
        "label": "Therapist",
        "fieldtype": "Link",
        "options": "Employee",
        "reqd": 0
    })
    pos_settings.save()
    print("  + Added therapist to POS Settings Invoice Fields")


if __name__ == "__main__":
    setup()
