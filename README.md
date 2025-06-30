# OCR Comparison: Tesseract vs Amazon Textract

This repository contains scripts, configuration, and sample results from testing OCR quality across a variety of document types in the New York Philharmonic Archives.

## Objective

To evaluate whether we can rely primarily on open-source Tesseract or whether Amazon Textract is needed for complex documents (e.g., overlaid stamps, handwriting).

## Summary of Findings

- ✅ Tesseract (with tuned settings) performs well on clean, typed materials.
- ❌ Tesseract struggles with:
  - Overlaid stamps (e.g., "COPY")
  - Handwriting
- ✅ Textract produced **much better results** in those cases.

## Recommended Strategy

- Use **Tesseract** for most documents with:
  - `--psm 3 --oem 1`
  - Grayscale JPEGs converted from JP2 with enhanced contrast

- Use **Amazon Textract** for:
  - Stamped letters
  - Handwritten annotations

## Contents

- `ocr_comparison.py`: main OCR test harness
- `test_images/`: location for input images (JP2s, JPGs, etc.)
- `results/`: sample outputs for Tesseract and Textract

## How to Run

1. Install Python dependency:

```bash
pip install boto3
```

2. Configure your AWS credentials (for Textract):

```bash
aws configure --profile textract-test
```

3. Run the script:

```bash
python ocr_comparison.py
```
