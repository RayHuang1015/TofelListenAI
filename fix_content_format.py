import re

# Read the original content
with open('google_doc_content.txt', 'r') as f:
    content = f.read()

# Split into sections
lines = content.split('\n')
fixed_lines = []

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Parse lines like: TPO35 Section 1 1 :
    # Convert to: TPO 35 Section 1 Passage 1: 
    match = re.match(r'TPO(\d+)\s+Section\s+(\d+)\s+(\d+)\s*:', line)
    if match:
        tpo_num = match.group(1)
        section = match.group(2) 
        part = match.group(3)
        fixed_lines.append(f"TPO {tpo_num} Section {section} Passage {part}:")
        continue
    
    # Parse URL lines and clean them
    # Remove quotes and add to previous line
    if line.startswith('"https://') and line.endswith('.mp3"'):
        url = line[1:-1]  # Remove quotes
        if fixed_lines and fixed_lines[-1].endswith(':'):
            fixed_lines[-1] += f" {url}"
        continue
    elif line.startswith('https://') and line.endswith('.mp3'):
        if fixed_lines and fixed_lines[-1].endswith(':'):
            fixed_lines[-1] += f" {line}"
        continue
    
    # Keep other lines as is
    fixed_lines.append(line)

# Write fixed content
with open('google_doc_content_fixed.txt', 'w') as f:
    f.write('\n\n'.join(fixed_lines))

print(f"Fixed {len(fixed_lines)} lines")
