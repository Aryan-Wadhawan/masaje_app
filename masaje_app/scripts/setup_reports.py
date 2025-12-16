"""
Setup New Reports for Masaje App
Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_reports.setup
"""
import frappe


def setup():
    """Create new reports in the database"""
    print("Setting up new reports...")
    
    reports = [
        {
            "name": "Therapist Commission",
            "report_name": "Therapist Commission",
            "ref_doctype": "POS Invoice",
            "report_type": "Script Report",
            "module": "Masaje App",
            "is_standard": "Yes",
            "add_total_row": 1
        },
        {
            "name": "Popular Services",
            "report_name": "Popular Services",
            "ref_doctype": "Service Booking",
            "report_type": "Script Report",
            "module": "Masaje App",
            "is_standard": "Yes",
            "add_total_row": 1
        },
        {
            "name": "Peak Hours",
            "report_name": "Peak Hours",
            "ref_doctype": "Service Booking",
            "report_type": "Script Report",
            "module": "Masaje App",
            "is_standard": "Yes",
            "add_total_row": 0
        }
    ]
    
    for report_data in reports:
        create_report(report_data)
    
    frappe.db.commit()
    print("✓ Reports setup complete!")


def create_report(report_data):
    """Create or update a report"""
    name = report_data["name"]
    
    if frappe.db.exists("Report", name):
        print(f"  - Already exists: {name}")
        return
    
    doc = frappe.new_doc("Report")
    doc.update(report_data)
    doc.insert(ignore_permissions=True)
    print(f"  + Created: {name}")


if __name__ == "__main__":
    setup()
