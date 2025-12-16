
import frappe

def run():
    print("--- Verifying Stock Deduction ---")
    
    item_code = "Massage Oil"
    warehouse = "Bohol Downtown Store - MDB"
    
    # Check Current Bin Qty
    qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
    print(f"Current Stock in {warehouse}: {qty}")
    
    # Broad search for Item
    entries = frappe.get_all("Stock Ledger Entry", 
        fields=["name", "creation", "item_code", "actual_qty", "voucher_type", "voucher_no"],
        filters={"item_code": item_code},
        limit=10,
        order_by="creation desc"
    )
    print(f"All SLEs for {item_code}: {entries}")
            
    print(f"All SLEs for {item_code}: {entries}")
    
    # Debug: Check one invoice
    inv_name = frappe.get_all("POS Invoice", limit=1, filters={"posting_date": frappe.utils.today()}, pluck="name")
    if inv_name:
        inv = frappe.get_doc("POS Invoice", inv_name[0])
        print(f"Checking Invoice {inv.name}:")
        print(f"  update_stock: {inv.update_stock}")
        print(f"  Status: {inv.status}")
        print(f"  DocStatus: {inv.docstatus}")
        
        # Check Packed Items
        packed = frappe.get_all("POS Invoice Item", filters={"parent": inv.name}, fields=["item_code", "warehouse", "qty"])
        print(f"  Line Items: {packed}")
        
        # Check if there's a Packed Items table (usually 'packed_items')
        if hasattr(inv, 'packed_items'):
             print(f"  Packed Items (Doc Property): {len(inv.packed_items)}")
             for p in inv.packed_items:
                 print(f"    - {p.item_code}: {p.qty} (Warehouse: {p.warehouse})")
        else:
             print("  No 'packed_items' property found on Doc.")
             
        # Try fetching from DB table 'Packed Item' (common in Sales Invoice, maybe POS too?)
        packed_db = frappe.get_all("Packed Item", filters={"parent": inv.name}, fields=["item_code", "qty"])
        print(f"  Packed Item Table (DB): {packed_db}")
    
    if entries and len(entries) > 1:
        print("SUCCESS: Stock deduction entries found.")
    else:
        print("FAILURE: Only opening stock found. No deductions.")
