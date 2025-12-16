
import frappe

def run():
    report_name = "Daily Branch Sales"
    if frappe.db.exists("Report", report_name):
        doc = frappe.get_doc("Report", report_name)
        
        # Change type to Script Report
        doc.report_type = "Script Report"
        doc.is_standard = "Yes"
        doc.module = "Masaje App"
        
        # Clear Query/JSON if present
        doc.query = None
        doc.json = None
        
        doc.save()
        print(f"Updated {report_name} to Script Report.")
    else:
        print(f"Report {report_name} not found. Bench migrate should create it from JSON.")

    # Remove the old Therapist Utilization query report to force a clean slate if we update it later
    report_name_2 = "Therapist Utilization"
    if frappe.db.exists("Report", report_name_2):
        doc = frappe.get_doc("Report", report_name_2)
        doc.report_type = "Script Report"
        doc.is_standard = "Yes"
        doc.module = "Masaje App"
        doc.query = None
        doc.json = None
        doc.save()
        print(f"Updated {report_name_2} to Script Report.")

