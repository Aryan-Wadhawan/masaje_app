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
            "fieldname": "hour",
            "label": _("Hour"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "booking_count",
            "label": _("Bookings"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "percentage",
            "label": _("% of Total"),
            "fieldtype": "Percent",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    # Get bookings grouped by hour
    raw_data = frappe.db.sql("""
        SELECT 
            HOUR(time_slot) as hour_num,
            COUNT(*) as booking_count
        FROM `tabService Booking`
        WHERE status != 'Cancelled'
            AND time_slot IS NOT NULL
            {conditions}
        GROUP BY HOUR(time_slot)
        ORDER BY hour_num
    """.format(conditions=conditions), filters, as_dict=1)
    
    # Calculate total for percentage
    total = sum(d.booking_count for d in raw_data) or 1
    
    # Format data
    data = []
    for row in raw_data:
        hour = row.hour_num
        hour_label = f"{hour:02d}:00 - {hour:02d}:59"
        if hour < 12:
            hour_label = f"{hour or 12} AM"
        elif hour == 12:
            hour_label = "12 PM"
        else:
            hour_label = f"{hour - 12} PM"
        
        data.append({
            "hour": hour_label,
            "booking_count": row.booking_count,
            "percentage": (row.booking_count / total) * 100
        })
    
    return data


def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("AND booking_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("AND booking_date <= %(to_date)s")
    
    if filters.get("branch"):
        conditions.append("AND branch = %(branch)s")
    
    return " ".join(conditions)


def get_chart(data):
    """Generate a bar chart of bookings by hour"""
    if not data:
        return None
    
    labels = [d["hour"] for d in data]
    values = [d["booking_count"] for d in data]
    
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
        "colors": ["#ff6b6b"]
    }
