# Create Catalog

This directory stores the normalized capability catalog for the `Create` product area.

Rules:

- Use this catalog for creation modes, templates, and capability entry points.
- Do not treat these entries as published Seed personas.
- Keep the catalog focused on creation workflows:
  - self persona
  - source-based persona creation
  - relationship personas
  - digital twin workflows
  - protection and boundary tools
- Every entry should carry its upstream source repository and a product-facing group label.

The frontend reads this catalog through `GET /persona-api/create-catalog`.

All creation flows must also share the common material capability layer:

- text file upload
- image upload
- OCR text extraction
- shared `raw_materials` and distillation inputs

New creation paths should inherit this material layer by default instead of re-implementing upload or OCR handling per page.
