
app_name = "masaje_app"
app_title = "Masaje App"
app_publisher = "Aryan"
app_description = "Masaje App"
app_email = "test@example.com"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_js = "/assets/masaje_app/js/service_booking_calendar.js"
# app_include_css = "/assets/masaje_app/css/masaje_app.css"

fixtures = [
    "Item Price",
    "Branch",
    "Custom DocPerm"
]

# Document Events
# ----------------
# Hook on document methods and events

doc_events = {
    "Service Booking": {
        "after_insert": "masaje_app.events.on_service_booking_insert",
        "on_update": "masaje_app.events.on_service_booking_update"
    }
}
