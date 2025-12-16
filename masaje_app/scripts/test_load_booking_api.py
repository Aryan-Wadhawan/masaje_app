"""
Test Load Booking API
Run: bench --site erpnext.localhost execute masaje_app.scripts.test_load_booking_api.test
"""
import frappe


def test():
    """Test the load_booking_for_pos API"""
    from masaje_app.api import load_booking_for_pos, search_pending_bookings
    
    print("Testing search_pending_bookings...")
    results = search_pending_bookings(txt="")
    print(f"  Found {len(results)} pending bookings")
    
    if results:
        booking_name = results[0]["value"]
        print(f"\nTesting load_booking_for_pos for {booking_name}...")
        data = load_booking_for_pos(booking_name)
        print(f"  Customer: {data.get('customer')}")
        print(f"  Therapist: {data.get('therapist')}")
        print(f"  Branch: {data.get('branch')}")
        print(f"  Items: {len(data.get('items', []))}")
        for item in data.get('items', []):
            print(f"    - {item['item_code']}: {item.get('item_name')}")
    else:
        print("No pending bookings found")


if __name__ == "__main__":
    test()
