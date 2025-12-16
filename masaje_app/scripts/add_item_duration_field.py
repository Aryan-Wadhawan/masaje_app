"""
Add custom_duration_minutes field to Item doctype
Run: bench --site erpnext.localhost execute masaje_app.scripts.add_item_duration_field.setup
"""
import frappe


def setup():
    """Add custom_duration_minutes field to Item doctype for service duration"""
    print("Adding custom_duration_minutes field to Item...")
    
    field_name = "custom_duration_minutes"
    doctype = "Item"
    
    if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
        print(f"  - Field {field_name} already exists on {doctype}")
        return
    
    custom_field = frappe.new_doc("Custom Field")
    custom_field.dt = doctype
    custom_field.fieldname = field_name
    custom_field.label = "Duration (Minutes)"
    custom_field.fieldtype = "Int"
    custom_field.description = "Default duration in minutes for this service"
    custom_field.insert_after = "description"
    custom_field.depends_on = "eval:doc.item_group == 'Services' || doc.is_stock_item == 0"
    custom_field.insert()
    
    print(f"  + Created field: {field_name} on {doctype}")
    frappe.db.commit()
    print("✓ Done!")


if __name__ == "__main__":
    setup()
