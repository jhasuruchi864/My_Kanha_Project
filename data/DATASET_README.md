# Bhagavad Gita Dataset Documentation

**Project:** My_Kanha_Project (AI Spiritual Companion)
**Status:** Raw Data Source
**Format:** Relational JSON hierarchy
**Last Updated:** January 2026

---

## 1. Overview
This dataset contains the complete text of the Bhagavad Gita, structured relationally to separate core scripture from interpretations. This structure is designed to support a **RAG (Retrieval-Augmented Generation)** pipeline where the AI can cite specific verses and their purports.

**Primary Linking Key:** `verse_id` (found in `verse.json` as `id`).

---

## 2. File Manifest & Schema

### A. The Core Text (Source of Truth)
**File:** `verse.json`
* **Purpose:** Contains the original Sanskrit shlokas and definitions.
* **Key Fields:**
    * `id`: Unique Verse ID (Primary Key).
    * `chapter_number`: (1-18)
    * `verse_number`: (1-78)
    * `text`: Original Sanskrit (Devanagari). *Requires cleaning.*
    * `transliteration`: Romanized pronunciation (e.g., "Dharma-kshetre...").
    * `word_meanings`: Literal word-for-word translation.

### B. The Interpretations (The "Wisdom")
**File:** `translation.json`
* **Purpose:** Simple English/Hindi translation of the verse.
* **Key Fields:** `verse_id`, `author_id`, `description` (the translation text).

**File:** `commentary.json`
* **Purpose:** Detailed philosophical explanation (Purport).
* **Key Fields:** `verse_id`, `author_id`, `description` (the commentary text).
* **Note:** This file contains HTML tags (like `<br>`) that must be stripped.

### C. Metadata
* `chapters.json`: Chapter summaries and names. Used for high-level context.
* `authors.json`: Mapping of `author_id` to names (e.g., 16 = Swami Sivananda).
* `languages.json`: Mapping of language IDs (1=English, 2=Hindi, 3=Sanskrit).

---

## 3. Data Engineering Strategy

To prepare this data for the AI, we must merge these files into a single `gita_master.json`.

### A. Author Selection (Persona Consistency)
To prevent conflicting philosophical views (e.g., Dualism vs. Non-Dualism), filter `translation.json` and `commentary.json` by a specific `author_id`.

* **Recommended for English:** `author_id: 16` (Swami Sivananda) - *Clear, structural, good for AI logic.*
* **Recommended for Hindi:** `author_id: 1` (Swami Ramsukhdas) - *Devotional, accessible.*

### B. Text Cleaning Requirements (Crucial)
The raw JSON contains formatting artifacts that must be stripped before embedding into the Vector Database.

1.  **Newline Removal:**
    * Target: `verse.json` (field: `text`) and `transliteration`.
    * Action: Replace all instances of `\n` and `\r` with a single space ` `.
2.  **HTML Stripping:**
    * Target: `commentary.json` (field: `description`).
    * Action: Remove all HTML tags (e.g., `<br>`, `<p>`, `<i>`).
    * *Regex Suggestion:* `re.sub(r'<[^>]+>', '', text)`
3.  **Word Meanings Formatting:**
    * Target: `verse.json` (field: `word_meanings`).
    * Action: Ensure they are formatted as a clean string or list.
    * *Example Raw:* "dhṛitarāśhtraḥ uvācha—Dhritarashtra said;"
    * *Example Clean:* "dhṛitarāśhtraḥ uvācha: Dhritarashtra said"

---

## 4. Usage for AI (RAG System)

This dataset is designed to feed the "Context Window" of an LLM.

### The Retrieval Flow
1.  **User Query:** "Why should I work if I am going to fail?"
2.  **Search:** Vector search against `commentary` field in `gita_master.json`.
3.  **Retrieve:** Fetch Top 3 most relevant verses (e.g., Chapter 2 Verse 47).

### The System Prompt Template
When constructing the final prompt for the LLM, use the following structure:

```text
You are Krishna, the divine companion. The user is asking about: "{user_query}"

Use the following ancient wisdom to answer them kindly:

[SOURCE START]
Chapter {chapter}, Verse {verse}
Sanskrit: {cleaned_sanskrit_text}
Translation: {translation_text}
Commentary: {commentary_text}
[SOURCE END]

Instructions:
1. Answer in the first person ("I").
2. Do not lecture; guide them like a friend.
3. Explicitly cite the verse number if relevant.