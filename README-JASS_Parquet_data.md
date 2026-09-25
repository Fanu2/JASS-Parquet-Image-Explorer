# JASS Parquet Data Explorer

### Any Parquet. One Explorer.

A lightweight **PySide6 + PyArrow + Pandas** desktop application for opening and investigating arbitrary `.parquet` datasets.

## Features

- 📂 Open any Parquet file
- 📊 Rows, row groups, file size and column count
- 🧩 Automatic schema inspection
- 🔎 Search across visible columns
- ↕ Sort rows
- 👁 Show/hide columns
- 📋 Tabular preview
- 🧮 Null/non-null counts
- 📈 Basic numeric profiling
- 🔤 Sample values for text columns
- 📤 Export current view to CSV
- 🌙 Dark/light mode
- 💾 Local/offline operation

## Design

```text
                 ANY PARQUET
                      │
                    PyArrow
                      │
              ┌───────┴────────┐
              │                │
            Schema          Preview
              │                │
              └───────┬────────┘
                      │
              JASS Explorer
          ┌───────────┼───────────┐
        Search       Sort       Profile
                      │
                    CSV
                   Export
```

The source Parquet file is never modified.

## Installation

```bash
pip install PySide6 pyarrow pandas
```

Run:

```bash
python JASS_Parquet_Data_Explorer.py
```

## Workflow

1. Open a `.parquet` file.
2. Inspect the automatically detected schema.
3. Browse a bounded preview.
4. Search across visible columns.
5. Select columns to profile them.
6. Sort records when useful.
7. Export the current view to CSV.

## Large files

The Explorer is designed as an **inspection tool**. It reads only enough Parquet row groups to satisfy the selected preview limit, rather than loading the entire dataset into memory.

For very large analytical workloads, PyArrow, DuckDB or a dedicated processing pipeline can be used before creating a specialized JASS application.

## Why it is useful in JASS

This provides a common first step for datasets downloaded from places such as Hugging Face or other data repositories:

```text
Parquet
  ↓
Inspect
  ↓
Understand schema
  ↓
Check sample records
  ↓
Check nulls / values
  ↓
Decide
  ├── keep as Parquet
  ├── clean / transform
  ├── convert to SQLite
  ├── build FTS5
  └── create a dedicated Explorer
```

## Status

**v1.0 — Stable working utility**

Future extensions could add row-group inspection, type-aware filters, charts, partitioned datasets and optional DuckDB integration.

## JASS Digital Lab

Part of **JASS Digital Lab**, the user's broader collection of practical local-first desktop applications and data tools.

> **Any Parquet. One Explorer.**
