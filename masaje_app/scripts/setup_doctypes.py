
import frappe
from frappe.utils import now_datetime

def setup():
    create_role_receptionist()
    create_service_booking_doctype()
    create_therapist_schedule_doctype()
    frappe.db.commit()
    print("Doctypes and Roles created successfully.")

def create_role_receptionist():
    if frappe.db.exists("Role", "Receptionist"):
        return
    doc = frappe.get_doc({
        "doctype": "Role",
        "role_name": "Receptionist",
        "desk_access": 1
    })
    doc.insert()
    print("Created Role Receptionist")

def create_service_booking_doctype():
    if frappe.db.exists("DocType", "Service Booking"):
        print("Service Booking Doctype already exists.")
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "module": "Masaje App",
        "custom": 1,
        "name": "Service Booking",
        "autoname": "SB-.#####",
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
                        {"role": "Receptionist", "read": 1, "write": 1, "create": 1, "delete": 0}],
        "fields": [
            {"fieldname": "customer", "fieldtype": "Link", "options": "Customer", "label": "Customer", "reqd": 1, "in_list_view": 1},
            {"fieldname": "branch", "fieldtype": "Link", "options": "Branch", "label": "Branch", "reqd": 1, "in_list_view": 1},
            {"fieldname": "therapist", "fieldtype": "Link", "options": "Employee", "label": "Therapist", "reqd": 0, "in_list_view": 1},
            {"fieldname": "service_item", "fieldtype": "Link", "options": "Item", "label": "Service / Package", "reqd": 1, "in_list_view": 1},
            {"fieldname": "booking_date", "fieldtype": "Date", "label": "Date", "reqd": 1, "in_list_view": 1},
            {"fieldname": "time_slot", "fieldtype": "Time", "label": "Time", "reqd": 1, "in_list_view": 1},
            {"fieldname": "duration_minutes", "fieldtype": "Int", "label": "Duration (Minutes)", "reqd": 1},
            {"fieldname": "status", "fieldtype": "Select", "options": "Pending\nApproved\nCancelled\nCompleted", "label": "Status", "default": "Pending", "reqd": 1, "in_list_view": 1}
        ]
    })
    doc.insert()
    print("Created Service Booking Doctype")

def create_therapist_schedule_doctype():
    if frappe.db.exists("DocType", "Therapist Schedule"):
        print("Therapist Schedule already exists.")
        return

    doc = frappe.get_doc({
        "doctype": "DocType",
        "module": "Masaje App",
        "custom": 1,
        "name": "Therapist Schedule",
        "autoname": "format:{therapist}-{day_of_week}",
        "permissions": [{"role": "System Manager", "read": 1, "write": 1},
                        {"role": "Receptionist", "read": 1, "write": 0}],
        "fields": [
            {"fieldname": "therapist", "fieldtype": "Link", "options": "Employee", "label": "Therapist", "reqd": 1, "in_list_view": 1},
            {"fieldname": "day_of_week", "fieldtype": "Select", "options": "Monday\nTuesday\nWednesday\nThursday\nFriday\nSaturday\nSunday", "label": "Day", "reqd": 1, "in_list_view": 1},
            {"fieldname": "start_time", "fieldtype": "Time", "label": "Start Time"},
            {"fieldname": "end_time", "fieldtype": "Time", "label": "End Time"},
            {"fieldname": "is_off", "fieldtype": "Check", "label": "Is Off Day", "default": 0}
        ]
    })
    doc.insert()
    print("Created Therapist Schedule Doctype")
