import frappe

def debug_pos_prices():
    pos_profile_name = "Bohol Main POS"
    
    # 1. Get POS Profile Config
    if not frappe.db.exists("POS Profile", pos_profile_name):
        print(f"POS Profile '{pos_profile_name}' not found!")
        # Try to find any POS Profile
        profiles = frappe.get_all("POS Profile", pluck="name")
        print(f"Available POS Profiles: {profiles}")
        return

    pos_profile = frappe.get_doc("POS Profile", pos_profile_name)
    price_list = pos_profile.selling_price_list
    print(f"POS Profile: {pos_profile_name}")
    print(f"Linked Price List: {price_list}")
    print(f"Company: {pos_profile.company}")
    print(f"Currency: {pos_profile.currency}")
    
    # 2. Check Item Prices for this Price List
    items = ["Tiger Balm (50g)", "Manicure Premium", "Full Body Massage"] # From screenshot
    # Need to find item codes first
    item_codes = []
    for i in items:
        code = frappe.db.get_value("Item", {"item_name": ["like", f"%{i}%"]}, "item_code")
        if code:
            item_codes.append(code)
        else:
            print(f"Could not find Item Code for '{i}'")

    print(f"\nChecking Prices for items: {item_codes}")
    
    for item_code in item_codes:
        price = frappe.db.get_value("Item Price", 
            {"item_code": item_code, "price_list": price_list}, 
            "price_list_rate"
        )
        print(f"Item: {item_code}")
        print(f"  - Price in '{price_list}': {price}")
        
        # Check if price exists in ANY list
        all_prices = frappe.get_all("Item Price", filters={"item_code": item_code}, fields=["price_list", "price_list_rate"])
        if all_prices:
            print(f"  - All found prices: {all_prices}")
        else:
            print(f"  - NO PRICES FOUND IN ANY LIST")

if __name__ == "__main__":
    frappe.connect()
    debug_pos_prices()
