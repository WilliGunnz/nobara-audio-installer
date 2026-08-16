# Publishing Workflow Guide

**Nobara Audio Installer (NAI)** — Complete publishing reference

---

## Quick Reference Cheat Sheet

| Task | Command |
|------|---------|
| Run diagnostics | `nai doctor` |
| Scan library for packages | `nai scan ~/Documents/nobara-audio-library` |
| Create new package skeleton | `nai init-package <name> --category <cat>` |
| Test publish (no upload) | `nai publish <package> --dry-run` |
| Publish to GitHub | `nai publish <package>` |
| Install package | `nai install <package-id>` |
| List installed packages | `nai list` |
| Verify installed package | `nai verify <package-id>` |
| Uninstall package | `nai uninstall <package-id>` |
| View configuration | `nai config --list` |
| Set config value | `nai config --set-key <key> --set-value <value>` |

---

## 1. Prerequisites

### 1.1 SSH Setup for Git

bash

Verify SSH key
ssh -T git@github.com

Configure Git
git config --global user.name "WilliGunnz" git config --global user.email "your-email@example.com"

1.2 GitHub Personal Access Token
Required for nai publish to upload releases

Create token at: https://github.com/settings/tokens
Scope: repo (Full control of private repositories)
Store securely
Configure in NAI:
nai config --set-key github_user --set-value WilliGunnz
nai config --set-key github_repo --set-value WilliGunnz/nobara-audio-installer
nai config --set-key github_token --set-value ghp_xxxxxxxxxxxx

1.3 Directory Structure
~/Documents/
├── nobara-audio-installer/     # CLI & GUI application
├── nobara-audio-content/       # Package metadata & manifests
└── nobara-audio-library/       # Original audio assets (NOT in Git)
    ├── drum-packs/
    │   └── <package-name>/     # Your packages live here
    ├── ir-packs/
    ├── midi-packs/
    ├── plugins/
    ├── presets/
    └── soundfonts/

2. Package Creation
2.1 Manual Package Structure
Every package must follow this layout:

package-name/
├── metadata.json    # Required
├── README.md        # Recommended
├── LICENSE          # Required
├── artwork/
│   └── cover.png    # Optional (512x512 recommended)
└── files/           # Package contents (WAV, SF2, presets, etc.)

2.2 metadata.json Example
{
  "id": "metal-essentials",
  "name": "Metal Essentials",
  "version": "1.0.0",
  "category": "drum-packs",
  "author": "Willi Gunnz",
  "license": "CC-BY-4.0",
  "description": "High quality metal drum samples",
  "homepage": "https://...",
  "tags": ["metal", "rock", "drums"]
}

Required Fields:

Field	Type	Description
id	string	Unique identifier (lowercase, hyphens only)
name	string	Display name
version	string	Semantic version (e.g., 1.0.0)
category	string	One of: drum-packs, ir-packs, midi-packs, plugins, presets, soundfonts
author	string	Package author name
license	string	License identifier (e.g., CC-BY-4.0)
description	string	Short description (≤140 chars)
Optional Fields:

homepage
tags
screenshots
dependencies
changelog
2.3 Using nai init-package
# Scaffold new package
nai init-package metal-essentials --category drum-packs --output ~/Documents/nobara-audio-library

This creates:

drum-packs/metal-essentials/
├── metadata.json
├── README.md
├── LICENSE
├── artwork/
└── files/

3. Testing the Package
3.1 Validate with Scanner
nai scan ~/Documents/nobara-audio-library

Expected output:

Scanning: /home/willigunnz/Documents/nobara-audio-library

✓ Found metal-essentials v1.0.0

Total packages found: 1

If a package is invalid, it will show:

✗ Invalid: package-name - Missing required file: metadata.json

3.2 Dry-Run Publish (Safe Testing)
nai publish metal-essentials --dry-run

This will:

✅ Validate metadata
✅ Create ZIP archive
✅ Calculate SHA-256 checksum
✅ Generate download URL
❌ Won't upload to GitHub
Use this before actual publishing to catch errors early.

4. Publishing to GitHub
4.1 Full Publish
nai publish metal-essentials

This will:

✅ Validate package
✅ Create ZIP archive
✅ Calculate SHA-256
✅ Upload to GitHub Releases
✅ Update packages.json in content repository
✅ Generate permanent download URL
4.2 Output Example
✓ Published: metal-essentials v1.0.0
  Archive:      metal-essentials-1.0.0.zip
  Size:         454 B
  SHA-256:     437164dbefad98c2...
  Download:    https://github.com/WilliGunnz/nobara-audio-installer/releases/download/v1.0.0/metal-essentials-1.0.0.zip

4.3 Verify in GitHub
After publishing:

Go to: https://github.com/WilliGunnz/nobara-audio-installer/releases
Check that release asset exists
Verify packages.json in nobara-audio-content repository updated
5. Installing & Verifying Packages
5.1 Install Package
nai install metal-essentials

Installs to: /home/willigunnz/.local/share/nai/packages/metal-essentials

5.2 List Installed Packages
nai list

Output:

Installed packages (1):

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ ID            ┃ Name          ┃ Version   ┃ Category   ┃      Install Date   ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ metal-essentials │ Metal Essentials │ v1.0.0 │ drum-packs │ 2026-08-16T15:30:00 │
└───────────────┴───────────────┴───────────┴────────────┴─────────────────────┘

5.3 Verify Integrity
nai verify metal-essentials

Checks:

✅ SHA-256 checksum matches published hash
✅ All files present
✅ No corruption
5.4 Uninstall
nai uninstall metal-essentials

Removes package from: /home/willigunnz/.local/share/nai/packages/

6. Project Release Workflow (Version Bump)
6.1 NAI Application Release
When updating the installer application itself (not packages):

# Bump version and create release
nai release

This:

Updates VERSION file
Generates CHANGELOG.md
Creates Git tag
Pushes to repository
Triggers GitHub Actions
6.2 Manual Alternative
# 1. Update VERSION file
echo "2.0.0" > VERSION

# 2. Update CHANGELOG
vim CHANGELOG.md

# 3. Commit and tag
git add VERSION CHANGELOG.md
git commit -m "release: v2.0.0"
git tag v2.0.0
git push origin main
git push origin v2.0.0

# 4. Create GitHub release manually or via GitHub Actions

7. Common Errors & Solutions
Error	Cause	Fix
✗ Invalid: <name> - Missing required file: metadata.json	Package folder doesn't have metadata.json	Create proper package structure
ImportError: cannot import name '...'	Missing import statement	Add from ... import ... at top of file
NameError: name 'console' is not defined	Missing Rich import	Add from rich.console import Console
ValueError: not enough values to unpack	Tuple mismatch in code	Match unpacking to actual tuple size
github_repo shows ✗ in nai doctor	Config not set	nai config --set-key github_repo --set-value WilliGunnz/nobara-audio-installer
github_token empty	No PAT configured	Create token at GitHub settings and set via config
TOMLDecodeError: Unclosed array	Invalid pyproject.toml	Check TOML syntax, balance brackets
IndentationError	Wrong whitespace in Python	Use 4 spaces per indent level (no tabs)
Scanner finds 0 packages	Scanner not recursing into category folders	See Scanner Fix below
7.1 Scanner Fix (If Not Detecting Packages)
Problem: Scanner only checks root-level folders, not inside category folders.

Fix in src/nai/cli/app.py (lines 146-163):

# OLD CODE (broken)
for item in path.iterdir():
    if item.is_dir():
        is_valid, error = validate_package_structure(item)

# NEW CODE (fixed)
valid_categories = {
    'drum-packs', 'ir-packs', 'midi-packs', 
    'plugins', 'presets', 'soundfonts'
}

for category_dir in path.iterdir():
    if category_dir.is_dir() and not category_dir.name.startswith('.'):
        if category_dir.name in valid_categories:
            for item in category_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    is_valid, error = validate_package_structure(item)
                    # ... rest of validation logic

8. Configuration Management
8.1 View Current Config
nai config --list

8.2 Get Specific Value
nai config --get github_token

8.3 Set Values
nai config --set-key <key> --set-value <value>

Example:

nai config --set-key github_user --set-value WilliGunnz
nai config --set-key library_path --set-value ~/Documents/nobara-audio-library
nai config --set-key content_path --set-value ~/Documents/nobara-audio-content

8.4 Reset to Defaults
nai config --init

9. Development Tips
9.1 Debug Mode
Add debug prints:

import logging
logging.basicConfig(level=logging.DEBUG)

9.2 Test Without Installing
# Run directly from source
cd ~/Documents/nobara-audio-installer
PYTHONPATH=src python -m nai.cli.app --help

9.3 Reinstall After Code Changes
cd ~/Documents/nobara-audio-installer
pip install -e . --force-reinstall --no-deps

9.4 Git Workflow
# Daily workflow
git add .
git commit -m "feat: description of change"
git push origin main

# Feature branch
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "feat: new feature"
git push origin feature/new-feature

# Create PR on GitHub, merge to main

10. File Locations Reference
Item	Path
NAI CLI executable	/home/willigunnz/.local/bin/nai
Configuration file	/home/willigunnz/.config/nai/config.json
Cache directory	/home/willigunnz/.local/share/nai/cache
Installed packages	/home/willigunnz/.local/share/nai/packages/
Installer source	~/Documents/nobara-audio-installer/
Content repo	~/Documents/nobara-audio-content/
Audio library	~/Documents/nobara-audio-library/
Logs	~/Documents/nobara-audio-installer/logs/
11. Related Documentation
Doc	Purpose
docs/architecture.md	System design and component overview
docs/specification.md	Package format and metadata schema
docs/packaging.md	Package building guidelines
docs/development.md	Development environment setup
docs/contributing.md	Contribution guidelines
docs/roadmap.md	Project milestones and future plans
12. Quick Copy-Paste Template
New Package Setup
# 1. Create package directory
mkdir -p ~/Documents/nobara-audio-library/drum-packs/<package-name>/{artwork,files}

# 2. Create metadata
cat > ~/Documents/nobara-audio-library/drum-packs/<package-name>/metadata.json << 'EOF'
{
  "id": "<package-name>",
  "name": "<Display Name>",
  "version": "1.0.0",
  "category": "drum-packs",
  "author": "Your Name",
  "license": "CC-BY-4.0",
  "description": "Short description"
}
EOF

# 3. Add files
# ... place audio files in files/ ...

# 4. Add README and LICENSE
touch ~/Documents/nobara-audio-library/drum-packs/<package-name>/README.md
touch ~/Documents/nobara-audio-library/drum-packs/<package-name>/LICENSE

# 5. Validate
nai scan ~/Documents/nobara-audio-library

# 6. Dry-run test
nai publish <package-name> --dry-run

# 7. Full publish
nai publish <package-name>

# 8. Verify
nai install <package-name>
nai verify <package-name>
nai list

Last Updated: 2026-08-16
Author: Willi Gunnz
License: CC-BY-4.0


---

## 📁 Save This File

bash

From your project root
cd ~/Documents/nobara-audio-installer

Create the file
nano docs/publishing-workflow.md

Paste the content above, then save (Ctrl+O) and exit (Ctrl+X)

---

## 🎯 Benefits of This Guide

| Feature | Benefit |
|---------|---------|
| Quick command reference | No need to remember exact flags |
| Troubleshooting table | Fast error resolution |
| Step-by-step workflows | Repeatable processes |
| Template section | Copy-paste ready commands |
| Location reference | Know where everything is stored |

---

Would you like me to commit this file to your repository, or make any adjustments to the content? 🔨



28 files


create the full file for me


Worked through your question
I appreciate you wanting to streamline the setup! However, I need to clarify: I don't have the ability to directly create files on your filesystem — I can only provide you with the complete content that you can copy and save.

But I can make this easier for you. Let me give you the complete file content in a ready-to-copy format, plus a quick command to create it:

📄 Complete File Content
Here's the full docs/publishing-workflow.md file content:

# Publishing Workflow Guide

**Nobara Audio Installer (NAI)** — Complete publishing reference

---

## Quick Reference Cheat Sheet

| Task | Command |
|------|---------|
| Run diagnostics | `nai doctor` |
| Scan library for packages | `nai scan ~/Documents/nobara-audio-library` |
| Create new package skeleton | `nai init-package <name> --category <cat>` |
| Test publish (no upload) | `nai publish <package> --dry-run` |
| Publish to GitHub | `nai publish <package>` |
| Install package | `nai install <package-id>` |
| List installed packages | `nai list` |
| Verify installed package | `nai verify <package-id>` |
| Uninstall package | `nai uninstall <package-id>` |
| View configuration | `nai config --list` |
| Set config value | `nai config --set-key <key> --set-value <value>` |

---

## 1. Prerequisites

### 1.1 SSH Setup for Git

bash

Verify SSH key
ssh -T git@github.com

Configure Git
git config --global user.name "WilliGunnz" git config --global user.email "your-email@example.com"

1.3 Directory Structure
3. Testing the Package
3.1 Validate with Scanner
1.2 GitHub Personal Access Token
Required for nai publish to upload releases

Create token at: https://github.com/settings/tokens
Scope: repo (Full control of private repositories)
Store securely
Configure in NAI:
nai config --set-key github_user --set-value WilliGunnz
nai config --set-key github_repo --set-value WilliGunnz/nobara-audio-installer
nai config --set-key github_token --set-value ghp_xxxxxxxxxxxx

1.3 Directory Structure
~/Documents/
├── nobara-audio-installer/     # CLI & GUI application
├── nobara-audio-content/       # Package metadata & manifests
└── nobara-audio-library/       # Original audio assets (NOT in Git)
    ├── drum-packs/
    │   └── <package-name>/     # Your packages live here
    ├── ir-packs/
    ├── midi-packs/
    ├── plugins/
    ├── presets/
    └── soundfonts/

2. Package Creation
2.1 Manual Package Structure
Every package must follow this layout:

package-name/
├── metadata.json    # Required
├── README.md        # Recommended
├── LICENSE          # Required
├── artwork/
│   └── cover.png    # Optional (512x512 recommended)
└── files/           # Package contents (WAV, SF2, presets, etc.)

2.2 metadata.json Example
{
  "id": "metal-essentials",
  "name": "Metal Essentials",
  "version": "1.0.0",
  "category": "drum-packs",
  "author": "Willi Gunnz",
  "license": "CC-BY-4.0",
  "description": "High quality metal drum samples",
  "homepage": "https://...",
  "tags": ["metal", "rock", "drums"]
}

Required Fields:

Field	Type	Description
id	string	Unique identifier (lowercase, hyphens only)
name	string	Display name
version	string	Semantic version (e.g., 1.0.0)
category	string	One of: drum-packs, ir-packs, midi-packs, plugins, presets, soundfonts
author	string	Package author name
license	string	License identifier (e.g., CC-BY-4.0)
description	string	Short description (≤140 chars)
Optional Fields:

homepage
tags
screenshots
dependencies
changelog
2.3 Using nai init-package
# Scaffold new package
nai init-package metal-essentials --category drum-packs --output ~/Documents/nobara-audio-library

This creates:

drum-packs/metal-essentials/
├── metadata.json
├── README.md
├── LICENSE
├── artwork/
└── files/

3. Testing the Package
3.1 Validate with Scanner
nai scan ~/Documents/nobara-audio-library

Expected output:

Scanning: /home/willigunnz/Documents/nobara-audio-library

✓ Found metal-essentials v1.0.0

Total packages found: 1

If a package is invalid, it will show:

✗ Invalid: package-name - Missing required file: metadata.json

3.2 Dry-Run Publish (Safe Testing)
nai publish metal-essentials --dry-run

This will:

✅ Validate metadata
✅ Create ZIP archive
✅ Calculate SHA-256 checksum
✅ Generate download URL
❌ Won't upload to GitHub
Use this before actual publishing to catch errors early.

4. Publishing to GitHub
4.1 Full Publish
nai publish metal-essentials

This will:

✅ Validate package
✅ Create ZIP archive
✅ Calculate SHA-256
✅ Upload to GitHub Releases
✅ Update packages.json in content repository
✅ Generate permanent download URL
4.2 Output Example
✓ Published: metal-essentials v1.0.0
  Archive:      metal-essentials-1.0.0.zip
  Size:         454 B
  SHA-256:     437164dbefad98c2...
  Download:    https://github.com/WilliGunnz/nobara-audio-installer/releases/download/v1.0.0/metal-essentials-1.0.0.zip

4.3 Verify in GitHub
After publishing:

Go to: https://github.com/WilliGunnz/nobara-audio-installer/releases
Check that release asset exists
Verify packages.json in nobara-audio-content repository updated
5. Installing & Verifying Packages
5.1 Install Package
nai install metal-essentials

Installs to: /home/willigunnz/.local/share/nai/packages/metal-essentials

5.2 List Installed Packages
nai list

Output:

Installed packages (1):

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ ID            ┃ Name          ┃ Version   ┃ Category   ┃      Install Date   ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ metal-essentials │ Metal Essentials │ v1.0.0 │ drum-packs │ 2026-08-16T15:30:00 │
└───────────────┴───────────────┴───────────┴────────────┴─────────────────────┘

5.3 Verify Integrity
nai verify metal-essentials

Checks:

✅ SHA-256 checksum matches published hash
✅ All files present
✅ No corruption
5.4 Uninstall
nai uninstall metal-essentials

Removes package from: /home/willigunnz/.local/share/nai/packages/

6. Project Release Workflow (Version Bump)
6.1 NAI Application Release
When updating the installer application itself (not packages):

# Bump version and create release
nai release

This:

Updates VERSION file
Generates CHANGELOG.md
Creates Git tag
Pushes to repository
Triggers GitHub Actions
6.2 Manual Alternative
# 1. Update VERSION file
echo "2.0.0" > VERSION

# 2. Update CHANGELOG
vim CHANGELOG.md

# 3. Commit and tag
git add VERSION CHANGELOG.md
git commit -m "release: v2.0.0"
git tag v2.0.0
git push origin main
git push origin v2.0.0

# 4. Create GitHub release manually or via GitHub Actions

7. Common Errors & Solutions
Error	Cause	Fix
✗ Invalid: <name> - Missing required file: metadata.json	Package folder doesn't have metadata.json	Create proper package structure
ImportError: cannot import name '...'	Missing import statement	Add from ... import ... at top of file
NameError: name 'console' is not defined	Missing Rich import	Add from rich.console import Console
ValueError: not enough values to unpack	Tuple mismatch in code	Match unpacking to actual tuple size
github_repo shows ✗ in nai doctor	Config not set	nai config --set-key github_repo --set-value WilliGunnz/nobara-audio-installer
github_token empty	No PAT configured	Create token at GitHub settings and set via config
TOMLDecodeError: Unclosed array	Invalid pyproject.toml	Check TOML syntax, balance brackets
IndentationError	Wrong whitespace in Python	Use 4 spaces per indent level (no tabs)
Scanner finds 0 packages	Scanner not recursing into category folders	See Scanner Fix below
7.1 Scanner Fix (If Not Detecting Packages)
Problem: Scanner only checks root-level folders, not inside category folders.

Fix in src/nai/cli/app.py (lines 146-163):

# OLD CODE (broken)
for item in path.iterdir():
    if item.is_dir():
        is_valid, error = validate_package_structure(item)

# NEW CODE (fixed)
valid_categories = {
    'drum-packs', 'ir-packs', 'midi-packs', 
    'plugins', 'presets', 'soundfonts'
}

for category_dir in path.iterdir():
    if category_dir.is_dir() and not category_dir.name.startswith('.'):
        if category_dir.name in valid_categories:
            for item in category_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    is_valid, error = validate_package_structure(item)
                    # ... rest of validation logic

8. Configuration Management
8.1 View Current Config
nai config --list

8.2 Get Specific Value
nai config --get github_token

8.3 Set Values
nai config --set-key <key> --set-value <value>

Example:

nai config --set-key github_user --set-value WilliGunnz
nai config --set-key library_path --set-value ~/Documents/nobara-audio-library
nai config --set-key content_path --set-value ~/Documents/nobara-audio-content

8.4 Reset to Defaults
nai config --init

9. Development Tips
9.1 Debug Mode
Add debug prints:

import logging
logging.basicConfig(level=logging.DEBUG)

9.2 Test Without Installing
# Run directly from source
cd ~/Documents/nobara-audio-installer
PYTHONPATH=src python -m nai.cli.app --help

9.3 Reinstall After Code Changes
cd ~/Documents/nobara-audio-installer
pip install -e . --force-reinstall --no-deps

9.4 Git Workflow
# Daily workflow
git add .
git commit -m "feat: description of change"
git push origin main

# Feature branch
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "feat: new feature"
git push origin feature/new-feature

# Create PR on GitHub, merge to main

10. File Locations Reference
Item	Path
NAI CLI executable	/home/willigunnz/.local/bin/nai
Configuration file	/home/willigunnz/.config/nai/config.json
Cache directory	/home/willigunnz/.local/share/nai/cache
Installed packages	/home/willigunnz/.local/share/nai/packages/
Installer source	~/Documents/nobara-audio-installer/
Content repo	~/Documents/nobara-audio-content/
Audio library	~/Documents/nobara-audio-library/
Logs	~/Documents/nobara-audio-installer/logs/
11. Related Documentation
Doc	Purpose
docs/architecture.md	System design and component overview
docs/specification.md	Package format and metadata schema
docs/packaging.md	Package building guidelines
docs/development.md	Development environment setup
docs/contributing.md	Contribution guidelines
docs/roadmap.md	Project milestones and future plans
12. Quick Copy-Paste Template
New Package Setup
# 1. Create package directory
mkdir -p ~/Documents/nobara-audio-library/drum-packs/<package-name>/{artwork,files}

# 2. Create metadata
cat > ~/Documents/nobara-audio-library/drum-packs/<package-name>/metadata.json << 'EOF'
{
  "id": "<package-name>",
  "name": "<Display Name>",
  "version": "1.0.0",
  "category": "drum-packs",
  "author": "Your Name",
  "license": "CC-BY-4.0",
  "description": "Short description"
}
EOF

# 3. Add files
# ... place audio files in files/ ...

# 4. Add README and LICENSE
touch ~/Documents/nobara-audio-library/drum-packs/<package-name>/README.md
touch ~/Documents/nobara-audio-library/drum-packs/<package-name>/LICENSE

# 5. Validate
nai scan ~/Documents/nobara-audio-library

# 6. Dry-run test
nai publish <package-name> --dry-run

# 7. Full publish
nai publish <package-name>

# 8. Verify
nai install <package-name>
nai verify <package-name>
nai list

Last Updated: 2026-08-16
Author: Willi Gunnz
License: CC-BY-4.0


---

## 🚀 Create It With One Command

Copy this entire command and paste it into your terminal:

bash cd ~/Documents/nobara-audio-installer && cat > docs/publishing-workflow.md << 'ENDOFGUIDE'

Publishing Workflow Guide
Nobara Audio Installer (NAI) — Complete publishing reference

Quick Reference Cheat Sheet
Task	Command
Run diagnostics	nai doctor
Scan library for packages	nai scan ~/Documents/nobara-audio-library
Create new package skeleton	nai init-package <name> --category <cat>
Test publish (no upload)	nai publish <package> --dry-run
Publish to GitHub	nai publish <package>
Install package	nai install <package-id>
List installed packages	nai list
Verify installed package	nai verify <package-id>
Uninstall package	nai uninstall <package-id>
View configuration	nai config --list
Set config value	nai config --set-key <key> --set-value <value>
1. Prerequisites
1.1 SSH Setup for Git
ssh -T git@github.com
git config --global user.name "WilliGunnz"
git config --global user.email "your-email@example.com"

1.2 GitHub Personal Access Token
Create token at: https://github.com/settings/tokens
Scope: repo
Configure in NAI:
nai config --set-key github_user --set-value WilliGunnz
nai config --set-key github_repo --set-value WilliGunnz/nobara-audio-installer
nai config --set-key github_token --set-value ghp_xxxxxxxxxxxx

1.3 Directory Structure
~/Documents/
├── nobara-audio-installer/
├── nobara-audio-content/
└── nobara-audio-library/
    ├── drum-packs/
    │   └── <package-name>/
    ├── ir-packs/
    ├── midi-packs/
    ├── plugins/
    ├── presets/
    └── soundfonts/

2. Package Creation
2.1 Manual Package Structure
package-name/
├── metadata.json
├── README.md
├── LICENSE
├── artwork/
│   └── cover.png
└── files/

2.2 Required metadata.json Fields
Field	Description
id	Unique identifier (lowercase, hyphens)
name	Display name
version	Semantic version
category	drum-packs, ir-packs, midi-packs, plugins, presets, or soundfonts
author	Package author
license	License identifier
description	Short description
2.3 Using nai init-package
nai init-package <name> --category <category> --output ~/Documents/nobara-audio-library

3. Testing the Package
3.1 Validate with Scanner
nai scan ~/Documents/nobara-audio-library

3.2 Dry-Run Publish
nai publish <package> --dry-run

4. Publishing to GitHub
4.1 Full Publish
nai publish <package>

4.2 Verify in GitHub
Visit: https://github.com/WilliGunnz/nobara-audio-installer/releases

5. Installing & Verifying Packages
5.1 Install
nai install <package-id>

5.2 List
nai list

5.3 Verify
nai verify <package-id>

5.4 Uninstall
nai uninstall <package-id>

6. Project Release Workflow
nai release

Or manually:

echo "2.0.0" > VERSION
git add VERSION CHANGELOG.md
git commit -m "release: v2.0.0"
git tag v2.0.0
git push origin main
git push origin v2.0.0

7. Common Errors & Solutions
Error	Fix
Missing metadata.json	Create proper package structure
ImportError	Add missing import statement
github_repo shows ✗	nai config --set-key github_repo --set-value WilliGunnz/nobara-audio-installer
Scanner finds 0 packages	See Scanner Fix below
7.1 Scanner Fix
File: src/nai/cli/app.py

Add valid_categories check to iterate inside category folders.

8. Configuration Management
nai config --list
nai config --get <key>
nai config --set-key <key> --set-value <value>
nai config --init

9. File Locations
Item	Path
NAI CLI	/home/willigunnz/.local/bin/nai
Configuration	/home/willigunnz/.config/nai/config.json
Installed packages	/home/willigunnz/.local/share/nai/packages/
Source	~/Documents/nobara-audio-installer/
Library	~/Documents/nobara-audio-library/
10. Quick Package Template
mkdir -p ~/Documents/nobara-audio-library/drum-packs/<package-name>/{artwork,files}
cat > ~/Documents/nobara-audio-library/drum-packs/<package-name>/metadata.json << 'EOF'
{
  "id": "<package-name>",
  "name": "<Display Name>",
  "version": "1.0.0",
  "category": "drum-packs",
  "author": "Willi Gunnz",
  "license": "CC-BY-4.0",
  "description": "Description"
}
EOF
touch README.md LICENSE
nai scan ~/Documents/nobara-audio-library
nai publish <package-name> --dry-run
nai publish <package-name>

Last Updated: 2026-08-16
Author: Willi Gunnz
License: CC-BY-4.0 ENDOFGUIDE

