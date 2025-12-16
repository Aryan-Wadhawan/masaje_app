
import frappe

def run():
    print("--- Configuring POS Profile for Stock ---")
    
    # Get the profile used (Bohol Downtown POS usually)
    profile_name = frappe.db.get_value("POS Profile", {"warehouse": ["like", "%Bohol%"]}, "name")
    print(f"Checking Profile: {profile_name}")
    
    if profile_name:
        profile = frappe.get_doc("POS Profile", profile_name)
        if not profile.update_stock:
            profile.update_stock = 1
            profile.save()
            print(f"Enabled 'Update Stock' for {profile_name}")
        else:
            print(f"'Update Stock' already enabled for {profile_name}")
            
    # Also check Is Sales Item for Service?
    # Actually, for Product Bundle to work, the Parent Item MUST be a Stock Item OR the System Settings must allow non-stock items to be bundled?
    # In ERPNext, Product Bundle Parent is usually a non-stock Sales Item. Child items are Stock Items.
    # We verified "Massage Service 60m" is Non-Stock, Sales Item. This is correct.
