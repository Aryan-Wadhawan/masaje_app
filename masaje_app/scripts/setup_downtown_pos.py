import frappe

def create_downtown_pos():
    branch = "Bohol Downtown"
    wh_name = "Bohol Downtown Store - MDB" # From setup_data.py logic hopefully
    
    # 1. Verify Warehouse exists
    if not frappe.db.exists("Warehouse", wh_name):
        # Fallback check
        wh_name = "Bohol Downtown Store"
        if not frappe.db.exists("Warehouse", wh_name):
            print("Error: Warehouse not found!")
            return
          # 2. Get dependencies
    cc_name = "Bohol Downtown"
    if not frappe.db.exists("Cost Center", cc_name):
        cc_name = "Bohol Downtown - MDB" # Try suffix
        
    # Find Account
    acc_name = frappe.db.get_value("Account", {"account_name": "Write Off", "company": "Masaje de Bohol"}, "name")
    if not acc_name:
         acc_name = frappe.db.get_value("Account", {"account_type": "Expense", "is_group": 0, "company": "Masaje de Bohol"}, "name")
    
    if not acc_name:
        # Create one
        parent = frappe.db.get_value("Account", {"is_group": 1, "root_type": "Expense", "company": "Masaje de Bohol"}, "name")
        if parent:
             frappe.get_doc({
                "doctype": "Account",
                "account_name": "Write Off",
                "parent_account": parent,
                "company": "Masaje de Bohol",
                "account_type": "Expense"
             }).insert(ignore_permissions=True)
             acc_name = "Write Off - MDB"
        else:
             print("Critical: No parent Expense account found!")
             return

    profile_name = "Bohol Downtown POS"
    
    if not frappe.db.exists("POS Profile", profile_name):
        doc = frappe.get_doc({
            "doctype": "POS Profile",
            "name": profile_name,
            "company": "Masaje de Bohol",
            "warehouse": wh_name,
            "selling_price_list": "Bohol Downtown", # Use its specific price list
            "currency": "PHP",
            "write_off_account": acc_name, 
            "write_off_cost_center": cc_name, 
            "payments": [{"mode_of_payment": "Cash", "default": 1}]
        })
        doc.insert(ignore_permissions=True)
        print(f"Created POS Profile: {profile_name}")
    else:
        print(f"POS Profile {profile_name} already exists.")
        
    # 3. Create Opening Entry (System User)
    if not frappe.db.exists("POS Opening Entry", {"pos_profile": profile_name, "status": "Open"}):
         frappe.get_doc({
            "doctype": "POS Opening Entry",
            "period_start_date": frappe.utils.now_datetime(),
            "pos_profile": profile_name,
            "user": frappe.session.user, # Administrator usually
            "company": "Masaje de Bohol",
            "balance_details": [{"mode_of_payment": "Cash", "opening_amount": 0}]
        }).submit()
         print(f"Opened POS Shift for {profile_name}")

if __name__ == "__main__":
    frappe.connect()
    create_downtown_pos()
