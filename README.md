# JASS Parquet Image Explorer

### Explore Parquet data **and see the images inside it**

**PySide6 • PyArrow • Pandas • Local-first**

## Features

- 📂 Open any `.parquet` file
- 🖼 Detect image-related columns
- 🔎 Search accompanying text/metadata
- 📋 Tabular preview
- 👁 Show/hide columns
- 🖼 Select a row and preview its image
- 📐 Show image dimensions
- 💾 Save the selected image
- 📊 Dataset/schema information
- 💾 Original Parquet remains untouched

### Supported image forms

The Explorer attempts to render:

- embedded image bytes
- image paths
- dictionary-style values containing `bytes`, `data`, or `path`
- common image extensions such as JPG, PNG, WEBP, BMP, GIF and TIFF

## Installation

```bash
pip install PySide6 pyarrow pandas
```

Run:

```bash
python JASS_Parquet_Image_Explorer.py
```

## Typical workflow

1. Open a Parquet file.
2. Select the detected image column.
3. Browse rows.
4. Select a row.
5. View the image in the right-hand panel.
6. Search captions, labels or metadata.
7. Save an image when required.

## Large files

The Explorer reads only a bounded preview of the Parquet file using PyArrow row batches. A large file such as a **423 MB Parquet dataset** can therefore be investigated without automatically loading the entire file into memory.

Start with around **1,000 preview rows** and increase the limit when needed.

## JASS workflow

```text
Parquet
   ↓
Inspect schema
   ↓
See actual images
   ↓
Inspect captions / labels
   ↓
Search metadata
   ↓
Decide what to build next
```

## Status

**v1.0 — Stable working utility**

Future versions could add thumbnails, image zoom, contact sheets, batch extraction, multiple image columns, audio/video previews and full-dataset DuckDB search.

## JASS Digital Lab

Part of **JASS Digital Lab**, a practical collection of local-first desktop applications and data tools.

> **See the data. See the images. Understand the dataset.**
