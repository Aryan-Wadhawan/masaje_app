"""
Rebuild Masaje Reception workspace content to fix number cards
Run: bench --site erpnext.localhost execute masaje_app.scripts.rebuild_workspace_content.setup
"""
import frappe
import json


def setup():
    """Rebuild the workspace content with correct structure"""
    print("Rebuilding Masaje Reception workspace content...")
    
    workspace = frappe.get_doc("Workspace", "Masaje Reception")
    
    # Build fresh content
    content = [
        # Dashboard Header
        {"id": "nc_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Dashboard</b></span>", "col": 12}},
        
        # Number Cards - using simpler format
        {"id": "nc_1", "type": "number_card", "data": {"number_card_name": "Today's Sales", "col": 3}},
        {"id": "nc_2", "type": "number_card", "data": {"number_card_name": "Bookings Today", "col": 3}},
        {"id": "nc_3", "type": "number_card", "data": {"number_card_name": "Pending Bookings", "col": 3}},
        {"id": "nc_4", "type": "number_card", "data": {"number_card_name": "Completed Today", "col": 3}},
        
        # Spacer
        {"id": "spacer_nc", "type": "spacer", "data": {"col": 12}},
        
        # Trends Header
        {"id": "chart_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Trends</b></span>", "col": 12}},
        
        # Charts
        {"id": "chart_1", "type": "chart", "data": {"chart_name": "Weekly Sales Trend", "col": 6}},
        {"id": "chart_2", "type": "chart", "data": {"chart_name": "Bookings by Status", "col": 6}},
        
        # Spacer
        {"id": "spacer_charts", "type": "spacer", "data": {"col": 12}},
        
        # Quick Access Header
        {"id": "header_1", "type": "header", "data": {"text": "<span class=\"h4\"><b>Quick Access</b></span>", "col": 12}},
        
        # POS Button
        {"id": "pos_button", "type": "paragraph", "data": {"text": "<div style='margin-bottom: 15px;'><a href='/app/point-of-sale' class='btn btn-primary btn-lg' style='font-size: 16px; padding: 12px 30px;'><i class='fa fa-shopping-cart'></i> Open Point of Sale</a></div>", "col": 12}},
        
        # Shortcuts
        {"id": "sc_booking", "type": "shortcut", "data": {"shortcut_name": "New Booking", "col": 3}},
        {"id": "sc_sched", "type": "shortcut", "data": {"shortcut_name": "Therapist Schedule", "col": 3}},
        {"id": "sc_cust", "type": "shortcut", "data": {"shortcut_name": "Customers", "col": 3}},
        
        # Spacer
        {"id": "spacer_1", "type": "spacer", "data": {"col": 12}},
        
        # Operations Header
        {"id": "header_2", "type": "header", "data": {"text": "<span class=\"h4\"><b>Operations &amp; Reports</b></span>", "col": 12}},
        
        # Cards
        {"id": "card_ops", "type": "card", "data": {"card_name": "Operations", "col": 4}},
        {"id": "card_mgmt", "type": "card", "data": {"card_name": "Management", "col": 4}},
        {"id": "card_rpt", "type": "card", "data": {"card_name": "Reports", "col": 4}}
    ]
    
    # Update workspace
    workspace.content = json.dumps(content)
    
    # Ensure number_cards child table has entries
    workspace.number_cards = []
    for card_name in ["Today's Sales", "Bookings Today", "Pending Bookings", "Completed Today"]:
        workspace.append("number_cards", {"number_card_name": card_name})
    
    workspace.save()
    frappe.db.commit()
    
    print("✓ Workspace content rebuilt!")
    print("  Number cards in child table:", len(workspace.number_cards))


if __name__ == "__main__":
    setup()
