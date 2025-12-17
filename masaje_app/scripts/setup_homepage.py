"""
Create homepage as Frappe Web Page
Run: bench --site erpnext.localhost execute masaje_app.scripts.setup_homepage.create_homepage
"""
import frappe


def create_homepage():
    """Create or update the homepage Web Page."""
    frappe.set_user("Administrator")
    
    homepage_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Masaje de Bohol</title>
    <style>
      :root {
        --primary: #6b73ff;
        --primary-dark: #5560d8;
        --text: #1f2933;
        --muted: #51606d;
        --bg: #f7f9fb;
        --card: #ffffff;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
        line-height: 1.6;
      }
      header {
        padding: 18px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: var(--card);
        position: sticky;
        top: 0;
        z-index: 10;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
      }
      .brand {
        font-weight: 700;
        letter-spacing: 0.04em;
      }
      .cta {
        padding: 10px 18px;
        background: var(--primary);
        color: #fff;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        box-shadow: 0 8px 20px rgba(107, 115, 255, 0.25);
        transition: transform 0.1s ease, box-shadow 0.1s ease, background 0.2s ease;
      }
      .cta:hover {
        transform: translateY(-1px);
        background: var(--primary-dark);
        box-shadow: 0 10px 22px rgba(85, 96, 216, 0.28);
      }
      .hero {
        padding: 72px 24px 60px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 32px;
        align-items: center;
      }
      .hero-text h1 {
        font-size: clamp(32px, 4vw, 44px);
        margin: 0 0 12px;
      }
      .hero-text p {
        color: var(--muted);
        margin: 0 0 20px;
        max-width: 560px;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: #e6e9ff;
        color: #2f3b63;
        font-weight: 600;
        margin-bottom: 12px;
      }
      .card {
        background: var(--card);
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
      }
      h2.section-title {
        margin: 0 0 12px;
      }
      p.section-sub {
        margin: 0 0 24px;
        color: var(--muted);
      }
      ul.checks {
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 10px;
      }
      ul.checks li::before {
        content: "✓";
        color: var(--primary);
        font-weight: 700;
        margin-right: 8px;
      }
      footer {
        padding: 28px 24px 36px;
        text-align: center;
        color: var(--muted);
      }
    </style>
  </head>
  <body>
    <header>
      <div class="brand">Masaje de Bohol</div>
      <a class="cta" href="/book">Book Now</a>
    </header>

    <main>
      <section class="hero">
        <div class="hero-text">
          <div class="pill">Wellness • Massage • Sauna</div>
          <h1>Relax, recover, and recharge in Bohol.</h1>
          <p>
            Premium massage and sauna experiences across our branches. Choose your location,
            pick your preferred service, and book instantly.
          </p>
          <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <a class="cta" href="/book">Book Your Session</a>
            <a class="cta" style="background:#eef2ff;color:#2f3b63;box-shadow:none;" href="tel:+639000000000">Call to Book</a>
          </div>
        </div>
        <div class="card">
          <h3 style="margin-top:0;">Popular Services</h3>
          <ul class="checks">
            <li>Signature / Swedish / Thai Massage</li>
            <li>Ventosa & Aromatherapy</li>
            <li>Waxing & Body Scrub</li>
            <li>Sauna (Dao & Panglao only)</li>
            <li>Packages and add-ons</li>
          </ul>
        </div>
      </section>

      <section style="padding: 12px 24px 48px;">
        <h2 class="section-title">Why book with us</h2>
        <p class="section-sub">Simple online booking, branch-specific pricing, and experienced therapists.</p>
        <div class="grid">
          <div class="card">
            <h4>Instant Booking</h4>
            <p style="margin:0;color:var(--muted);">Check availability, pick a time, and confirm in seconds.</p>
          </div>
          <div class="card">
            <h4>Branch‑specific Services</h4>
            <p style="margin:0;color:var(--muted);">See only what's available at your chosen branch.</p>
          </div>
          <div class="card">
            <h4>Trusted Therapists</h4>
            <p style="margin:0;color:var(--muted);">Skilled teams across Bohol to match your preferred style.</p>
          </div>
          <div class="card">
            <h4>Transparent Pricing</h4>
            <p style="margin:0;color:var(--muted);">Standard and Panglao price lists—no surprises at checkout.</p>
          </div>
        </div>
      </section>
    </main>

    <footer>
      © Masaje de Bohol · Book online at <a href="/book">masajedebohol.com/book</a>
    </footer>
  </body>
</html>"""
    
    # We no longer rely on Web Page for the homepage; use static www/index.html instead.
    # If an old 'home' Web Page exists, unpublish it so it doesn't interfere with routing.
    if frappe.db.exists("Web Page", "home"):
        doc = frappe.get_doc("Web Page", "home")
        doc.published = 0
        doc.route = "home"
        doc.save(ignore_permissions=True)
        print("✓ Unpublished legacy 'home' Web Page")

    # Ensure Website Settings does NOT override the static homepage.
    try:
        ws = frappe.get_doc("Website Settings", "Website Settings")
        # Blank home_page => Frappe serves sites/.../www/index.html at /
        ws.home_page = ""
        ws.disable_signup = 0
        ws.save(ignore_permissions=True)
        print("✓ Website Settings home_page cleared to use static index.html")
    except Exception as e:
        print(f"⚠️ Could not update Website Settings: {e}")

    frappe.db.commit()
    print("\n✓ Homepage is now served from static index.html at: http://erpnext.localhost:8000/")
    print("  (If you still see an old page, hard refresh with /?no_cache=1 or clear browser cache.)")


if __name__ == "__main__":
    create_homepage()

