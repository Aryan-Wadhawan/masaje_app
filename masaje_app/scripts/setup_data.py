
import frappe

def setup_demo_data():
    create_branches()
    create_warehouses()
    create_cost_centers()
    create_price_lists()
    create_items()
    create_item_prices()
    create_employees()
    create_schedules()
    frappe.db.commit()
    print("Demo Data created successfully.")

def create_branches():
    branches = ["Bohol Main", "Bohol Downtown"]
    for b in branches:
        if not frappe.db.exists("Branch", b):
            frappe.get_doc({"doctype": "Branch", "branch": b}).insert()
            print(f"Created Branch: {b}")

def create_warehouses():
    # Ensure root company warehouse exists/find it
    company = "Masaje de Bohol"
    parent_wh = frappe.db.get_value("Warehouse", {"company": company, "is_group": 1}, "name")
    if not parent_wh:
        # Fallback if no group warehouse found, rarely happens in fresh install
        parent_wh = "All Warehouses - MDB" # Construct likely name or skip hierarchy check for now if lazy
        
    warehouses = [
        {"name": "Bohol Main Store", "parent": parent_wh},
        {"name": "Bohol Downtown Store", "parent": parent_wh}
    ]
    
    for wh in warehouses:
        if not frappe.db.exists("Warehouse", {"warehouse_name": wh["name"], "company": company}):
            # We need a valid parent. Let's try to get 'Stores - MDB' or 'All Warehouses - ...'
            # Simpler: just get the default 'Stores' or ANY group warehouse
            if not parent_wh:
                 parent_wh = frappe.db.get_value("Warehouse", {"is_group": 1, "company": company})
            
            try:
                frappe.get_doc({
                    "doctype": "Warehouse",
                    "warehouse_name": wh["name"],
                    "company": company,
                    "parent_warehouse": parent_wh
                }).insert(ignore_permissions=True)
                print(f"Created Warehouse: {wh['name']}")
            except frappe.DuplicateEntryError:
                print(f"Warehouse {wh['name']} already exists (caught DuplicateEntryError).")

def create_cost_centers():
    company = "Masaje de Bohol"
    ccs = ["Bohol Main", "Bohol Downtown"] # Removed "- MDB"
    # Get a parent CC
    parent_cc = frappe.db.get_value("Cost Center", {"company": company, "is_group": 1}, "name")
    
    for cc_name in ccs:
        if not frappe.db.exists("Cost Center", {"cost_center_name": cc_name, "company": company}):
             try:
                 frappe.get_doc({
                    "doctype": "Cost Center",
                    "cost_center_name": cc_name,
                    "company": company,
                    "parent_cost_center": parent_cc
                }).insert()
                 print(f"Created Cost Center: {cc_name}")
             except frappe.DuplicateEntryError:
                 print(f"Cost Center {cc_name} exists.")

def create_price_lists():
    pls = ["Bohol Main", "Bohol Downtown"]
    for pl in pls:
        if not frappe.db.exists("Price List", pl):
            frappe.get_doc({
                "doctype": "Price List",
                "price_list_name": pl,
                "enabled": 1,
                "selling": 1,
                "buying": 0,
                "currency": "PHP" 
            }).insert()
            print(f"Created Price List: {pl}")

def create_items():
    # Item Groups
    for ig in ["Services", "Products"]:
        if not frappe.db.exists("Item Group", ig):
            frappe.get_doc({"doctype": "Item Group", "item_group_name": ig, "parent_item_group": "All Item Groups"}).insert()

    # Service Item
    if not frappe.db.exists("Item", "Service-Massage-60"):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": "Service-Massage-60",
            "item_name": "Full Body Massage (60m)",
            "item_group": "Services",
            "is_stock_item": 0,
            "stock_uom": "Unit"
        }).insert()

    # Product Item
    if not frappe.db.exists("Item", "Product-TigerBalm"):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": "Product-TigerBalm",
            "item_name": "Tiger Balm (50g)",
            "item_group": "Products",
            "is_stock_item": 1,
            "stock_uom": "Unit",
            "valuation_rate": 50 # Default cost
        }).insert()

def create_item_prices():
    # Helper to get all relevant items
    services = ["Service-Massage-60", "Service-Massage-90", "Service-Manicure", "Service-Pedicure"]
    products = ["Product-TigerBalm"]
    
    # Base rates (Standard)
    # Ideally we'd have specific logic, but for robustness let's just ensure they exist everywhere.
    base_rates = {
        "Service-Massage-60": 1000,
        "Service-Massage-90": 1400,
        "Service-Manicure": 350,
        "Service-Pedicure": 450,
        "Product-TigerBalm": 150
    }
    
    # Specific overrides
    overrides = {
        "Bohol Downtown": {
            "Service-Massage-60": 800,
            "Service-Massage-90": 1200,
            "Product-TigerBalm": 90
        }
    }
    
    # Get all active selling price lists
    # Aggressive Price Setup
    selling_pls = frappe.get_all("Price List", {"selling": 1}, pluck="name")
    
    # Standard rates for types
    rates = {
        "Service": 800,
        "Product": 1500, # Tiger Balm etc
        "Services": 1000
    }
    
    items = frappe.get_all("Item", fields=["name", "item_code", "item_group"])
    
    for pl in selling_pls:
        for item in items:
            # Check if price exists
            if not frappe.db.exists("Item Price", {"item_code": item.item_code, "price_list": pl}):
                # Determine rate
                rate = rates.get(item.item_group, 500)
                
                # Specific overrides
                if "Tiger" in item.item_code: rate = 300
                if "Manicure" in item.item_code: rate = 450
                
                frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item.item_code,
                    "price_list": pl,
                    "price_list_rate": rate,
                    "currency": "PHP"
                }).insert(ignore_permissions=True)
                print(f"Set Price: {item.item_code} -> {rate} in {pl}")
            else:
                # Optional: Force update to ensure consistency
                # This part of the original code was trying to update, but the new logic focuses on creation if missing.
                # If an update is desired, it would need to be re-implemented here based on the new rate determination.
                pass # For now, skip update if price already exists

def create_employees():
    # Define staff for each branch
    staff = {
        "Bohol Main": ["Therapist A", "Therapist B", "Therapist C"],
        "Bohol Downtown": ["Therapist D", "Therapist E"]
    }
    
    for branch, descriptions in staff.items():
        for i, emp_name in enumerate(descriptions):
            email_id = f"{emp_name.replace(' ', '.').lower()}@masaje.com"
            
            # Check exist by first/last or email
            exists = frappe.db.get_value("Employee", {"employee_name": emp_name, "company": "Masaje de Bohol"}, "name")
            
            if not exists:
                frappe.get_doc({
                    "doctype": "Employee",
                    "employee_name": emp_name,
                    "first_name": emp_name.split()[0],
                    "last_name": emp_name.split()[1],
                    # "user_id": email_id, # Link only if user exists
                    "company": "Masaje de Bohol",
                    "status": "Active",
                    "branch": branch, 
                    "date_of_joining": "2024-01-01",
                    "gender": "Female",
                    "date_of_birth": "1990-01-01"
                }).insert(ignore_permissions=True)
                print(f"Created Employee: {emp_name} at {branch}")
            else:
                # Update branch to ensure correct setup
                frappe.db.set_value("Employee", exists, "branch", branch)
                print(f"Updated Branch for Employee: {emp_name} to {branch}")

def create_schedules():
    # Create 9AM - 6PM schedules for ALL active therapists for ALL 7 days
    emps = frappe.get_all("Employee", filters={"status": "Active", "company": "Masaje de Bohol"}, fields=["name", "employee_name"])
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for emp in emps:
        for day in days:
            # Check overlap
            exists = frappe.db.exists("Therapist Schedule", {"therapist": emp.name, "day_of_week": day})
            
            if not exists:
                 frappe.get_doc({
                    "doctype": "Therapist Schedule",
                    "therapist": emp.name,
                    "day_of_week": day,
                    "start_time": "09:00:00",
                    "end_time": "18:00:00"
                }).insert(ignore_permissions=True)
                 print(f"Created Schedule for {emp.employee_name} on {day}")
            else:
                pass # Skip if exists


