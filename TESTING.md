# Validation

Validated on Linux with Python 3.12 and Django 5.2.18.

20 automated tests cover page responses, registration privileges, business isolation, server totals, cash change, payment references, insufficient-stock rollback, checkout retries, invalid amounts/quantities, stale prices, full returns, purchase receiving, warehouse transfers, negative-stock prevention, inventory replay protection, cashier permissions/revocation, CSRF, receipt snapshots, CSV formula escaping, inactive businesses and sample catalog protection.

Django system checks, migration consistency and JavaScript syntax checks pass. Run `python manage.py test` to repeat the suite.

Browser preview could not be completed because the preview runtime could not access Python. Visual layout, accessibility, hardware scanner/printer behavior and macOS/Windows launchers require testing on the intended devices. Django tests do not execute browser JavaScript. No live banking transaction, public deployment or load test was performed.

The GitHub Actions matrix will run on Linux, macOS and Windows after you push the repository; those remote runs are not claimed as completed here.
