"""
Script to automatically mark all text in HTML templates for translation
This finds plain text and wraps it with {{ _('text') }}
Use carefully - manually review the changes
"""
import os
import re
from pathlib import Path

template_dir = Path('slaptop/templates')

def mark_text_for_translation(html_content):
    """
    Marks plain text in HTML with {{ _() }} translation function
    Be careful not to translate HTML attributes, variables, etc.
    """
    
    # List of common HTML elements containing user-visible text
    # We'll focus on headers, paragraphs, buttons, labels, links
    patterns = [
        # <h1>Text</h1>, <h2>Text</h2>, etc
        (r'(<h[1-6][^>]*?>)([^<{]*?)(<\/h[1-6]>)', lambda m: m.group(1) + ("{{ _('%s') }}" % m.group(2).strip() if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(2)) + m.group(3) if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(0)),
        
        # <p>Text</p>
        (r'(<p[^>]*?>)([^<{]*?)(<\/p>)', lambda m: m.group(1) + ("{{ _('%s') }}" % m.group(2).strip() if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(2)) + m.group(3) if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(0)),
        
        # button>Text</button>
        (r'(<button[^>]*?>)([^<{]*?)(<\/button>)', lambda m: m.group(1) + ("{{ _('%s') }}" % m.group(2).strip() if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(2)) + m.group(3) if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(0)),
        
        # <label>Text</label>
        (r'(<label[^>]*?>)([^<{]*?)(<\/label>)', lambda m: m.group(1) + ("{{ _('%s') }}" % m.group(2).strip() if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(2)) + m.group(3) if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(0)),
        
        # <a>Text</a>  
        (r'(<a[^>]*?>)([^<{]*?)(<\/a>)', lambda m: m.group(1) + ("{{ _('%s') }}" % m.group(2).strip() if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(2)) + m.group(3) if m.group(2).strip() and not m.group(2).strip().startswith('{{') else m.group(0)),
    ]
    
    # Apply patterns carefully
    for pattern, replacement in patterns:
        html_content = re.sub(pattern, replacement, html_content)
    
    return html_content

# Process all HTML files
html_files = list(template_dir.glob('*.html'))
print(f"Found {len(html_files)} HTML files to process\n")

for html_file in html_files:
    print(f"Processing: {html_file.name}")
    
    try:
        content = html_file.read_text(encoding='utf-8')
        original_length = len(content)
        
        # Don't process base.html - already done
        if html_file.name == 'base.html':
            print("  → Skipping base.html (already translated)\n")
            continue
        
        # Mark text for translation
        new_content = mark_text_for_translation(content)
        
        # Only write if changes made
        if new_content != content:
            html_file.write_text(new_content, encoding='utf-8')
            print(f"  ✓ Updated - changes made")
        else:
            print(f"  → No changes needed (already wrapped)")
        
        print()
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")

print("Done! Now run:")
print("  pybabel extract -F babel.cfg -o messages.pot .")
print("  pybabel update -i messages.pot -d slaptop/translations")
print("  python auto_translate.py")
print("  pybabel compile -d slaptop/translations")
