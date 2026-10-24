# MM POS Desk Inventory Management

A business desk for everyday sales, inventory, purchases and customer records. Run it on your computer, create a business account and start with your own catalog.

**Developer: Min SiThu (itsmeminsithu)**  
[minsithu.org](https://minsithu.org/) · [Contact](https://minsithu.org/contact/) · [MIT License](LICENSE)

## Features

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

This release focuses on daily retail operations. Subscription billing, an online storefront, HR/payroll, accounting ledgers, direct payment APIs and automated fiscal reporting are not included. See [ROADMAP.md](ROADMAP.md).

## Start on Mac

Requires Python **3.11 or newer**. Install it from [python.org](https://www.python.org/downloads/) if needed, then reopen Terminal.

Extract the ZIP. In Terminal:

```bash
cd ~/Downloads/mm-pos-desk
python3 start.py
```

The launcher installs dependencies, prepares the database and opens **http://127.0.0.1:8001/**. Initial installation needs internet access. Later launches reuse the environment.

1. In the browser, select **Create business**.
2. Enter your business name, username, email and password.
3. Choose **Settings & team → Load sample inventory** to try six example products, or add your own products.
4. Use **Inventory → Move stock** to enter opening stock or receive a purchase.
5. Open **Point of sale** to record your first sale.

**There is no Terminal account-creation prompt and no default password.** Create your account in the browser. Keep Terminal open while using the app; press **Control+C** to stop.

Alternatively, run `bash Start-MM-POS.command` from the extracted folder. If macOS blocks double-click launching, use Terminal. Do not disable system security.

Windows: install Python 3.11+ and run `Start-MM-POS.bat` or `py -3 start.py`. Linux: `python3 start.py`.

Port 8001 lets this app run alongside another app on port 8000. If occupied:

```bash
POS_PORT=8002 python3 start.py
```

Then open `http://127.0.0.1:8002/`.

## Products and inventory

Add a product with a unique SKU within its business. Quantities are **whole units**. Set selling price, reference cost and reorder threshold. Product edits do not directly change inventory; use the movement form so each change has a reason and actor.

**Receive purchase** immediately adds stock. Enter product, warehouse, quantity, purchase unit cost, optional supplier and reference. Each purchase record is one received product line; purchase-order drafts and supplier debt tracking are not included.

Use **Stock increase/decrease** for corrections or **Transfer stock** with a different destination warehouse. Negative stock is rejected. Record compensating adjustments for mistakes rather than deleting movement history.

Sample inventory is available only for an empty business. Sample prices are nominal amounts in its currency, not converted prices. Review them before real use.

## Point of sale and receipts

Choose a warehouse and customer, then add products. A USB/Bluetooth scanner that types a barcode and presses Enter can use the search field. Camera scanning and barcode-label printing are not included.

Discount is a fixed amount applied before tax. Tax is a percentage of the discounted subtotal, rounded to two decimal places. These are calculation inputs, not jurisdiction-specific tax rules.

For cash, enter the received amount. For other methods, verify the payment externally and enter its reference. **Complete sale** records the sale, reduces stock and opens the receipt. Print or save PDF using your browser.

If checkout loses its connection, retry the same sale. Do not collect money again. The POS retains its pending request in the current browser session; the server recognizes its ID. Check Sales & receipts if uncertain. A changed price requires reloading the POS before proceeding.

Owners can record a **full return** from a receipt. All units are restored to the original warehouse and the sale is excluded from net sales reports. Complete any money refund separately. Partial returns, exchanges and refund accounting are not included.

## Team and workspaces

Owners manage products, stock, suppliers, settings, cashier accounts, reports and returns. Cashiers use POS and view products, inventory, customers and receipts. They cannot edit stock, products or owner settings/reports.

Create cashiers under **Settings & team** and share initial credentials privately. Removing membership removes business access on the next request. It does not delete the user's other memberships or account.

An account can own multiple businesses and switch between them. Isolation uses business-filtered records in a shared database, not separate databases or schemas. A platform superuser can view records and disable businesses at `/admin/`. Business owners are not platform superusers.

## Payments and currencies

Methods are **records of payments collected outside the app**. The app does not process cards, verify bank settlements, create MMQR payloads, connect merchant accounts or manage chargebacks.

Each workspace has one fixed currency: MMK, THB or USD. Initial registration creates an MMK workspace. **Create business** lets you select another currency. There is no currency conversion or mixed-currency checkout.

## Reports

Reports exclude full returns and use the original sale date. Estimated gross margin equals sales less tax and the reference cost saved at checkout. It does not use FIFO/weighted-average costing or expenses. Purchase receipts do not automatically change reference product costs.

CSV exports escape spreadsheet formula prefixes in text fields. Receipts are sales records, not certified fiscal invoices. Printing uses the browser; direct ESC/POS and cash-drawer hardware are not included.

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

Optional platform administrator: `python manage.py createsuperuser`, then sign in at `/admin/`.

Source layout:

- `retail/models.py`: business, inventory, contacts and transaction records.
- `retail/services.py`: atomic checkout, stock movements and returns.
- `retail/views.py`: authorization and application routes.
- `retail/tests.py`: workflow and permission tests.
- `static/pos.js`: basket, product selection and checkout retries.
- `templates/` and `static/app.css`: interface and print layout.

## Data and backups

Database and development secret are stored in `.local-data/`, excluded from Git. Stop the app before copying that directory for a backup. Store backups securely; never publish databases, secrets or `.venv/`.

Configuration uses environment variables. `.env.example` is documentation, not automatically loaded. Core screens use local assets and system fonts.

Read [DEPLOYMENT.md](DEPLOYMENT.md) and [SECURITY.md](SECURITY.md) before public hosting. The launcher uses a development server. GitHub Pages cannot run this backend. See [GITHUB_SETUP.md](GITHUB_SETUP.md) to upload the source.

## Troubleshooting

- **Site cannot be reached:** wait for `Starting development server`, then open its URL and keep Terminal open.
- **Wrong folder:** run `python3 start.py` inside the extracted `mm-pos-desk` directory.
- **Python not found:** install Python and reopen Terminal; check `python3 --version`.
- **No POS products:** add active products and receive stock in the selected warehouse.
- **Checkout pending:** retry the same sale or check receipts before creating another sale.
- **Forgot password:** run `.venv/bin/python manage.py changepassword YOUR_USERNAME`.

Copyright © 2026 Min SiThu (itsmeminsithu). MIT License. Dependencies retain their respective licenses.
