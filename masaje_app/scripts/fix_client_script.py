"""
Fix Client Script datetime format bug
Run: bench --site erpnext.localhost execute masaje_app.scripts.fix_client_script.setup
"""
import frappe


def setup():
    """Update the client script with correct datetime format"""
    print("Fixing Client Script datetime format...")
    
    script_name = "Service Booking - Walk-in UX"
    
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)
        print("  - Deleted old script")
    
    # Fixed script - no longer appending ':00' to time_slot
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
        // time_slot may be HH:MM or HH:MM:SS - handle both
        let time = frm.doc.time_slot;
        // If time is HH:MM format, add :00 for seconds
        if (time.split(':').length === 2) {
            time = time + ':00';
        }
        let datetime_str = frm.doc.booking_date + ' ' + time;
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
    
    frappe.db.commit()
    print("  + Created fixed client script")
    print("✓ Done!")


if __name__ == "__main__":
    setup()
