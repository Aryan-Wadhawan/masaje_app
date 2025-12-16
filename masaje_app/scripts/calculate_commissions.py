
import frappe
from frappe.utils import getdate

def run(start_date=None, end_date=None):
    print("--- Calculating Commissions ---")
    
    if not start_date:
        start_date = frappe.utils.add_days(frappe.utils.today(), -30)
    if not end_date:
        end_date = frappe.utils.today()
        
    print(f"Period: {start_date} to {end_date}")
    
    # 1. Fetch Bookings
    bookings = frappe.get_all("Service Booking", 
        fields=["name", "therapist", "booking_date", "service_item"],
        filters={
            "booking_date": ["between", [start_date, end_date]],
            "status": ["in", ["Completed", "Paid"]], # Assuming Paid/Completed validation
            "therapist": ["is", "set"]
        }
    )
    
    # 2. Group by Therapist
    therapist_stats = {}
    
    for b in bookings:
        t = b.therapist
        if t not in therapist_stats:
            therapist_stats[t] = {"bookings": 0, "revenue": 0.0, "commission": 0.0}
            
        # Get Price
        rate = 1500.0 
        
        # Improvement: Fetch actual rate from Item Price
        if b.service_item:
            rate = frappe.db.get_value("Item Price", {"item_code": b.service_item, "price_list": "Standard Selling"}, "price_list_rate") or 1500.0
            
        # Calculate Commission per Booking
        b_comm = rate * 0.10
        
        # Update Booking immediately
        frappe.db.set_value("Service Booking", b.name, "commission_amount", b_comm)
        
        # Update POS Invoice if linked (User Request)
        # Note: 'invoice' field might not be in the 'fields' list of get_all above, need to verify
        inv_name = frappe.db.get_value("Service Booking", b.name, "invoice")
        if inv_name:
             frappe.db.set_value("POS Invoice", inv_name, "total_commission", b_comm) # Standard Field
             frappe.db.set_value("POS Invoice", inv_name, "amount_eligible_for_commission", rate) # Standard Field
             print(f"Updated Invoice {inv_name} total_commission: {b_comm}")
            
        therapist_stats[t]["bookings"] += 1
        therapist_stats[t]["revenue"] += rate
        therapist_stats[t]["commission"] += b_comm
        
    # 3. Generate Commission Docs
    for t, stats in therapist_stats.items():
        comm_amt = stats["commission"]
        
        # Check existing
        existing = frappe.db.exists("Therapist Commission", {
            "therapist": t, 
            "start_date": start_date, 
            "end_date": end_date,
            "docstatus": 0 # Only update Drafts
        })
        
        if existing:
            doc = frappe.get_doc("Therapist Commission", existing)
            doc.total_bookings = stats["bookings"]
            doc.total_revenue = stats["revenue"]
            doc.commission_amount = comm_amt
            doc.save()
            print(f"Updated Commission for {t}: {comm_amt}")
        else:
            doc = frappe.get_doc({
                "doctype": "Therapist Commission",
                "therapist": t,
                "start_date": start_date,
                "end_date": end_date,
                "total_bookings": stats["bookings"],
                "total_revenue": stats["revenue"],
                "commission_rate": 10.0,
                "commission_amount": comm_amt,
                "status": "Draft"
            })
            doc.insert()
            print(f"Created Commission for {t}: {comm_amt}")
            
    print("Commission Calculation Complete.")
