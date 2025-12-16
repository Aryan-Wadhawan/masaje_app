
import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    # --- Security / Permission Logic ---
    # If user is not System Manager, restrict to their assigned Branch
    user = frappe.session.user
    if "System Manager" not in frappe.get_roles(user):
        employee = frappe.db.get_value("Employee", {"user_id": user}, ["name", "branch"], as_dict=True)
        if employee and employee.branch:
            # Enforce the branch filter
            filters["branch"] = employee.branch
    
    # --- Columns ---
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
        {"label": _("Total Bookings"), "fieldname": "total_bookings", "fieldtype": "Int", "width": 100},
        {"label": _("Total Sales"), "fieldname": "total_sales", "fieldtype": "Currency", "width": 120},
    ]

    # --- Data Query ---
    # We need to aggregate data from two sources:
    # 1. POS Invoice (Real Money)
    # 2. Service Booking (Operational Count)
    
    # Let's verify commonly used date range.
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += f" AND posting_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'"
    
    branch_condition = ""
    if filters.get("branch"):
        branch_condition = f" AND branch = '{filters.get('branch')}'"
        
    # Get Sales Data (POS Invoice)
    # Note: POS Invoices are linked to branches usually via POS Profile -> Warehouse -> Branch or Custom Field.
    # In our setup, POS Profile has a Warehouse. Warehouse name usually contains Branch Name 
    # OR we can rely on `Service Booking` link if populated.
    # Since we want ROBUST sales data, we check both. 
    # However, standard POS Invoice doesn't have "branch" field by default unless added.
    # We added "Branch" to "Service Booking".
    # Let's assume for now we join via the `pos_profile` name or we replicate the branch logic.
    # A simpler way given our recent testing: We created POS Profiles named "Main" etc.
    # Let's try to infer branch from POS Profile or Warehouse if direct link missing.
    # BUT, to keep it simple and aligned with our custom app:
    # We should have ensured POS Invoice has a branch. If not, we join Service Booking.
    
    sql = f"""
        SELECT 
            p.posting_date as date,
            '{filters.get('branch', 'All Branches')}' as branch,
            COUNT(DISTINCT s.name) as total_bookings,
            COALESCE(SUM(p.grand_total), 0) as total_sales
        FROM `tabPOS Invoice` p
        LEFT JOIN `tabService Booking` s ON s.invoice = p.name
        WHERE p.docstatus = 1 {conditions}
    """
    
    # Join columns explicitly
    where_conditions = "p.docstatus = 1"
    if conditions:
        where_conditions += conditions.replace("posting_date", "p.posting_date")
    
    if filters.get("branch"):
        where_conditions += f" AND s.branch = '{filters.get('branch')}'"

    sql = f"""
        SELECT 
            p.posting_date as date,
            s.branch as branch,
            COUNT(DISTINCT s.name) as total_bookings,
            SUM(p.grand_total) as total_sales
        FROM `tabPOS Invoice` p
        JOIN `tabService Booking` s ON s.invoice = p.name
        WHERE {where_conditions}
        GROUP BY p.posting_date, s.branch
        ORDER BY p.posting_date DESC
    """
    print(f"DEBUG SQL: {sql}")
    data = frappe.db.sql(sql, as_dict=True)
    data = frappe.db.sql(sql, as_dict=True)
    
    # Default to "Today" if no dates passed, to avoid massive querying if table grows? 
    # Or just let it query all.
    # Actually, standard reports usually respect the JS defaults.
    
    # ... logic ...
    
    # Return full tuple standard
    # columns, data, message, chart, summary, skip_total_row
    
    chart = []
    if data:
        # Simple Line Chart of Sales
        labels = [d.get("date") for d in data]
        values = [d.get("total_sales") for d in data]
        chart = {
            "data": {
                "labels": labels,
                "datasets": [{"name": "Sales", "values": values}]
            },
            "type": "line"
        }

    return columns, data, None, chart, None, 0
