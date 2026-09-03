import re
import os

readme_path = r"c:\Users\Banwa\Desktop\IWT\CODING\PROJECTS\Sankalp-AI\README.md"
features_path = r"c:\Users\Banwa\Desktop\IWT\CODING\PROJECTS\Sankalp-AI\FEATURES.md"

with open(features_path, "r", encoding="utf-8") as f:
    features = f.read()

def repl(m):
    return '#' + m.group(0)

features_adjusted = re.sub(r'^#+', repl, features, flags=re.MULTILINE)
features_adjusted = features_adjusted.replace("## SankalpAI \u2014 Feature Inventory", "## Feature Inventory")
features_adjusted = features_adjusted.replace("## SankalpAI - Feature Inventory", "## Feature Inventory")

with open(readme_path, "r", encoding="utf-8") as f:
    readme = f.read()

license_idx = readme.find("## License")
if license_idx != -1:
    new_readme = readme[:license_idx] + features_adjusted.strip() + "\n\n" + readme[license_idx:]
else:
    new_readme = readme + "\n\n" + features_adjusted.strip()

with open(readme_path, "w", encoding="utf-8") as f:
    f.write(new_readme)

print("Merged successfully")
