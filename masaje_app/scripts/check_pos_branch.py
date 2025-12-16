
import frappe

def run():
    print("--- Auditing POS Invoice Integration ---")
    
    # 1. Metadata Check
    meta = frappe.get_meta("POS Invoice")
    has_branch = "branch" in [df.fieldname for df in meta.fields]
    print(f"POS Invoice has 'branch' field: {has_branch}")
    
    # 2. Data Check
    invoices = frappe.get_all("POS Invoice", 
        fields=["name", "customer", "posting_date", "grand_total", "pos_profile", "set_warehouse", "cost_center"], 
        limit=5, 
        filters={"customer": ["like", "Test Cust%"]} # Check our test data
    )
    
    if has_branch:
        # If field exists, fetch it too
        branch_data = frappe.get_all("POS Invoice", fields=["name", "branch"], limit=5, filters={"customer": ["like", "Test Cust%"]})
        print(f"Branch Data: {branch_data}")
    
    print(f"Recent Test Invoices (Standard Fields):")
    for inv in invoices:
        print(f"Invoice: {inv.name} | Header CC: {inv.cost_center}")
        # Fetch items
        items = frappe.get_all("POS Invoice Item", filters={"parent": inv.name}, fields=["item_code", "cost_center", "warehouse"])
        for item in items:
            print(f"  - Item: {item.item_code} | CC: {item.cost_center} | Warehouse: {item.warehouse}")
        
    # 3. Check POS Profile linkage
    if invoices:
        profile_name = invoices[0].pos_profile
        if profile_name:
            profile = frappe.get_doc("POS Profile", profile_name)
            print(f"POS Profile '{profile_name}' configuration:")
            print(f"  Warehouse: {profile.warehouse}")
            print(f"  Cost Center: {profile.cost_center}")
            # Check if POS Profile has a branch link?
            # Standard doesn't, but let's see.

    print("--- Audit Complete ---")
