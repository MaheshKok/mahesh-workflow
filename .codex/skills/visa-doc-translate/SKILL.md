---
name: visa-doc-translate
description: Prepare a bilingual draft translation of user-provided visa-document text, preserving source text and flagging uncertain OCR or translation segments. Use when a user needs a non-certified translation draft for review. Do not use to OCR files, install tools, create PDFs, or claim certification.
---

# Visa Translation Draft

## Required input

Need verbatim source text or user-supplied OCR, source language, target language, and intended use. Return `blocked` for image-only input or missing source text.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"source": "", "translation": "", "confidence": "high|medium|low", "review_note": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Preserve names, identifiers, dates, amounts, and layout markers verbatim beside translations.
- Mark unreadable, ambiguous, or OCR-derived text as uncertain; never invent content.
- State that the result is a draft, not a certified translation or legal advice.
- Do not inspect images, install packages, write files, or produce a PDF.

## Trigger checks

Trigger: "Translate this supplied bank-certificate text into English."; "Prepare a bilingual draft for this visa letter."; "Flag uncertain OCR in this translated employment record."; "Preserve these dates and amounts in translation."; "Review this translation draft before certification."

Do not trigger: "OCR this passport image."; "Make a certified translation."; "Generate a PDF."; "Install EasyOCR."; "Submit this visa application."
