"""
Auto-translate the .po file from English to Dutch using deep-translator
Run this script once to fill in Dutch translations automatically
"""
import polib
from deep_translator import GoogleTranslator

# Open the Dutch translation file
po_file = polib.pofile('slaptop/translations/nl/LC_MESSAGES/messages.po')

# Create translator (English to Dutch)
translator = GoogleTranslator(source_language='en', target_language='nl')

# Counter for tracking progress
translated_count = 0

# Go through each entry and translate if not already translated
for entry in po_file:
    if entry.msgid and not entry.msgstr:  # If there's English text but no Dutch translation yet
        try:
            translated_text = translator.translate(entry.msgid)
            entry.msgstr = translated_text
            translated_count += 1
            print(f"✓ Translated: {entry.msgid} → {translated_text}")
        except Exception as e:
            print(f"✗ Failed to translate '{entry.msgid}': {e}")

# Save the updated file
po_file.save('slaptop/translations/nl/LC_MESSAGES/messages.po')
print(f"\n✓ Done! Translated {translated_count} strings")
print("Review the translations and run: pybabel compile -d slaptop/translations")
