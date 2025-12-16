"""
Fix Service Booking mandatory fields
Run: bench --site erpnext.localhost execute masaje_app.scripts.fix_mandatory_fields.setup
"""
import frappe


def setup():
    """Remove mandatory from hidden fields"""
    print("Fixing mandatory fields on Service Booking...")
    
    # Remove mandatory from service_item (hidden field)
    set_field_not_mandatory("service_item")
    
    # Remove mandatory from duration_minutes (auto-calculated)
    set_field_not_mandatory("duration_minutes")
    
    frappe.db.commit()
    print("✓ Done - both fields are now optional!")


def set_field_not_mandatory(field_name):
    """Remove mandatory requirement from a field"""
    prop_name = f"Service Booking-{field_name}-reqd"
    
    if frappe.db.exists("Property Setter", prop_name):
        frappe.db.set_value("Property Setter", prop_name, "value", "0")
        print(f"  - Updated: {field_name} is no longer mandatory")
    else:
        if frappe.get_meta("Service Booking").has_field(field_name):
            frappe.get_doc({
                "doctype": "Property Setter",
                "name": prop_name,
                "doctype_or_field": "DocField",
                "doc_type": "Service Booking",
                "field_name": field_name,
                "property": "reqd",
                "property_type": "Check",
                "value": "0"
            }).insert()
            print(f"  + Created: {field_name} is no longer mandatory")
        else:
            print(f"  - {field_name} field not found")


if __name__ == "__main__":
    setup()
