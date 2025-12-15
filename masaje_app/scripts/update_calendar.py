
import frappe

def execute():
    if not frappe.db.exists("DocType", "Service Booking"):
        print("Service Booking not found")
        return

    doc = frappe.get_doc("DocType", "Service Booking")
    doc.is_calendar_and_gantt = 1
    doc.save()
    print("Enabled Calendar View for Service Booking")
