# Deployment

The package is configured for local use with SQLite. Before public access:

- Use a production WSGI/ASGI server behind HTTPS. Do not expose Django's development server.
- Set `DJANGO_DEBUG=0`, a strong `DJANGO_SECRET_KEY` and explicit `DJANGO_ALLOWED_HOSTS`. Keep credentials outside Git.
- Configure a trusted reverse proxy to strip untrusted forwarded headers; add proxy/CSRF settings for your actual deployment.
- Run migrations and `python manage.py collectstatic`. Serve `staticfiles/`; never publish `.local-data/`.
- Add registration/login/checkout rate limits, request size limits, timeouts, monitoring and backups. Email verification, password-reset email, MFA and distributed login throttling are not included.
- Before concurrent production workloads, configure PostgreSQL and its driver, migrate data and test concurrency. SQLite can return lock errors during concurrent writes; checkout reports a retryable failure.
- Stock decrement uses a conditional update in a transaction, and checkout has a unique request ID. Test concurrent cashiers and stock operations on your production database.
- Secure the platform superuser account and review cashier access. Do not grant unrelated Django admin permissions.
- Establish record retention, support, refund, privacy and tax policies. No certified fiscal integration is included.
- Run `python manage.py check --deploy` with production settings and resolve warnings.

Public hosting, domain setup, subscription billing, merchant APIs, email delivery and production database provisioning are not included.
