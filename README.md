# MM POS Desk Inventory Management

Point of sale and inventory for a small shop. It runs on your own computer. Create a business account in the browser, add products, and start recording sales.

**Developer: Min SiThu (itsmeminsithu)**
[minsithu.org](https://minsithu.org/) · [Contact](https://minsithu.org/contact/) · [MIT License](LICENSE)

**Run the real app in GitHub:** [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/itsmeminsithu/MM-POS-Desk-Inventory-Management) — this starts the actual Django app in Codespaces. No other host, no static copy. Steps under "Codespaces" below.

## Run it locally first

You need Python **3.11 or newer**. If you don't have it, install it from [python.org](https://www.python.org/downloads/) and reopen Terminal.

Extract the ZIP, then in Terminal:

```bash
cd ~/Downloads/mm-pos-desk
python3 start.py
```

The launcher installs dependencies, prepares the database and opens **http://127.0.0.1:8001/**. The first install needs internet. Later launches reuse the environment.

1. In the browser, select **Create business**.
2. Enter your business name, username, email and password.
3. Choose **Settings & team → Load sample inventory** to try six example products, or add your own.
4. Use **Inventory → Move stock** to enter opening stock or receive a purchase.
5. Open **Point of sale** to record your first sale.

There is no Terminal account-creation prompt and **no default password**. You create the account in the browser. Keep Terminal open while you use the app; press **Control+C** to stop.

You can also run `bash Start-MM-POS.command` from the extracted folder. If macOS blocks double-click launching, use Terminal instead. Do not disable system security.

Windows: install Python 3.11+ and run `Start-MM-POS.bat` or `py -3 start.py`. Linux: `python3 start.py`.

Port 8001 lets this app run next to another app on port 8000. If 8001 is taken:

```bash
POS_PORT=8002 python3 start.py
```

Then open `http://127.0.0.1:8002/`.

## Codespaces

GitHub Pages cannot run a Django backend, so there is no always-on public link for this app from GitHub alone. Codespaces runs the real app:

1. Click **Open in GitHub Codespaces** above (or open https://codespaces.new/itsmeminsithu/MM-POS-Desk-Inventory-Management), choose a 2-core machine, and wait for setup. Setup installs the dependencies, runs migrations and checks the project.
2. In the Codespace terminal, run:

```bash
python3 start.py --no-browser
```

3. When port **8001** forwards, open it from the preview prompt or the Ports tab.
4. Select **Create business**, then **Settings & team → Load sample inventory** to try the POS with example products.
5. Stop the Codespace when you finish, to save your free quota. Data in a Codespace lives in that Codespace only. It is a demo, not a shared production shop.

The Pages site at https://itsmeminsithu.github.io/MM-POS-Desk-Inventory-Management/ is only a launch page for the Codespaces preview. It does not log you in or record sales.

## What it does

- Business workspaces with separate catalogs, stock, contacts and sales.
- Owner/cashier permissions, cashier account creation and access removal.
- POS product search, category filters and keyboard-style barcode scanner input.
- Server-calculated prices, fixed-amount discounts, percentage tax, cash tender and change.
- Cash, external card terminal, KPay, WavePay, bank transfer and MMQR payment records.
- Checkout retry protection and insufficient-stock checks.
- SKU, barcode, category, reference cost, selling price and reorder levels.
- Multiple warehouses, purchase receiving, stock adjustments and transfers.
- Stock movement history, low-stock indicators and sample opening inventory.
- Customer and supplier records.
- Sales history and printable receipts with saved product/price/business details.
- Full-sale returns with inventory restoration.
- Date-filtered summaries, payment-method totals, estimated gross margin and CSV export.
- Platform administration for a separately created superuser.

Not included: subscription billing, an online storefront, HR/payroll, accounting ledgers, direct payment APIs and automated fiscal reporting. This release is about daily retail work. See [ROADMAP.md](ROADMAP.md).

## Products and stock

Add a product with a SKU that is unique within its business. Quantities are **whole units**. Set selling price, reference cost and reorder threshold. Editing a product does not change stock — use the movement form, so each change has a reason and a person attached to it.

**Receive purchase** adds stock right away. Enter product, warehouse, quantity, purchase unit cost, and optional supplier and reference. Each purchase record is one received product line. Purchase-order drafts and supplier debt tracking are not included.

Use **Stock increase/decrease** for corrections, or **Transfer stock** to a different warehouse. Negative stock is rejected. Fix mistakes with a compensating adjustment; do not delete movement history.

Sample inventory only loads into an empty business. Sample prices are nominal amounts in the business currency, not converted prices. Check them before real use.

## Selling and receipts

Pick a warehouse and customer, then add products. A USB/Bluetooth scanner that types a barcode and presses Enter works in the search field. Camera scanning and barcode-label printing are not included.

Discount is a fixed amount, applied before tax. Tax is a percentage of the discounted subtotal, rounded to two decimal places. These are inputs for the calculation, not tax rules for any country.

For cash, enter the amount received. For other methods, check the payment outside the app and enter its reference. **Complete sale** records the sale, reduces stock and opens the receipt. Print or save a PDF from your browser.

If checkout loses its connection, retry the same sale. Do not take the money again. The POS keeps its pending request in the current browser session and the server recognises its ID. If you are not sure what happened, check Sales & receipts. If a price has changed, reload the POS before you continue.

Owners can record a **full return** from a receipt. All units go back to the original warehouse and the sale is left out of net sales reports. Handle the money refund separately. Partial returns, exchanges and refund accounting are not included.

## Team and workspaces

Owners manage products, stock, suppliers, settings, cashier accounts, reports and returns. Cashiers use the POS and can view products, inventory, customers and receipts. They cannot edit stock, products, or owner settings and reports.

Create cashiers under **Settings & team** and share the first login details privately. Removing a member removes their access to that business on the next request. It does not delete their account or their other memberships.

One account can own several businesses and switch between them. Businesses are separated by filtered records in one shared database, not by separate databases or schemas. A platform superuser can view records and disable businesses at `/admin/`. Business owners are not platform superusers.

## Payments and currencies

The payment methods are **records of money collected outside the app**. The app does not process cards, check bank settlements, create MMQR payloads, connect merchant accounts or handle chargebacks.

Each workspace has one fixed currency: MMK, THB or USD. Registration starts with an MMK workspace. **Create business** lets you pick another currency. There is no currency conversion and no mixed-currency checkout.

## Reports

Reports leave out full returns and use the original sale date. Estimated gross margin is sales minus tax and the reference cost saved at checkout. It does not use FIFO or weighted-average costing, and it does not count expenses. Purchase receipts do not change a product's reference cost on their own.

CSV exports escape spreadsheet formula prefixes in text fields. Receipts are sales records, not certified fiscal invoices. Printing goes through the browser. ESC/POS printers and cash drawers are not supported.

## Developer setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

Windows activation: `.venv\Scripts\activate`.

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Optional platform admin: `python manage.py createsuperuser`, then sign in at `/admin/`.

Where things live:

- `retail/models.py` — business, inventory, contacts and transaction records.
- `retail/services.py` — checkout, stock movements and returns.
- `retail/views.py` — permissions and routes.
- `retail/tests.py` — workflow and permission tests.
- `static/pos.js` — basket, product selection and checkout retries.
- `templates/` and `static/app.css` — interface and print layout.

## Data and backups

The database and development secret sit in `.local-data/`, which is excluded from Git. Stop the app before copying that folder for a backup. Keep backups somewhere safe. Never publish databases, secrets or `.venv`.

Settings come from environment variables. `.env.example` documents them; it is not loaded automatically. Core screens use local assets and system fonts.

Read [DEPLOYMENT.md](DEPLOYMENT.md) and [SECURITY.md](SECURITY.md) before hosting this in public. The launcher runs a development server. GitHub Pages cannot run this backend. See [GITHUB_SETUP.md](GITHUB_SETUP.md) to upload the source.

## Troubleshooting

- **Site cannot be reached:** wait for `Starting development server`, then open its URL and keep Terminal open.
- **Wrong folder:** run `python3 start.py` inside the extracted `mm-pos-desk` directory.
- **Python not found:** install Python and reopen Terminal; check `python3 --version`.
- **No POS products:** add active products and receive stock in the selected warehouse.
- **Checkout pending:** retry the same sale or check receipts before creating another sale.
- **Forgot password:** run `.venv/bin/python manage.py changepassword YOUR_USERNAME`.

Copyright © 2026 Min SiThu (itsmeminsithu). MIT License. Dependencies retain their respective licenses.
