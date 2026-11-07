# Sentiment Classifier & Annotation Studio

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![CTL Engine](https://img.shields.io/badge/Text%20Engine-Pango%20%2B%20HarfBuzz-informational.svg)](https://pango.gnome.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)]()

A modern, high-speed, portable desktop data annotation studio engineered for rapid sentiment classification and qualitative text tagging. Built with a mathematically balanced user interface and a native **Pango + HarfBuzz Complex Text Layout (CTL)** rendering engine, it delivers flawless rendering for Bengali, Indic, and multilingual text datasets with **zero external Python package dependencies**.

---

## 🌟 Key Highlights

- **⚡ Blazing Fast Annotation**: Label thousands of samples per hour using single-finger keyboard hotkeys (`A`, `S`, `D`, `F`) and arrow navigation (`←`, `→`).
- **🇧🇩 Native Bengali & Indic CTL Engine**: Bypasses standard Tkinter X11 font rendering limitations using `libpango` and `libcairo` via `ctypes`. Accurately renders complex conjuncts (যুক্তবর্ণ), pre-base vowel signs (ি, ে, ৈ), and reph (র্).
- **💾 Dual-Stream Auto-Saving**: Automatically saves every 10 rows and on window close. Directly updates the master CSV file while simultaneously streaming labeled rows into 4 segregated CSV files (`_positive.csv`, `_negative.csv`, `_neutral.csv`, `_discard.csv`).
- **🔄 Session Resilience & Checkpointing**: Maintains a lightweight JSON progress checkpoint (`*_label_progress.json`). Automatically resumes at the first pending row upon reload.
- **📐 Mathematically Balanced UI**: Ergonomically structured 4-column classification grid (25% width each) and balanced 50/50 navigation controls modeled after portable scraping and annotation suites.
- **🌐 Universal Encoding & Delimiter Support**: Automatically sniffs separators (`,`, `;`, `\t`, `|`) and decodes UTF-8, UTF-8-BOM, Latin-1, and CP1252 files.

---

## 🖥️ User Interface Overview

```
+---------------------------------------------------------------------------------------------------+
| Sentiment Classifier Studio v2.3.0                                                                |
| High-Speed Annotation • Complex Bengali Engine • Portable Edition                                 |
+---------------------------------------------------------------------------------------------------+
|  1. Dataset File & Column                                                                         |
|  Dataset CSV:  [/path/to/dataset.csv                     ]  [ Browse... ]  [ Open Folder  ]       |
|  Text Column:  [review_text                            ▼]   Jump: [  ] [Go] [ Jump to Last ]      |
+---------------------------------------------------------------------------------------------------+
|  2. Current Row Text                                                                              |
|  Row: 42 of 50,000      ● LABEL: POSITIVE (or ○ PENDING)                 [📋 Copy] [A-] [A+]      |
|  +---------------------------------------------------------------------------------------------+  |
|  | প্রোডাক্টটি সত্যি অসাধারণ! বিল্ড কোয়ালিটি এবং প্যাকেজিং খুবই চমৎকার ছিল।                      |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
|  3. Classification Actions [Shortcuts: A, S, D, F | Navigation: ←, →]                              |
|  +-------------------+-------------------+-------------------+-------------------+                |
|  | [ A ]  POSITIVE   | [ S ]  NEUTRAL    | [ D ]  NEGATIVE   | [ F ]  DISCARD    | (25% each)     |
|  +-------------------+-------------------+-------------------+-------------------+                |
|  +---------------------------------------+---------------------------------------+                |
|  |       ◀  PREVIOUS (LEFT)              |           NEXT (RIGHT)  ▶             | (50% each)     |
|  +---------------------------------------+---------------------------------------+                |
+---------------------------------------------------------------------------------------------------+
| Status: Auto-saved at 00:37 (Original CSV + 4 split files updated)         [More] [📄 Open CSV]    |
| [======================================= Progress Bar =========================================] |
+---------------------------------------------------------------------------------------------------+
```

---

## 🇧🇩 Why the Native CTL Engine Matters

Standard Tkinter text widgets on Linux rely on basic X11 font rendering without full HarfBuzz text shaping. For Indic scripts such as Bengali, this traditionally leads to severe visual corruption:
- Pre-base vowel signs (*hroshsho-i kar*, *e-kar*) appear after consonants instead of before them.
- Complex conjunct ligatures (e.g., ক্ষ, ক্ত, ঙ্গ, ণ্ড, স্থ) decompose into isolated consonants and exposed viramas/hasantas (্).
- Reph (র্) fails to bind properly across grapheme clusters.

### The Pango + Cairo Solution
`SentimentClassifier` features an integrated C-level bridging layer (`PangoHarfBuzzRenderer`) using standard system libraries (`libcairo.so.2`, `libpango-1.0.so.0`, `libpangocairo-1.0.so.0`). It renders text off-screen into high-definition rasterized surfaces, providing:
- 100% linguistically correct conjunct shaping and vowel reordering.
- Responsive word-wrapping matching canvas resizing.
- Dynamic font size adjustment with **`A+`** / **`A-`**.
- Instant clipboard copying with **`📋 Copy`** or **`Ctrl+C`**.
- Graceful automatic fallback to standard text widgets if Pango libraries are absent.

---

## ⌨️ Keyboard Shortcuts Reference

The studio is designed for continuous, hands-on-keyboard annotation without reaching for the mouse:

| Action | Default Key | Configurable | Description |
| :--- | :---: | :---: | :--- |
| **Label Positive** | <kbd>A</kbd> | Yes | Assigns `positive`, auto-advances to next row |
| **Label Neutral** | <kbd>S</kbd> | Yes | Assigns `neutral`, auto-advances to next row |
| **Label Negative** | <kbd>D</kbd> | Yes | Assigns `negative`, auto-advances to next row |
| **Label Discard** | <kbd>F</kbd> | Yes | Assigns `discard` (spam/noise), auto-advances |
| **Previous Row** | <kbd>←</kbd> or <kbd>Backspace</kbd> | Yes | Moves to previous row without altering label |
| **Next Row** | <kbd>→</kbd>, <kbd>Space</kbd>, <kbd>Enter</kbd> | Yes | Advances to next row |
| **Copy Text** | <kbd>Ctrl</kbd> + <kbd>C</kbd> | No | Copies current row text to system clipboard |
| **Jump to Row** | <kbd>Enter</kbd> in jump box | No | Jumps directly to specified 1-based row number |

> [!TIP]
> Custom key bindings can be configured on the fly via **More ▾ → ⚙️ Shortcuts...** and are permanently saved to `~/.sentiment_annotator_config.json`.

---

## 🚀 Getting Started

### 1. Prerequisites

The application uses standard Python 3 and system libraries, requiring **no `pip install` commands**:

- **Python**: 3.8 or higher
- **Tkinter**: GUI library
- **Pango & Cairo** *(recommended for Bengali/Indic scripts)*:
  ```bash
  # Debian / Ubuntu / Linux Mint
  sudo apt-get update
  sudo apt-get install python3-tk libpango1.0-dev libcairo2 fonts-noto-core fonts-beng
  
  # Fedora / RHEL
  sudo dnf install python3-tkinter pango cairo google-noto-sans-bengali-fonts
  
  # Arch Linux
  sudo pacman -S tk pango cairo noto-fonts
  ```

### 2. Launching the Studio

Launch the application directly:
```bash
python3 app.py
```

Or preload your CSV dataset directly from the command line:
```bash
python3 app.py path/to/dataset.csv
```

---

## 📊 Dataset Workflow & File Outputs

When you open a dataset (e.g. `reviews.csv`), the application manages the following files in the dataset directory:

```
📁 dataset_directory/
├── reviews.csv                      # Primary dataset (updated in-place)
├── reviews_label_progress.json      # Checkpoint state (row index & labels)
├── reviews_positive.csv             # Filtered positive instances
├── reviews_neutral.csv              # Filtered neutral instances
├── reviews_negative.csv             # Filtered negative instances
└── reviews_discard.csv              # Filtered discard/spam instances
```

### 1. Master CSV (`reviews.csv`)
The application adds or updates two standardized columns while preserving all existing columns and row order:
- `sentiment`: Set to `positive`, `neutral`, `negative`, or `discard`.
- `status`: Marked as `LABELED` or `PENDING`.

### 2. Segmented CSVs (`*_positive.csv`, etc.)
Real-time split files containing only rows classified under that specific category. Useful for immediate training pipelines or team distribution.

### 3. Checkpoint JSON (`*_label_progress.json`)
Tracks labeling progress, row counts, and timestamp. On reloading `reviews.csv`, the studio restores existing labels and automatically jumps to the first pending row.

---

## 🛠️ Menu & Navigation Tools

Click the **More ▾** button at the bottom-right for advanced controls:
- **⚙️ Shortcuts...**: Remap classification and navigation hotkeys.
- **🔄 Reset...**: 
  - *Option 1*: Clear the label for the current row.
  - *Option 2*: Clear all labels in the active dataset.
- **💾 Save CSV Now**: Force an immediate manual write of the master CSV, split files, and JSON checkpoint.
- **⚡ Next Unlabeled Row**: Instantly jump to the next unannotated item.
- **⏮ Jump to First Row** / **⏭ Jump to Last Row**: Quick navigation across massive datasets.
- **📄 Open Dataset CSV**: Opens the active dataset in your default spreadsheet viewer (e.g., LibreOffice Calc, Excel) cleanly in the background.
- **Open Folder**: Opens the current dataset's directory in your file manager.

---

## 🧪 Testing & Verification

A comprehensive automated test suite is included in [`test_app.py`](test_app.py) to verify end-to-end functionality (dataset loading, navigation, auto-saving, CSV splitting, reset logic, and menu operations):

```bash
python3 test_app.py
```

Expected output:
```text
[1] Loading sample CSV...
[2] Testing Jump to Last and Jump to First...
 -> Jump to Last verified (index 9 / row 10).
 -> Jump to First verified (index 0 / row 1).
[3] Testing classification and auto-save after 10 labels...
 -> 10 labels applied and auto-save completed.
[4] Verifying original CSV has 'sentiment' and 'status' columns...
 -> Original CSV verified! Header: ['id', 'review_text', 'source', 'author', 'sentiment', 'status']
[5] Verifying 4 split CSV files...
 -> sample_dataset_positive.csv verified with 4 rows.
 -> sample_dataset_negative.csv verified with 2 rows.
 -> sample_dataset_neutral.csv verified with 2 rows.
 -> sample_dataset_discard.csv verified with 2 rows.
[6] Testing reset current row...
 -> Single row reset verified.
[7] Testing More ▾ menu items...
 -> More ▾ menu items verified.

✅ ALL TESTS PASSED SUCCESSFULLY!
```

---

## 📁 Repository Structure

```
SentimentClassifier/
├── app.py                 # Main desktop application & PangoHarfBuzz renderer
├── test_app.py            # Automated test suite
├── sample_dataset.csv     # Multilingual sample dataset (English & Bengali)
└── README.md              # Documentation and user guide
```

---

## 📄 License

This project is licensed under the MIT License — free for both academic research and commercial use.
