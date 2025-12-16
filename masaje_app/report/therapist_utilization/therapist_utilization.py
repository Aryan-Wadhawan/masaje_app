
import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    # --- Security / Permission Logic ---
    user = frappe.session.user
    if "System Manager" not in frappe.get_roles(user):
        employee = frappe.db.get_value("Employee", {"user_id": user}, ["name", "branch"], as_dict=True)
        if employee and employee.branch:
            filters["branch"] = employee.branch
    
    # --- Columns ---
    columns = [
        {"label": _("Therapist"), "fieldname": "therapist", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
        {"label": _("Total Bookings"), "fieldname": "total_bookings", "fieldtype": "Int", "width": 100},
        {"label": _("Booked Minutes"), "fieldname": "booked_minutes", "fieldtype": "Int", "width": 120},
        {"label": _("Revenue (Est)"), "fieldname": "revenue", "fieldtype": "Currency", "width": 120},
    ]

    # --- Build Query with Parameterized Filters ---
    conditions = ["s.status != 'Cancelled'", "s.therapist IS NOT NULL"]
    query_filters = {}
    
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("s.booking_date BETWEEN %(from_date)s AND %(to_date)s")
        query_filters["from_date"] = filters.get("from_date")
        query_filters["to_date"] = filters.get("to_date")
    
    if filters.get("branch"):
        conditions.append("s.branch = %(branch)s")
        query_filters["branch"] = filters.get("branch")

    if filters.get("therapist"):
        conditions.append("s.therapist = %(therapist)s")
        query_filters["therapist"] = filters.get("therapist")

    where_clause = " AND ".join(conditions)
    
    # Join with POS Invoice to get actual revenue
    sql = f"""
        SELECT 
            s.therapist as therapist,
            s.branch as branch,
            COUNT(s.name) as total_bookings,
            COALESCE(SUM(s.duration_minutes), 0) as booked_minutes,
            COALESCE(SUM(p.grand_total), 0) as revenue
        FROM `tabService Booking` s
        LEFT JOIN `tabPOS Invoice` p ON p.name = s.invoice AND p.docstatus = 1
        WHERE {where_clause}
        GROUP BY s.therapist, s.branch
        ORDER BY booked_minutes DESC
    """
    
    data = frappe.db.sql(sql, query_filters, as_dict=True)
    
    # --- Chart ---
    chart = None
    if data:
        labels = [str(d.get("therapist") or "Unknown") for d in data]
        values = [int(d.get("booked_minutes") or 0) for d in data]
        chart = {
            "data": {
                "labels": labels,
                "datasets": [{"name": _("Booked Minutes"), "values": values}]
            },
            "type": "bar"
        }

    return columns, data, None, chart, None, 0
