
import frappe

def run():
    doctype = "Service Booking"
    if not frappe.db.exists("DocType", doctype):
        print(f"DocType {doctype} not found!")
        return

    doc = frappe.get_doc("DocType", doctype)
    
    # Check if field exists
    existing = [f.fieldname for f in doc.fields]
    if "invoice" in existing:
        print("Field 'invoice' already exists.")
        return

    # Add Field
    doc.append("fields", {
        "fieldname": "invoice",
        "label": "POS Invoice",
        "fieldtype": "Link",
        "options": "POS Invoice",
        "insert_after": "status"
    })
    
    doc.save()
    print("Added 'invoice' field to Service Booking.")
