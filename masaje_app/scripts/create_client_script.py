
import frappe

def execute():
    script_content = """
frappe.views.calendar["Service Booking"] = {
    field_map: {
        "start": "start_datetime",
        "end": "end_datetime",
        "id": "name",
        "title": "customer",
        "status": "status"
    },
    color_map: {
        "Pending": "orange",
        "Approved": "green",
        "Cancelled": "red",
        "Completed": "blue"
    }
};
    """
    
    # Check if exists
    if frappe.db.exists("Client Script", {"dt": "Service Booking", "view": "List"}):
        doc = frappe.get_doc("Client Script", {"dt": "Service Booking", "view": "List"})
        doc.script = script_content
        doc.enabled = 1
        doc.save()
        print("Updated existing Client Script")
    else:
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "name": "Service Booking Calendar View",
            "dt": "Service Booking",
            "view": "List",
            "script": script_content,
            "enabled": 1
        })
        doc.insert()
        print("Created new Client Script")
