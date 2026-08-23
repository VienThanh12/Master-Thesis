---
name: code-visualizer-thesis
description: >-
  Creates images programmatically with SVG or Python (Pillow, matplotlib), and
  verifies any diagram derived from source code against the code itself before
  presenting it. Use when the user asks to draw, create, or generate an image,
  icon, chart, illustration or graphic, or to diagram a workflow, architecture
  or control flow taken from source code.
disable-model-invocation: true
---

# Draw Images

Create images using SVG (vector) or Python (raster). Choose based on use case.

For figures going into a paper or thesis, read
`~/.cursor/skills/latex-authoring/FIGURES.md` first: it covers sizing, fonts,
colour safety, uncertainty and captions, which decide whether a figure survives
review. This skill covers making the image and, in the last section, checking
that a code-derived diagram tells the truth.

## When to Use What

| Format | Best For |
|--------|----------|
| **SVG** | Icons, logos, diagrams, flowcharts, simple illustrations, scalable graphics |
| **Python/Pillow** | Photo manipulation, pixel art, complex raster graphics, image processing |
| **Python/matplotlib** | Charts, plots, data visualization, scientific graphics |

---

## SVG Images

### Basic Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <!-- Drawing elements here -->
</svg>
```

### Common Elements

```xml
<!-- Rectangle -->
<rect x="10" y="10" width="80" height="60" fill="#e94560" rx="5"/>

<!-- Circle -->
<circle cx="100" cy="100" r="40" fill="#3498db"/>

<!-- Ellipse -->
<ellipse cx="100" cy="100" rx="60" ry="30" fill="#2ecc71"/>

<!-- Line -->
<line x1="10" y1="10" x2="100" y2="100" stroke="#333" stroke-width="2"/>

<!-- Polyline (open shape) -->
<polyline points="10,10 50,50 90,10" fill="none" stroke="#e94560" stroke-width="2"/>

<!-- Polygon (closed shape) -->
<polygon points="100,10 150,100 50,100" fill="#f1c40f"/>

<!-- Path (complex shapes) -->
<path d="M10 80 Q 95 10 180 80" fill="none" stroke="#9b59b6" stroke-width="3"/>

<!-- Text -->
<text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="16" fill="#333">Hello</text>
```

### Gradients

```xml
<defs>
  <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#e94560"/>
    <stop offset="100%" style="stop-color:#0f3460"/>
  </linearGradient>
  <radialGradient id="grad2" cx="50%" cy="50%" r="50%">
    <stop offset="0%" style="stop-color:#fff"/>
    <stop offset="100%" style="stop-color:#3498db"/>
  </radialGradient>
</defs>
<rect fill="url(#grad1)" .../>
```

### Groups and Transforms

```xml
<g transform="translate(50, 50) rotate(45) scale(1.5)">
  <rect x="0" y="0" width="20" height="20" fill="#e94560"/>
</g>
```

### SVG Icons Example

```xml
<!-- Star icon -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <polygon points="12,2 15,9 22,9 17,14 19,21 12,17 5,21 7,14 2,9 9,9" fill="#f1c40f"/>
</svg>

<!-- Heart icon -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="#e94560"/>
</svg>
```

---

## Python with Pillow

### Setup
```bash
pip install Pillow
```

### Basic Template

```python
from PIL import Image, ImageDraw, ImageFont

# Create image
width, height = 800, 600
img = Image.new('RGB', (width, height), color='#16213e')
draw = ImageDraw.Draw(img)

# Draw here...

# Save
img.save('output.png')
```

### Drawing Operations

```python
# Rectangle
draw.rectangle([x1, y1, x2, y2], fill='#e94560', outline='#fff', width=2)

# Rounded rectangle
draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill='#3498db')

# Circle/Ellipse
draw.ellipse([x1, y1, x2, y2], fill='#2ecc71', outline='#fff')

# Line
draw.line([(x1, y1), (x2, y2)], fill='#e94560', width=3)

# Polygon
draw.polygon([(x1, y1), (x2, y2), (x3, y3)], fill='#f1c40f')

# Arc
draw.arc([x1, y1, x2, y2], start=0, end=180, fill='#9b59b6', width=3)

# Text
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
draw.text((x, y), 'Hello', fill='#fff', font=font, anchor='mm')
```

### With Transparency (RGBA)

```python
img = Image.new('RGBA', (width, height), (0, 0, 0, 0))  # Transparent background
draw = ImageDraw.Draw(img)
draw.ellipse([10, 10, 100, 100], fill=(233, 69, 96, 128))  # Semi-transparent
img.save('output.png')
```

---

## Python with matplotlib

### Setup
```bash
pip install matplotlib numpy
```

### Basic Figure

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))

# Draw here...

plt.savefig('output.png', dpi=150, bbox_inches='tight')
plt.close()
```

### Shapes with matplotlib

```python
from matplotlib.patches import Circle, Rectangle, Polygon, FancyBboxPatch
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')

# Circle
circle = Circle((5, 5), 2, color='#e94560')
ax.add_patch(circle)

# Rectangle
rect = Rectangle((1, 1), 3, 2, color='#3498db')
ax.add_patch(rect)

# Rounded rectangle
fancy = FancyBboxPatch((6, 1), 3, 2, boxstyle='round,pad=0.1', color='#2ecc71')
ax.add_patch(fancy)

# Polygon
poly = Polygon([(2, 7), (4, 9), (6, 7)], color='#f1c40f')
ax.add_patch(poly)

# Arrow
ax.annotate('', xy=(8, 8), xytext=(6, 6),
            arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2))

# Text
ax.text(5, 5, 'Hello', ha='center', va='center', fontsize=16, color='white')

plt.savefig('shapes.png', dpi=150, facecolor='#16213e', bbox_inches='tight')
```

### Charts

```python
# Bar chart
plt.bar(['A', 'B', 'C'], [10, 20, 15], color=['#e94560', '#3498db', '#2ecc71'])

# Line chart
plt.plot([1, 2, 3, 4], [1, 4, 2, 3], color='#e94560', linewidth=2, marker='o')

# Pie chart
plt.pie([30, 40, 30], labels=['A', 'B', 'C'], colors=['#e94560', '#3498db', '#2ecc71'])

# Scatter plot
plt.scatter(x_data, y_data, c='#e94560', s=50, alpha=0.7)
```

---

## Color Palette

| Purpose | Color |
|---------|-------|
| Background | `#1a1a2e`, `#16213e`, `#0f0f23` |
| Primary | `#e94560`, `#ff6b6b` |
| Secondary | `#3498db`, `#0f3460` |
| Accent | `#f1c40f`, `#2ecc71`, `#9b59b6` |
| Text | `#ffffff`, `#eaeaea`, `#333333` |

---

## Post-Generation Verification (MANDATORY for code-based diagrams)

When the image depicts a workflow, architecture, or logic derived from source code, you MUST perform a verification pass after generating the initial image. This catches inaccuracies before presenting to the user.

### Verification Procedure

**Step 1: Re-read the source code**
After writing the image file, go back and re-read the key source functions/files that the diagram is based on. Focus on:
- Function call order and nesting
- Conditional branches (if/else/switch) and their exact conditions
- Variable names, flag names, enum values used in decisions
- Error/edge-case handling paths
- Async boundaries (callbacks, state transitions)

**Step 2: Walk through the diagram against the code**
For each box/step/arrow in the diagram, confirm:
- [ ] The function name matches the real code exactly (spelling, class prefix)
- [ ] The condition text in decision diamonds matches the actual `if` condition in code
- [ ] The branching logic (Yes/No paths) is correct and not swapped
- [ ] The order of steps matches the actual execution order in the code
- [ ] No significant steps are omitted (especially error handling, early returns)
- [ ] The data flow labels (variable names, flags, enums) match the source code
- [ ] All paths eventually converge or terminate correctly

**Step 3: Check for common mistakes**
- Missing paths: Did you include all branches from switch/if-else chains?
- Wrong causality: Is A really the cause of B, or are they independent?
- Conflated steps: Are two separate function calls shown as one box?
- Wrong scope: Is a step shown in the wrong path/branch?
- Stale info: If the code has multiple versions (e.g., VoLTE vs VoNR), are the differences accurately reflected?

**Step 4: Fix and re-generate if needed**
If discrepancies are found, edit the image file to correct them. Then briefly explain to the user what was corrected. If no issues are found, state that the verification passed.

### Example Verification Workflow

```
1. Generate SVG/image based on understanding of source code
2. Write the image file
3. Re-read the actual source functions:
   - SemanticSearch or Grep for key function names
   - Read the relevant code sections
4. Compare each diagram element against real code
5. If issues found -> fix the image -> note corrections
6. If clean -> confirm verification passed
```

### When to Skip Verification
- Pure decorative images (icons, logos, illustrations)
- Generic diagrams not tied to specific source code
- User explicitly says "rough sketch is fine" or similar

---

## Output

- Save SVG files with `.svg` extension
- Save raster images as `.png` (transparency) or `.jpg` (smaller size)
- Default output directory: current working directory
- Always show the user the path to the created image
