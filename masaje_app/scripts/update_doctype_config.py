
import frappe

def run():
    print("--- Updating Service Booking DocType ---")
    
    dt = frappe.get_doc("DocType", "Service Booking")
    updated = False
    
    for field in dt.fields:
        if field.fieldname == "branch":
            print(f"Found 'branch' field. Current: List={field.in_list_view}, Filter={field.in_standard_filter}")
            if not field.in_list_view or not field.in_standard_filter:
                field.in_list_view = 1
                field.in_standard_filter = 1
                updated = True
                print("  -> Updated settings.")
                
    if updated:
        dt.save()
        print("Saved DocType 'Service Booking'.")
    else:
        print("No changes needed.")
        
    print("--- Checking Therapist Schedule ---")
    if frappe.db.exists("DocType", "Therapist Schedule"):
        dt_ts = frappe.get_doc("DocType", "Therapist Schedule")
        updated_ts = False
        for field in dt_ts.fields:
             if field.fieldname == "branch":
                if not field.in_list_view or not field.in_standard_filter:
                    field.in_list_view = 1
                    field.in_standard_filter = 1
                    updated_ts = True
                    print("  -> Updated Therapist Schedule branch settings.")
        if updated_ts:
            dt_ts.save()
            print("Saved DocType 'Therapist Schedule'.")
