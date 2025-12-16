# Copyright (c) 2025, Masaje de Bohol
# License: MIT

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {
            "fieldname": "service_item",
            "label": _("Service"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 200
        },
        {
            "fieldname": "service_name",
            "label": _("Service Name"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "booking_count",
            "label": _("Bookings"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "total_revenue",
            "label": _("Revenue"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "avg_price",
            "label": _("Avg Price"),
            "fieldtype": "Currency",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            sbi.service_item,
            COALESCE(sbi.service_name, i.item_name) as service_name,
            COUNT(sbi.name) as booking_count,
            SUM(COALESCE(sbi.price, 0)) as total_revenue,
            AVG(COALESCE(sbi.price, 0)) as avg_price
        FROM `tabService Booking Item` sbi
        INNER JOIN `tabService Booking` sb ON sbi.parent = sb.name
        LEFT JOIN `tabItem` i ON sbi.service_item = i.name
        WHERE sb.status != 'Cancelled'
            {conditions}
        GROUP BY sbi.service_item
        ORDER BY booking_count DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND sb.booking_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND sb.booking_date <= %(to_date)s")
    
    if filters.get("branch"):
        conditions.append("AND sb.branch = %(branch)s")
    
    return " ".join(conditions)


def get_chart(data):
    """Generate a bar chart of popular services"""
    if not data:
        return None
    
    labels = [d.service_name or d.service_item for d in data[:10]]
    values = [d.booking_count for d in data[:10]]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Bookings",
                    "values": values
                }
            ]
        },
        "type": "bar",
        "colors": ["#5e64ff"]
    }
