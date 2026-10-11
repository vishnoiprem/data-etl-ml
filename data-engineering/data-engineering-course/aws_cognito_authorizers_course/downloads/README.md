# Downloads

This folder contains the printable PDF resources for the course. The
"real" deliverable is a PDF generated from the markdown placeholders
below by `pandoc` + a LaTeX template.

| # | File | When you'll use it |
|---|---|---|
| 1 | `cognito_cheat_sheet.md` (→ `cognito_cheat_sheet.pdf`) | Throughout the course — User Pool fields, Identity Pool fields, limits, IAM ARNs |
| 2 | `jwt_validation_cheat_sheet.md` (→ `jwt_validation_cheat_sheet.pdf`) | Section 4 (L19) and Section 5 (L25) — JWT header/payload claims, JWKS endpoint, validation recipe in `pyjwt` |

## Why `.md` and not `.pdf`?

The source of truth for each PDF is a markdown file in this folder. To
build a PDF locally:

```bash
pandoc downloads/cognito_cheat_sheet.md -o downloads/cognito_cheat_sheet.pdf
```

The course CI does this on every push. The `*.pdf` files in the published
zip are the result of that build.

## Generating all PDFs in one go

```bash
for md in downloads/*.md; do
    pandoc "$md" -o "${md%.md}.pdf"
done
```
