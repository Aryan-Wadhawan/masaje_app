"""
Service Booking UX Improvements Setup
--------------------------------------
Creates:
1. Property Setter to hide redundant service_item field
2. Property Setter to default time_slot to current time
3. Client Script to auto-calculate duration from items

Run via: bench --site erpnext.localhost execute masaje_app.scripts.setup_booking_ux.setup
"""
import frappe
from frappe.utils import nowtime


def setup():
    """Main setup function"""
    print("Setting up Service Booking UX improvements...")
    
    # 1. Hide the redundant service_item field
    hide_service_item_field()
    
    # 2. Set default for time_slot to current time  
    set_time_slot_default()
    
    # 3. Create client script for auto-duration calculation
    create_duration_client_script()
    
    frappe.db.commit()
    print("✓ Service Booking UX setup complete!")


def hide_service_item_field():
    """Hide the single service_item field - use items table instead"""
    prop_name = "Service Booking-service_item-hidden"
    
    if frappe.db.exists("Property Setter", prop_name):
        print("  - service_item already hidden")
        return
    
    # Check if field exists
    if not frappe.get_meta("Service Booking").has_field("service_item"):
        print("  - service_item field not found, skipping")
        return
    
    frappe.get_doc({
        "doctype": "Property Setter",
        "name": prop_name,
        "doctype_or_field": "DocField",
        "doc_type": "Service Booking",
        "field_name": "service_item",
        "property": "hidden",
        "property_type": "Check",
        "value": "1"
    }).insert()
    print("  + Hidden service_item field")


def set_time_slot_default():
    """Set time_slot default to current time"""
    prop_name = "Service Booking-time_slot-default"
    
    if frappe.db.exists("Property Setter", prop_name):
        print("  - time_slot default already set")
        return
    
    # Check if field exists
    if not frappe.get_meta("Service Booking").has_field("time_slot"):
        print("  - time_slot field not found, skipping")
        return
    
    frappe.get_doc({
        "doctype": "Property Setter",
        "name": prop_name,
        "doctype_or_field": "DocField",
        "doc_type": "Service Booking",
        "field_name": "time_slot",
        "property": "default",
        "property_type": "Text",
        "value": "Now"  # Frappe recognizes "Now" as current time
    }).insert()
    print("  + Set time_slot default to current time")


def create_duration_client_script():
    """Create client script to auto-calculate duration from items"""
    script_name = "Service Booking - Auto Duration"
    
    if frappe.db.exists("Client Script", script_name):
        print("  - Auto duration script already exists")
        return
    
    script_code = """
// Auto-calculate duration_minutes from items child table
frappe.ui.form.on('Service Booking', {
    refresh: function(frm) {
        calculate_total_duration(frm);
    }
});

frappe.ui.form.on('Service Booking Item', {
    duration_minutes: function(frm, cdt, cdn) {
        calculate_total_duration(frm);
    },
    items_add: function(frm, cdt, cdn) {
        calculate_total_duration(frm);
    },
    items_remove: function(frm, cdt, cdn) {
        calculate_total_duration(frm);
    }
});

function calculate_total_duration(frm) {
    let total_duration = 0;
    
    if (frm.doc.items && frm.doc.items.length > 0) {
        frm.doc.items.forEach(function(item) {
            total_duration += (item.duration_minutes || 0);
        });
    }
    
    if (total_duration > 0 && frm.doc.duration_minutes !== total_duration) {
        frm.set_value('duration_minutes', total_duration);
    }
}
"""
    
    frappe.get_doc({
        "doctype": "Client Script",
        "name": script_name,
        "dt": "Service Booking",
        "script": script_code,
        "enabled": 1
    }).insert()
    print("  + Created auto-duration client script")


if __name__ == "__main__":
    setup()
