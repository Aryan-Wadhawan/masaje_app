
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def run():
    print("--- Setting up Therapist Commission DocType ---")
    
    dt_name = "Therapist Commission"
    
    if not frappe.db.exists("DocType", dt_name):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "Masaje App",
            "custom": 1,
            "name": dt_name,
            "naming_rule": "Expression",
            "autoname": "format:COMM-{YYYY}-{#####}",
            "is_submittable": 1,
            "fields": [
                {"label": "Therapist", "fieldname": "therapist", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
                {"label": "Period Start", "fieldname": "start_date", "fieldtype": "Date", "reqd": 1, "in_list_view": 1},
                {"label": "Period End", "fieldname": "end_date", "fieldtype": "Date", "reqd": 1, "in_list_view": 1},
                {"label": "Values", "fieldtype": "Section Break"},
                {"label": "Total Bookings", "fieldname": "total_bookings", "fieldtype": "Int", "read_only": 1},
                {"label": "Total Revenue", "fieldname": "total_revenue", "fieldtype": "Currency", "read_only": 1},
                {"label": "Commission Rate (%)", "fieldname": "commission_rate", "fieldtype": "Float", "default": "10"},
                {"label": "Commission Amount", "fieldname": "commission_amount", "fieldtype": "Currency", "read_only": 1, "in_list_view": 1},
                {"label": "Status", "fieldname": "status", "fieldtype": "Select", "options": "Draft\nSubmitted\nPaid", "default": "Draft", "reqd": 1}
            ],
            "permissions": [
                {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1},
                {"role": "Accounts User", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1}
            ]
        })
        doc.insert()
        print(f"Created DocType: {dt_name}")
    else:
        print(f"DocType {dt_name} already exists.")
