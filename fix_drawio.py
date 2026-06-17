import os

with open("class_diagram.drawio", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('as_="geometry"', 'as="geometry"')

with open("class_diagram.drawio", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed draw.io XML attributes.")
