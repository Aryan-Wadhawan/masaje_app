
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def run():
    print("--- Setting up Financial Integration Fields ---")
    
    # 1. Add 'branch' to POS Invoice
    # We use create_custom_fields for safety (idempotent)
    custom_fields = {
        "POS Invoice": [
            {
                "fieldname": "branch",
                "label": "Branch",
                "fieldtype": "Link",
                "options": "Branch",
                "insert_after": "customer",
                "read_only": 1 # Should be set by system
            }
        ],
        "Branch": [
            {
                "fieldname": "default_cost_center",
                "label": "Default Cost Center",
                "fieldtype": "Link",
                "options": "Cost Center",
                "insert_after": "branch"
            }
        ]
    }
    
    create_custom_fields(custom_fields)
    print("Created Custom Fields on POS Invoice and Branch.")
    
    # 2. Configure Cost Centers for existing Branches
    # Ensure Cost Centers exist
    company = "Masaje de Bohol"
    parent_cc = frappe.db.get_value("Cost Center", {"is_group": 1, "company": company}, "name") or f"Main - {frappe.utils.get_msg_id(company)}"
    # Fallback to standard "Main - MDB" usually created by setup
    
    branches = {
        "Bohol Main": "Main - MDB", # Assuming this exists or will map to standard
        "Panglao Branch": "Panglao - MDB" 
    }
    
    for b_name, cc_name in branches.items():
        if frappe.db.exists("Branch", b_name):
            # 2a. Ensure Cost Center exists
            if not frappe.db.exists("Cost Center", cc_name):
                # Try to find a parent
                parent = frappe.db.get_value("Cost Center", {"company": company, "is_group": 1}, "name")
                if parent:
                    cc = frappe.get_doc({
                        "doctype": "Cost Center",
                        "cost_center_name": cc_name.replace(" - MDB", ""), # cleaner name
                        "company": company,
                        "parent_cost_center": parent
                    })
                    cc.insert(ignore_permissions=True)
                    cc_name = cc.name
                    print(f"Created Cost Center: {cc_name}")
            
            # 2b. Updates Branch
            frappe.db.set_value("Branch", b_name, "default_cost_center", cc_name)
            print(f"Linked {b_name} -> Cost Center {cc_name}")
            
    frappe.db.commit()
    print("Configuration Complete.")
