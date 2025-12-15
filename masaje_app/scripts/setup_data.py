
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
    # (Item Code, Price List, Rate)
    prices = [
        ("Service-Massage-60", "Bohol Main", 1000),
        ("Service-Massage-60", "Bohol Downtown", 800),
        ("Product-TigerBalm", "Bohol Main", 100),
        ("Product-TigerBalm", "Bohol Downtown", 90),
        ("Service-Massage-60", "Standard Selling", 1200)
    ]
    
    for item, pl, rate in prices:
        if not frappe.db.exists("Item Price", {"item_code": item, "price_list": pl}):
            frappe.get_doc({
                "doctype": "Item Price",
                "item_code": item,
                "price_list": pl,
                "price_list_rate": rate
            }).insert()
            print(f"Set Price: {item} @ {pl} = {rate}")

def create_employees():
    employees = ["Therapist A", "Therapist B"]
    for emp_name in employees:
        if not frappe.db.exists("Employee", {"employee_name": emp_name}):
            frappe.get_doc({
                "doctype": "Employee",
                "employee_name": emp_name,
                "first_name": emp_name.split()[0],
                "last_name": emp_name.split()[1],
                "company": "Masaje de Bohol",
                "status": "Active",
                "date_of_joining": "2024-01-01",
                "gender": "Female",
                "date_of_birth": "1990-01-01"
            }).insert()
            print(f"Created Employee: {emp_name}")

def create_schedules():
    # Set 9-5 for all days for Therapist A
    emp = frappe.db.get_value("Employee", {"employee_name": "Therapist A"}, "name")
    if not emp: return

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in days:
        name = f"{emp}-{day}"
        if not frappe.db.exists("Therapist Schedule", name):
             frappe.get_doc({
                "doctype": "Therapist Schedule",
                "therapist": emp,
                "day_of_week": day,
                "start_time": "09:00:00",
                "end_time": "17:00:00"
            }).insert(ignore_permissions=True)
             print(f"Created Schedule for {emp} on {day}")


