
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
            filters["branch"] = employee.branch
    
    # --- Columns ---
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
        {"label": _("Total Bookings"), "fieldname": "total_bookings", "fieldtype": "Int", "width": 100},
        {"label": _("Total Sales"), "fieldname": "total_sales", "fieldtype": "Currency", "width": 120},
    ]

    # --- Build Query with Parameterized Filters ---
    conditions = ["p.docstatus = 1"]
    query_filters = {}
    
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("p.posting_date BETWEEN %(from_date)s AND %(to_date)s")
        query_filters["from_date"] = filters.get("from_date")
        query_filters["to_date"] = filters.get("to_date")
    
    if filters.get("branch"):
        # Check both POS Invoice branch (if set) and Service Booking branch
        conditions.append("(p.branch = %(branch)s OR s.branch = %(branch)s)")
        query_filters["branch"] = filters.get("branch")

    where_clause = " AND ".join(conditions)
    
    # Query with LEFT JOIN to capture both:
    # 1. Walk-in POS (no Service Booking link)
    # 2. Booking-linked POS Invoices
    sql = f"""
        SELECT 
            p.posting_date as date,
            COALESCE(s.branch, p.branch) as branch,
            COUNT(DISTINCT s.name) as total_bookings,
            SUM(p.grand_total) as total_sales
        FROM `tabPOS Invoice` p
        LEFT JOIN `tabService Booking` s ON s.invoice = p.name
        WHERE {where_clause}
        GROUP BY p.posting_date, COALESCE(s.branch, p.branch)
        ORDER BY p.posting_date DESC
    """
    
    data = frappe.db.sql(sql, query_filters, as_dict=True)
    
    # --- Chart ---
    chart = None
    if data:
        labels = [str(d.get("date")) for d in data]
        values = [float(d.get("total_sales") or 0) for d in data]
        chart = {
            "data": {
                "labels": labels,
                "datasets": [{"name": _("Sales"), "values": values}]
            },
            "type": "line"
        }

    return columns, data, None, chart, None, 0
