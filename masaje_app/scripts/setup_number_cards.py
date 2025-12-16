"""
Setup Number Cards for Masaje Dashboard
Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_number_cards.setup
"""
import frappe
import json
import os


def setup():
    """Create Number Cards for the Masaje Reception workspace"""
    print("Setting up Number Cards...")
    
    number_cards = [
        {
            "name": "Todays Sales",
            "label": "Today's Sales",
            "document_type": "POS Invoice",
            "function": "Sum",
            "aggregate_function_based_on": "grand_total",
            "filters_json": json.dumps([
                ["POS Invoice", "docstatus", "=", 1],
                ["POS Invoice", "posting_date", "Timespan", "today"]
            ]),
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Bookings Today",
            "label": "Bookings Today",
            "document_type": "Service Booking",
            "function": "Count",
            "filters_json": json.dumps([
                ["Service Booking", "booking_date", "Timespan", "today"]
            ]),
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Pending Bookings",
            "label": "Pending Bookings",
            "document_type": "Service Booking",
            "function": "Count",
            "filters_json": json.dumps([
                ["Service Booking", "status", "=", "Pending"]
            ]),
            "is_public": 1,
            "show_percentage_stats": 0,
            "stats_time_interval": "Daily"
        },
        {
            "name": "Completed Today",
            "label": "Completed Today",
            "document_type": "Service Booking",
            "function": "Count",
            "filters_json": json.dumps([
                ["Service Booking", "status", "=", "Completed"],
                ["Service Booking", "booking_date", "Timespan", "today"]
            ]),
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Daily"
        }
    ]
    
    for card_data in number_cards:
        create_or_update_number_card(card_data)
    
    frappe.db.commit()
    print("✓ Number Cards setup complete!")


def create_or_update_number_card(card_data):
    """Create or update a Number Card"""
    name = card_data["name"]
    
    if frappe.db.exists("Number Card", name):
        # Update existing
        doc = frappe.get_doc("Number Card", name)
        doc.update(card_data)
        doc.save()
        print(f"  - Updated: {name}")
    else:
        # Create new
        doc = frappe.new_doc("Number Card")
        doc.update(card_data)
        doc.type = "Document Type"
        doc.insert()
        print(f"  + Created: {name}")


if __name__ == "__main__":
    setup()
