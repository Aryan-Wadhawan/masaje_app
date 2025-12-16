
import frappe

def run():
    print("--- Clearing Report DB Config ---")
    reports = ["Daily Branch Sales", "Therapist Utilization"]
    
    for r in reports:
        if frappe.db.exists("Report", r):
            doc = frappe.get_doc("Report", r)
            print(f"Update: {r}")
            print(f"  Old JSON len: {len(doc.json or '')}")
            
            doc.json = None
            doc.query = None
            doc.report_type = "Script Report"
            doc.is_standard = "Yes"
            
            # Important: The 'module' must match. 
            # If doc.module is 'Masaje App', Frappe looks for 'masaje_app' folder.
            # Let's confirm module mapping.
            print(f"  Module: {doc.module}")
            
            doc.save()
            print(f"  Saved {r}. JSON is: {doc.json}")
            
            frappe.db.commit()
