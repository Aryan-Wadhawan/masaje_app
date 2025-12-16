"""
Setup Dashboard Charts for Masaje Dashboard
Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_dashboard_charts.setup
"""
import frappe
import json


def setup():
    """Create Dashboard Charts for the Masaje Reception workspace"""
    print("Setting up Dashboard Charts...")
    
    # 1. Weekly Sales Trend Chart
    create_weekly_sales_chart()
    
    # 2. Bookings by Status Chart
    create_bookings_by_status_chart()
    
    # 3. Update workspace to include charts
    update_workspace_with_charts()
    
    frappe.db.commit()
    print("✓ Dashboard Charts setup complete!")


def create_weekly_sales_chart():
    """Create a line chart showing daily sales for the past week"""
    chart_name = "Weekly Sales Trend"
    
    if frappe.db.exists("Dashboard Chart", chart_name):
        frappe.delete_doc("Dashboard Chart", chart_name)
    
    chart = frappe.new_doc("Dashboard Chart")
    chart.chart_name = chart_name
    chart.chart_type = "Count"
    chart.document_type = "POS Invoice"
    chart.based_on = "posting_date"
    chart.time_interval = "Daily"
    chart.timespan = "Last Week"
    chart.type = "Line"
    chart.filters_json = json.dumps([
        ["POS Invoice", "docstatus", "=", 1]
    ])
    chart.is_public = 1
    chart.is_standard = 1
    chart.module = "Masaje App"
    chart.insert()
    print(f"  + Created: {chart_name}")


def create_bookings_by_status_chart():
    """Create a bar/donut chart showing bookings grouped by status"""
    chart_name = "Bookings by Status"
    
    if frappe.db.exists("Dashboard Chart", chart_name):
        frappe.delete_doc("Dashboard Chart", chart_name)
    
    chart = frappe.new_doc("Dashboard Chart")
    chart.chart_name = chart_name
    chart.chart_type = "Group By"
    chart.document_type = "Service Booking"
    chart.group_by_type = "Count"
    chart.group_by_based_on = "status"
    chart.type = "Donut"
    chart.filters_json = json.dumps([
        ["Service Booking", "booking_date", "Timespan", "this week"]
    ])
    chart.is_public = 1
    chart.is_standard = 1
    chart.module = "Masaje App"
    chart.insert()
    print(f"  + Created: {chart_name}")


def update_workspace_with_charts():
    """Add charts to the Masaje Reception workspace"""
    workspace_name = "Masaje Reception"
    
    if not frappe.db.exists("Workspace", workspace_name):
        print(f"Workspace '{workspace_name}' not found")
        return
    
    workspace = frappe.get_doc("Workspace", workspace_name)
    
    # Add charts
    chart_names = ["Weekly Sales Trend", "Bookings by Status"]
    
    existing_charts = {c.chart_name for c in workspace.charts}
    
    for chart_name in chart_names:
        if chart_name not in existing_charts:
            workspace.append("charts", {
                "chart_name": chart_name,
                "label": chart_name
            })
    
    # Update content to include charts
    content = json.loads(workspace.content or "[]")
    
    # Check if charts already in content
    has_chart_section = any(item.get("id") == "chart_header" for item in content)
    
    if not has_chart_section:
        # Find index after number cards (after spacer_nc)
        insert_idx = 0
        for i, item in enumerate(content):
            if item.get("id") == "spacer_nc":
                insert_idx = i + 1
                break
        
        # Insert chart section
        chart_content = [
            {"id": "chart_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Trends</b></span>", "col": 12}},
            {"id": "chart_1", "type": "chart", "data": {"chart_name": "Weekly Sales Trend", "col": 6}},
            {"id": "chart_2", "type": "chart", "data": {"chart_name": "Bookings by Status", "col": 6}},
            {"id": "spacer_charts", "type": "spacer", "data": {"col": 12}}
        ]
        
        content = content[:insert_idx] + chart_content + content[insert_idx:]
        workspace.content = json.dumps(content)
    
    workspace.save()
    print("  - Updated workspace with charts")


if __name__ == "__main__":
    setup()
