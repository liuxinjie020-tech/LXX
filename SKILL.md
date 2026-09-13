---
name: lixiang-layout-branding
description: Add a consistent LiXiang Design presentation frame, vector logo, and one centered watermark to architectural or design-sheet images. Use when the user asks to batch-brand, typeset, frame, or export submitted design boards.
---

# LiXiang Layout Branding

Turn supplied design-board images into consistent, high-resolution branded presentation sheets. The defaults preserve the visual system used for LiXiang Design's autumn rapid-design work: a white 4800 x 3400 canvas, orange frame, title, lower-left LiXiang Design logo, and one translucent centered watermark.

## Use

1. Inspect the supplied images and ask only if the user has given conflicting branding requirements. Preserve their drawings, annotations, and relative proportions; do not crop drawings to fill the page.
2. Use `scripts/brand_sheets.py` to batch-render JPG and PNG exports. It never alters its input files.
3. The default brand orange is `#EF6512`, matching the frame. Use [assets/lixiang-design-orange.svg](assets/lixiang-design-orange.svg) when a standalone logo is needed; the renderer redraws the same mark directly for crisp raster output.
4. Verify a representative export visually and confirm all exported files are 4800 x 3400 pixels at 300 DPI.

Example:

```powershell
python scripts/brand_sheets.py --input "C:\\work\\incoming" --output "C:\\work\\branded" --title "秋季快题作品展示"
```

## Branding invariants

- Keep only one large, centered watermark. Do not stack or repeat old and new watermarks. If an input is already branded, clean or rebuild it only after confirming the intended replacement scope with the user.
- Put the provided LiXiang Design block logo and `LiXiang Design` at the lower left. Recreate the vector geometry rather than enlarging a low-resolution reference image.
- Match the logo to the frame color unless the user chooses another color.
- Export both PNG and high-quality JPG at 300 DPI. Keep originals and earlier versions outside the output directory.
- Default heading: `秋季快题作品展示`. Change it when the user supplies a different title or says to omit it.

## Boundaries

This skill standardizes presentation and branding; it does not redraw the architectural work, remove content watermarks owned by a third party, or infer a new logo design. For a different brand, request its approved logo asset and color specification.
