"""
Enhanced Service Booking UX Setup
----------------------------------
Creates Client Script and Property Setters for:
1. Auto-default booking_date to today
2. Auto-default time_slot to current time  
3. Make booking_date and time_slot read-only (use start/end datetime for future)
4. Auto-calculate duration from items

Run via: bench --site erpnext.localhost execute masaje_app.scripts.setup_booking_ux_enhanced.setup
"""
import frappe
from frappe.utils import today, nowtime


def setup():
    """Main setup function"""
    print("Setting up Enhanced Service Booking UX...")
    
    # Remove old client script if exists
    remove_old_client_script()
    
    # Set defaults via Property Setter
    set_booking_date_default()
    set_time_slot_default()
    
    # Make fields read-only
    set_booking_date_readonly()
    set_time_slot_readonly()
    
    # Hide redundant service_item field
    hide_service_item_field()
    
    # Create enhanced client script
    create_enhanced_client_script()
    
    frappe.db.commit()
    print("✓ Enhanced Service Booking UX setup complete!")
    print("\nChanges applied:")
    print("  - booking_date defaults to today (read-only)")
    print("  - time_slot defaults to now (read-only)")
    print("  - Use start_datetime/end_datetime for future bookings")
    print("  - Duration auto-calculates from items")


def remove_old_client_script():
    """Remove the old client script"""
    if frappe.db.exists("Client Script", "Service Booking - Auto Duration"):
        frappe.delete_doc("Client Script", "Service Booking - Auto Duration")
        print("  - Removed old client script")


def set_booking_date_default():
    """Set booking_date default to today"""
    prop_name = "Service Booking-booking_date-default"
    
    if frappe.db.exists("Property Setter", prop_name):
        frappe.db.set_value("Property Setter", prop_name, "value", "Today")
        print("  - Updated booking_date default to Today")
        return
    
    if not frappe.get_meta("Service Booking").has_field("booking_date"):
        print("  - booking_date field not found, skipping")
        return
    
    frappe.get_doc({
        "doctype": "Property Setter",
        "name": prop_name,
        "doctype_or_field": "DocField",
        "doc_type": "Service Booking",
        "field_name": "booking_date",
        "property": "default",
        "property_type": "Text",
        "value": "Today"
    }).insert()
    print("  + Set booking_date default to Today")


def set_time_slot_default():
    """Set time_slot default to current time"""
    prop_name = "Service Booking-time_slot-default"
    
    if frappe.db.exists("Property Setter", prop_name):
        print("  - time_slot default already set")
        return
    
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
        "value": "Now"
    }).insert()
    print("  + Set time_slot default to Now")


def set_booking_date_readonly():
    """Make booking_date read-only"""
    prop_name = "Service Booking-booking_date-read_only"
    
    if frappe.db.exists("Property Setter", prop_name):
        print("  - booking_date already read-only")
        return
    
    if not frappe.get_meta("Service Booking").has_field("booking_date"):
        return
    
    frappe.get_doc({
        "doctype": "Property Setter",
        "name": prop_name,
        "doctype_or_field": "DocField",
        "doc_type": "Service Booking",
        "field_name": "booking_date",
        "property": "read_only",
        "property_type": "Check",
        "value": "1"
    }).insert()
    print("  + Set booking_date to read-only")


def set_time_slot_readonly():
    """Make time_slot read-only"""
    prop_name = "Service Booking-time_slot-read_only"
    
    if frappe.db.exists("Property Setter", prop_name):
        print("  - time_slot already read-only")
        return
    
    if not frappe.get_meta("Service Booking").has_field("time_slot"):
        return
    
    frappe.get_doc({
        "doctype": "Property Setter",
        "name": prop_name,
        "doctype_or_field": "DocField",
        "doc_type": "Service Booking",
        "field_name": "time_slot",
        "property": "read_only",
        "property_type": "Check",
        "value": "1"
    }).insert()
    print("  + Set time_slot to read-only")


def hide_service_item_field():
    """Hide the single service_item field - use items table instead"""
    prop_name = "Service Booking-service_item-hidden"
    
    if frappe.db.exists("Property Setter", prop_name):
        print("  - service_item already hidden")
        return
    
    if not frappe.get_meta("Service Booking").has_field("service_item"):
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


def create_enhanced_client_script():
    """Create enhanced client script for auto-calculations"""
    script_name = "Service Booking - Walk-in UX"
    
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)
    
    script_code = """
// Enhanced Service Booking UX for Walk-ins
// Auto-calculates duration and auto-populates start_datetime

frappe.ui.form.on('Service Booking', {
    refresh: function(frm) {
        calculate_total_duration(frm);
        update_start_datetime(frm);
    },
    
    booking_date: function(frm) {
        update_start_datetime(frm);
    },
    
    time_slot: function(frm) {
        update_start_datetime(frm);
    }
});

frappe.ui.form.on('Service Booking Item', {
    duration_minutes: function(frm, cdt, cdn) {
        calculate_total_duration(frm);
        update_end_datetime(frm);
    },
    items_add: function(frm, cdt, cdn) {
        calculate_total_duration(frm);
        update_end_datetime(frm);
    },
    items_remove: function(frm, cdt, cdn) {
        calculate_total_duration(frm);
        update_end_datetime(frm);
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

function update_start_datetime(frm) {
    if (frm.doc.booking_date && frm.doc.time_slot && !frm.doc.start_datetime) {
        let datetime_str = frm.doc.booking_date + ' ' + frm.doc.time_slot + ':00';
        frm.set_value('start_datetime', datetime_str);
    }
}

function update_end_datetime(frm) {
    if (frm.doc.start_datetime && frm.doc.duration_minutes) {
        let start = frappe.datetime.str_to_obj(frm.doc.start_datetime);
        let end = frappe.datetime.add_minutes(start, frm.doc.duration_minutes);
        frm.set_value('end_datetime', frappe.datetime.obj_to_str(end));
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
    print("  + Created enhanced client script")


if __name__ == "__main__":
    setup()
