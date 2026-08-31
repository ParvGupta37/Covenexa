# Borrower View

> Full frontend documentation in [Dashboard.md](./Dashboard.md).

## Page: `/app/borrowers`

Lists all borrowers for the authenticated organization.

### Features
- Borrower cards showing: company name, sector, country, risk level badge
- Health score preview (if analyzed)
- Click borrower → sets as selected company in Zustand store
- Register new borrower modal

### Borrower Registration
```
POST /api/v1/borrowers/
Body: {
  company_name: string,
  sector: string,
  country: string,
  organization_id: string
}
```

Organization ID comes from the active organization in settings context.
