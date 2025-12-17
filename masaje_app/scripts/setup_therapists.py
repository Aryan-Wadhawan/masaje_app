"""
Setup Therapists for Masaje de Bohol
Creates all therapist employees and their schedules (branch-agnostic).

Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_therapists.setup_all
"""
import frappe

# All therapists from the provided list
# Format: (surname, first_name, middle_name, mobile)
THERAPISTS = [
    ("AMPO", "Pamie", "Munil", "0920-8875322"),
    ("ANASCO", "Sandie", "", "0985-118-1056"),
    ("ANONUEVO", "Joshua Raphael", "Suello", "0966-756-4068"),
    ("APARECE", "Marjorie", "M.", "0946-231-0528"),
    ("APUYA", "Michelle", "Escaso", "0938-0770695"),
    ("AUZA", "Philip", "Lapuri", "0975-4180116"),
    ("AYOP", "Glenda", "Valloso", "0960-6087167"),
    ("BUTAWAN", "Lovely", "Mier", "0975-9144574"),
    ("CALAGOS", "Chelsie", "Escaso", "0955-544-7203"),
    ("CAMBANGAY", "Janelle", "Soria", "0935-873-1914"),
    ("CAMPUSO", "Judilo", "Alfante", "0938-8100730"),
    ("CEPEDOZA", "Efriel Jane", "Betasa", "0995-8842238"),
    ("CRISTAL", "Regiene", "Gurrea", "0993-9043292"),
    ("CUARESMA", "Janice", "Aniban", "0963-9005030"),
    ("CUTILLAS", "Jocelyn", "Vallecera", "0963-6467400"),
    ("DAMASO", "Melvin", "", "0956-5577845"),
    ("DECENILLA", "Regilyn", "Santos", "0946-2384781"),
    ("DUTERTE", "Janelyn", "", "0975-197-2290"),
    ("ESTOQUIA", "Charol Ann", "Arevalo", "0970-1921402"),
    ("FLORES", "Jocelis", "Buyan", "0955-3982549"),
    ("GAMANA", "Meralen", "Zerna", "0948-6406218"),
    ("GELICAME", "Elma", "Estillore", "0965-1853368"),
    ("GONZAGA", "Margelyn", "Orapa", "0935-125-7102"),
    ("GUCOR", "Rubie", "Riza", "0970-6281902"),
    ("GUDIA", "Rose Marie", "Bonio", "0985-0810175"),
    ("HOYLE", "Hannah Grace", "Banaag", "0955-490-5598"),
    ("HOYLE", "Heide", "Banaag", "0955-253-1220"),
    ("JAJI", "Princess Mae Ann", "Dela Pena", "0953-8076624"),
    ("JUSTOL", "Angel Mae", "", "0950-819-0047"),
    ("LANGAMEN", "Melannie", "Macas", "0970-6856741"),
    ("LEONES", "Michele", "Patentes", "0951-871-2604"),
    ("MAKILING", "Nikko", "Amandoron", "0927-8605846"),
    ("MILLOREA", "Nethz Claire", "Orapa", "0970-7590981"),
    ("MUNEZ", "Lymuel", "", "0927-6546489"),
    ("MUNIL", "Margie", "Silmaro", "0938-8288328"),
    ("MUTOC", "Jamaica", "", "0906-264-8741"),
    ("NARAGA", "Esperidion", "Caputan", "0949-5757658"),
    ("NAVAL", "Bryan Jay", "", "0966-362-4175"),
    ("ORAPA", "Anna Marie", "", "0938-747-7623"),
    ("ORAPA", "Airish", "", "0931-852-5041"),
    ("RECEMILLA", "Kelvin Jay", "", "0946-2310065"),
    ("REGANON", "Rosemarie", "Oyao", "0915-2719261"),
    ("ROSALES", "Joucyl", "Tagulalak", "0909-6828585"),
    ("SENDRIJAS", "Reyna", "Suello", "0956-2841432"),
    ("SUAYBAGUIO", "Mechiel", "Perez", "0955-5034224"),
    ("SUMATRA", "Prima", "Bangabanga", "0917-1473130"),
    ("TANDUGON", "Alvin", "Abanda", "0948-6376802"),
    ("TOREJAS", "Jane Margel", "Cuaresma", "0963-8746751"),
    ("TOREJAS", "June Myriel", "", "0936-312-9049"),
    ("TORRENUEVA", "Gerarld", "", "0997-675-7278"),
    ("TORREON", "Adelyn", "Dalogdog", "0931-9196676"),
    ("TUSOY", "Cristen", "Pedarios", "0938-4759805"),
    ("YATOR", "Angel Mae", "", "0953-762-1350"),
]

# Operating hours
WORKING_HOURS = {
    "start": "11:00:00",
    "end": "23:00:00"
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def setup_designation():
    """Create Therapist designation if not exists."""
    print("\n1. Setting up Designation...")
    if not frappe.db.exists("Designation", "Therapist"):
        frappe.get_doc({
            "doctype": "Designation",
            "designation_name": "Therapist"
        }).insert()
        print("   ✓ Created: Therapist designation")
    else:
        print("   ✓ Exists: Therapist designation")
    frappe.db.commit()


def setup_employees():
    """Create all therapist employees."""
    print("\n2. Creating Therapist Employees...")
    
    created_count = 0
    default_branch = "CPG East Branch"  # Home branch for admin purposes
    
    for surname, first_name, middle_name, mobile in THERAPISTS:
        # Create unique employee name
        full_name = f"{first_name} {surname}"
        
        # Check if employee exists by name
        existing = frappe.db.get_value("Employee", {"employee_name": full_name}, "name")
        if existing:
            print(f"   ✓ Exists: {full_name}")
            continue
        
        # Clean mobile number
        mobile_clean = mobile.replace("-", "")
        
        emp = frappe.get_doc({
            "doctype": "Employee",
            "first_name": first_name,
            "middle_name": middle_name if middle_name else None,
            "last_name": surname,
            "employee_name": full_name,
            "gender": "Female",  # Default, can be updated
            "date_of_birth": "1990-01-01",  # Placeholder
            "date_of_joining": "2024-01-01",  # Placeholder
            "status": "Active",
            "designation": "Therapist",
            "branch": default_branch,
            "cell_number": mobile_clean
        })
        emp.insert()
        created_count += 1
        print(f"   ✓ Created: {full_name} ({mobile})")
    
    frappe.db.commit()
    print(f"\n   Created {created_count} new employees, Total: {len(THERAPISTS)} therapists")


def setup_schedules():
    """Create therapist schedules - for ALL branches, all 7 days 11AM-11PM."""
    print("\n3. Creating Therapist Schedules...")
    
    # Get all therapist employees
    therapists = frappe.get_all("Employee", 
        filters={"designation": "Therapist", "status": "Active"},
        pluck="name")
    
    # Get all branches
    branches = frappe.get_all("Branch", pluck="name")
    
    if not branches:
        print("   ❌ No branches found!")
        return
    
    schedule_count = 0
    
    for emp_id in therapists:
        for branch in branches:
            for day in DAYS:
                # Check if schedule exists
                existing = frappe.db.exists("Therapist Schedule", {
                    "therapist": emp_id,
                    "day_of_week": day,
                    "branch": branch
                })
                
                if existing:
                    continue
                
                # Create schedule for this branch
                frappe.get_doc({
                    "doctype": "Therapist Schedule",
                    "therapist": emp_id,
                    "day_of_week": day,
                    "start_time": WORKING_HOURS["start"],
                    "end_time": WORKING_HOURS["end"],
                    "is_off": 0,
                    "branch": branch
                }).insert()
                schedule_count += 1
    
    frappe.db.commit()
    print(f"   ✓ Created {schedule_count} schedules")
    print(f"     ({len(therapists)} therapists x {len(branches)} branches x 7 days)")


def setup_all():
    """Run complete therapist setup."""
    print("=" * 60)
    print("SETTING UP THERAPISTS")
    print("=" * 60)
    
    setup_designation()
    setup_employees()
    setup_schedules()
    
    print("\n" + "=" * 60)
    print("✓ THERAPIST SETUP COMPLETE!")
    print(f"  Total Therapists: {len(THERAPISTS)}")
    print(f"  Working Hours: 11:00 AM - 11:00 PM")
    print(f"  Working Days: All 7 days")
    print("=" * 60)


if __name__ == "__main__":
    setup_all()
