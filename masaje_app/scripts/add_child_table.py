
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    # 1. Create Child Table: Service Booking Item
    if not frappe.db.exists("DocType", "Service Booking Item"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Service Booking Item",
            "module": "Masaje App",
            "istable": 1,
            "fields": [
                {"fieldname": "service_item", "fieldtype": "Link", "options": "Item", "label": "Service", "reqd": 1, "in_list_view": 1},
                {"fieldname": "service_name", "fieldtype": "Data", "label": "Service Name", "read_only": 1, "fetch_from": "service_item.item_name"},
                {"fieldname": "price", "fieldtype": "Currency", "label": "Price", "read_only": 1},
                {"fieldname": "duration_minutes", "fieldtype": "Int", "label": "Duration (min)", "read_only": 1} # We might need to fetch this
            ]
        })
        doc.insert()
        print("Created Child Table: Service Booking Item")

    # 2. Add Table field to Service Booking
    # We will keep 'service_item' for now to avoid breaking existing code immediately, 
    # but we will add 'items' table.
    
    dt = frappe.get_doc("DocType", "Service Booking")
    
    # Check if 'items' field exists in fields list
    found = any(f.fieldname == "items" for f in dt.fields)
    
    if not found:
        dt.append("fields", {
            "fieldname": "items",
            "fieldtype": "Table",
            "options": "Service Booking Item",
            "label": "Selected Services"
        })
        dt.save()
        print("Added 'items' table to Service Booking")

    # 3. Update API logic will happen in next steps
