"""
Remove mandatory from duration_minutes field
Run: bench --site erpnext.localhost execute masaje_app.scripts.fix_duration_field.setup
"""
import frappe


def setup():
    """Remove mandatory from duration_minutes field"""
    print("Fixing duration_minutes field...")
    
    prop_name = "Service Booking-duration_minutes-reqd"
    
    if frappe.db.exists("Property Setter", prop_name):
        frappe.db.set_value("Property Setter", prop_name, "value", "0")
        print("  - Updated: duration_minutes is no longer mandatory")
    else:
        if frappe.get_meta("Service Booking").has_field("duration_minutes"):
            frappe.get_doc({
                "doctype": "Property Setter",
                "name": prop_name,
                "doctype_or_field": "DocField",
                "doc_type": "Service Booking",
                "field_name": "duration_minutes",
                "property": "reqd",
                "property_type": "Check",
                "value": "0"
            }).insert()
            print("  + Created: duration_minutes is no longer mandatory")
        else:
            print("  - duration_minutes field not found")
    
    frappe.db.commit()
    print("✓ Done!")


if __name__ == "__main__":
    setup()
