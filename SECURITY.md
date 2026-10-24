# Security

Report concerns privately at https://minsithu.org/contact/. Do not post passwords, customer details or databases in public issues.

Controls include Django password hashing/session authentication, CSRF checks, business-scoped queries, owner/cashier permissions, server-calculated amounts and atomic stock changes. Sales and movements are not directly editable in the platform admin interface. Returns retain the original sale.

Receipts are available only to business members. Cashiers can see their business's transactions and customers, not just their own sales. Platform superusers have broader access.

Complete DEPLOYMENT.md before public operation. This release has not had an independent security audit. Tests are regression checks, not a security guarantee. Keep dependencies updated and back up local data securely.
