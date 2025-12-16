
import frappe

def run():
    print("--- Verifying Sales Team Data ---")
    
    # Check Invoice ACC-PSINV-2025-00079
    inv_name = "ACC-PSINV-2025-00079"
    
    if not frappe.db.exists("POS Invoice", inv_name):
        print(f"Invoice {inv_name} not found.")
        return

    # Check Sales Team via SQL
    teams = frappe.db.sql(f"SELECT * FROM `tabSales Team` WHERE parent='{inv_name}'", as_dict=1)
    
    if teams:
        print(f"Sales Team for {inv_name}:")
        for t in teams:
            print(f"- Sales Person: {t.sales_person}, %: {t.allocated_percentage}")
    else:
        print(f"No Sales Team found for {inv_name}")
