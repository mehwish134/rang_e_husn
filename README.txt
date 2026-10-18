RANG-E-HUSN COMPLETE STARTER WEBSITE
====================================

FEATURES
- Responsive pink/white homepage
- Services and prices managed through admin dashboard
- Beauty product store
- Cart, checkout request, stock tracking
- Appointment request form
- SQLite database for orders and appointments
- Admin dashboard for order status, appointment status, products and services
- WhatsApp confirmation link for orders and appointments

WINDOWS SETUP (VS CODE)
1. Extract this ZIP file.
2. Open the extracted folder in VS Code.
3. Select Terminal > New Terminal.
4. Run each command separately:

   py -m venv .venv
   .venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python app.py

   If "py" is not recognised, use "python -m venv .venv" instead of the first command.

5. Open http://127.0.0.1:5000 in Chrome or Edge.
6. Keep the terminal open while using the site. Press Ctrl+C to stop the server.

ADMIN PANEL
- Open: http://127.0.0.1:5000/admin/login
- Default username: admin
- Default password: ChangeMe123!
- Change these before public hosting. Set environment variables ADMIN_USERNAME, ADMIN_PASSWORD and SECRET_KEY.

WHATSAPP
The number in app.py is 923186957897, corresponding to 03186957897.
For a different number, use country code 92 and remove the leading 0.

EDITING PRODUCTS/SERVICES
Use the admin dashboard to add or update products, prices, stock, services and service prices.
Products can be hidden from the store; historical order data remains.

DATABASE
rang_e_husn.db is created automatically next to app.py. Keep a backup.
The checkout is a request/order workflow, not a payment gateway. It does not take card payments.
Appointment times and orders need manual confirmation with the customer.
This app uses Flask's development server and SQLite for a beginner/local starter. Before making it public, arrange production hosting, secure configuration, backups, HTTPS and appropriate privacy/security review. Do not use debug mode on a public website.
