
import frappe

def execute():
    company = "Masaje de Bohol"
    create_user()
    assign_roles()
    set_permissions()
    create_pos_profile(company)

def create_user():
    email = "receptionist_main@masaje.com"
    if not frappe.db.exists("User", email):
        frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Receptionist",
            "last_name": "Main",
            "send_welcome_email": 0,
            "enabled": 1
        }).insert(ignore_permissions=True)
        print("Created User")

def assign_roles():
    email = "receptionist_main@masaje.com"
    user = frappe.get_doc("User", email)
    user.add_roles("Receptionist") 
    # Also needs Sales User maybe for POS? Yes.
    user.add_roles("Sales User")
    print("Assigned Roles")

def set_permissions():
    email = "receptionist_main@masaje.com"
    if not frappe.db.exists("User Permission", {"user": email, "allow": "Branch", "for_value": "Bohol Main"}):
        frappe.get_doc({
            "doctype": "User Permission",
            "user": email,
            "allow": "Branch",
            "for_value": "Bohol Main"
        }).insert(ignore_permissions=True)
        print("Set Branch Permission")

def create_pos_profile(company):
    if frappe.db.exists("POS Profile", "Bohol Main POS"):
        print("POS Profile exists")
        return

    write_off = "Write Off - MDB"
    income_account = "Sales - MDB"
    cash_account = "Cash - MDB"
    
    cash = frappe.db.get_value("Mode of Payment", {"type": "Cash"}, "name") or "Cash"
    if cash:
         payments = [{"mode_of_payment": cash, "default": 1, "account": cash_account}]
    else:
         payments = []

    if not write_off or not income_account or not payments:
        print("Could not find necessary accounts for POS Profile. Please setup Chart of Accounts.")
        return

    write_off_cc = frappe.db.get_value("Cost Center", {"cost_center_name": "Bohol Main", "company": company}, "name")
    if not write_off_cc:
        write_off_cc = "Bohol Main - MDB" # Fallback guess

    warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": "Bohol Main Store", "company": company}, "name")
    if not warehouse:
        warehouse = "Bohol Main Store - MDB"

    frappe.get_doc({
        "doctype": "POS Profile",
        "name": "Bohol Main POS",
        "company": company,
        "warehouse": warehouse,
        "currency": "PHP",
        "write_off_account": write_off,
        "write_off_cost_center": write_off_cc,
        "selling_price_list": "Bohol Main",
        "payments": payments,
        "applicable_for_users": [{"user": "receptionist_main@masaje.com"}]
    }).insert(ignore_permissions=True)
    print("Created POS Profile")

