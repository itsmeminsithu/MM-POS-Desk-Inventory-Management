# GitHub setup

Repository name: `mm-pos-desk`

Description:

> A POS and inventory management app with business workspaces, warehouse stock, purchases, customers, printable receipts and sales reports.

Create an empty repository under your GitHub account. Do not add another README or license during creation. From the project folder:

```bash
git init
git add .
git commit -m "Initial MM POS Desk release"
git branch -M main
git remote add origin https://github.com/itsmeminsithu/mm-pos-desk.git
git push -u origin main
```

Change the remote if the repository owner or name differs. Authenticate with your own GitHub credentials.

Alternatively, use **Add file → Upload files** and upload the extracted source, including `.github/`, `.gitignore`, `.env.example` and migrations. Do not upload the ZIP as a substitute for source files. Do not upload `.local-data/` or `.venv/` after running the app.

The package does not automatically create a remote repository or deploy a hosted service.
