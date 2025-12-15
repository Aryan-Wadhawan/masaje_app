
frappe.views.calendar["Service Booking"] = {
    field_map: {
        "start": "start_datetime",
        "end": "end_datetime",
        "id": "name",
        "title": "customer",
        "allDay": "all_day",
        "status": "status"
    },
    get_events_method: "frappe.desk.calendar.get_events",
    color_map: {
        "Pending": "orange",
        "Approved": "green",
        "Cancelled": "red",
        "Completed": "blue"
    }
}
