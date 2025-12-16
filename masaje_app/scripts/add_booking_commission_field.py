
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def run():
    print("--- Adding Commission Field to Service Booking ---")
    
    create_custom_field("Service Booking", field)
    print("Added 'commission_amount' to Service Booking")
