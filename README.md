# Sentiment Classifier & Annotation Studio

A clean, modern, portable desktop GUI modeled after `FacebookCommentScraper_Portable`, featuring a **mathematically balanced, symmetrical button grid** and a **native Pango + HarfBuzz Complex Text Layout (CTL) engine** for flawless Bengali & Indic rendering.

---

## 🇧🇩 Full Bengali / Indic Script Support

Tkinter's standard X11 text renderer on Linux cannot shape complex Brahmic/Indic scripts, which previously caused:
- Pre-base vowel signs (ি, ে, ৈ) to appear on the wrong side of consonants.
- Conjunct ligatures (যুক্তবর্ণ like ক্ষ, ক্ত, ঙ্গ, ণ্ড, স্থ) to break into isolated letters with exposed hasantas.
- Reph (র্) to fail to bind over following consonants.

### The Solution:
`app.py` incorporates a native **Pango + HarfBuzz CTL engine** via `ctypes` (utilizing system `libpango` and `libcairo` with zero external pip dependencies). It renders:
- 100% accurate Bengali conjuncts and matra reordering.
- Clean word-wrapping and smooth vertical scrolling.
- Font scaling with **`A+`** / **`A-`**.
- Instant clipboard copying with **`📋 Copy`** or **`Ctrl+C`**.

---

## 📐 Interface Layout & Symmetry

```
+---------------------------------------------------------------------------------------------------+
| Sentiment Classifier & Annotation Studio v2.3.0                                                   |
| High-Speed Manual Annotation • Complex Bengali/Indic Engine • Portable Edition                    |
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
|  3. Classification Actions                                                                        |
|  +-------------------+-------------------+-------------------+-------------------+                |
|  | [ A ]  POSITIVE   | [ S ]  NEUTRAL    | [ D ]  NEGATIVE   | [ F ]  DISCARD    | (25% each)     |
|  +-------------------+-------------------+-------------------+-------------------+                |
|  +---------------------------------------+---------------------------------------+                |
|  |          ◀  PREVIOUS (LEFT)           |           NEXT (RIGHT)  ▶             | (50% each)     |
|  +---------------------------------------+---------------------------------------+                |
|       Always-listening keyboard shortcuts (A, S, D, F, ←, →) • Auto-saves every 10 rows           |
+---------------------------------------------------------------------------------------------------+
| Status: Auto-saved at 00:37 (Original CSV + 4 split files updated)         [More] [📄 Open CSV]    |
| [======================================= Progress Bar =========================================] |
+---------------------------------------------------------------------------------------------------+
```

---

## 🏃 Running the Application

```bash
python3 app.py
```

Or open directly with your dataset:
```bash
python3 app.py sample_dataset.csv
```
