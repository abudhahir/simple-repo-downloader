# Installation Guide

Complete guide to installing Simple Repository Downloader on various platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
  - [Quick Install (Recommended)](#quick-install-recommended)
  - [Install from Source](#install-from-source)
  - [Development Installation](#development-installation)
  - [Install from PyPI](#install-from-pypi-coming-soon)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [Verify Installation](#verify-installation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before installing, ensure you have:

### 1. Python 3.10 or Higher

**Check your Python version:**
```bash
python3 --version
```

If you need to install or upgrade Python:

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

**macOS (using Homebrew):**
```bash
brew install python@3.10
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

### 2. Git

**Check if Git is installed:**
```bash
git --version
```

**Install Git:**

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install git
```

**macOS:**
```bash
brew install git
```

**Windows:**
Download from [git-scm.com](https://git-scm.com/download/win)

### 3. pip (Python Package Installer)

Usually comes with Python, but verify:
```bash
python3 -m pip --version
```

If missing:
```bash
python3 -m ensurepip --upgrade
```

## Installation Methods

### Quick Install (Recommended)

This is the fastest way to get started:

```bash
# 1. Clone the repository
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

# 2. Create virtual environment (recommended)
python3 -m venv venv

# 3. Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install the package
pip install -e .

# 5. Verify installation
repo-dl --version
```

**Why use a virtual environment?**
- Keeps dependencies isolated
- Prevents conflicts with other Python packages
- Easy to remove (just delete the `venv` folder)

### Install from Source

Detailed step-by-step installation:

#### Step 1: Clone the Repository

```bash
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader
```

#### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
```

This creates a `venv` directory containing a Python installation.

#### Step 3: Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

Your prompt should change to show `(venv)`.

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Note:** On Windows, you may need to enable script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

The `-e` flag installs in "editable" mode, useful for development.

#### Step 5: Verify Installation

```bash
repo-dl --help
```

You should see the help message.

### Development Installation

For contributors or if you want to run tests:

```bash
# Clone repository
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install with development dependencies
pip install -e ".[dev]"

# Run tests to verify
pytest

# Run with coverage
pytest --cov=simple_repo_downloader
```

**Development dependencies include:**
- pytest - Testing framework
- pytest-asyncio - Async test support
- pytest-cov - Coverage reporting
- black - Code formatter
- ruff - Linter
- mypy - Type checker
- aioresponses - Mock aiohttp responses

### Install from PyPI (Coming Soon)

Once published to PyPI:

```bash
pip install simple-repo-downloader
```

## Platform-Specific Instructions

### Linux

**Ubuntu/Debian:**
```bash
# Install prerequisites
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip git

# Clone and install
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Verify
repo-dl --help
```

**Fedora/RHEL:**
```bash
# Install prerequisites
sudo dnf install python3.10 python3-pip git

# Clone and install
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**Arch Linux:**
```bash
# Install prerequisites
sudo pacman -S python python-pip git

# Clone and install
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader
python -m venv venv
source venv/bin/activate
pip install -e .
```

### macOS

**Using Homebrew (recommended):**
```bash
# Install prerequisites
brew install python@3.10 git

# Clone and install
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Verify
repo-dl --help
```

**Without Homebrew:**
1. Install Python from [python.org](https://www.python.org/downloads/macos/)
2. Install Git from [git-scm.com](https://git-scm.com/download/mac)
3. Follow the standard installation steps

### Windows

**Using Command Prompt:**
```cmd
:: Install Git and Python first from official websites

:: Clone repository
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

:: Create virtual environment
python -m venv venv

:: Activate virtual environment
venv\Scripts\activate.bat

:: Install
pip install -e .

:: Verify
repo-dl --help
```

**Using PowerShell:**
```powershell
# Clone repository
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

# Create virtual environment
python -m venv venv

# Enable script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate virtual environment
venv\Scripts\Activate.ps1

# Install
pip install -e .

# Verify
repo-dl --help
```

**Using WSL (Windows Subsystem for Linux):**

Follow the Linux instructions after setting up WSL.

## Verify Installation

After installation, verify everything works:

### 1. Check Command Availability

```bash
repo-dl --help
```

Expected output:
```
Usage: repo-dl [OPTIONS] COMMAND [ARGS]...

  Simple Repository Downloader - Download all repos from GitHub/GitLab users.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  download  Download repositories from a platform user/org.
```

### 2. Check Version

```bash
repo-dl --version
```

Expected: `repo-dl, version 0.1.0`

### 3. Test with a Small Download

```bash
# Download a small public repository
repo-dl download github octocat
```

This should create `./repos/github/octocat/` with repositories.

### 4. Run Tests (if installed with dev dependencies)

```bash
pytest
```

Expected: All tests should pass.

## Troubleshooting

### Command Not Found: `repo-dl`

**Problem:**
```bash
repo-dl: command not found
```

**Solutions:**

1. **Virtual environment not activated:**
   ```bash
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Not installed correctly:**
   ```bash
   pip install -e .
   ```

3. **Use Python module directly:**
   ```bash
   python -m simple_repo_downloader.cli download github octocat
   ```

### Permission Denied

**Problem:**
```bash
Permission denied: '/usr/local/lib/python3.10/...'
```

**Solution:**
Use a virtual environment (recommended) or install with `--user`:
```bash
pip install --user -e .
```

### Python Version Too Old

**Problem:**
```
Python 3.9 is not supported
```

**Solution:**
Install Python 3.10 or higher:
```bash
# Ubuntu/Debian
sudo apt install python3.10

# macOS
brew install python@3.10

# Or download from python.org
```

### pip Not Found

**Problem:**
```bash
pip: command not found
```

**Solution:**
```bash
python3 -m ensurepip --upgrade
# or
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### Git Not Found

**Problem:**
```bash
git: command not found
```

**Solution:**

**Linux:**
```bash
sudo apt install git  # Ubuntu/Debian
sudo dnf install git  # Fedora
```

**macOS:**
```bash
brew install git
# or install Xcode Command Line Tools:
xcode-select --install
```

**Windows:**
Download from [git-scm.com](https://git-scm.com/download/win)

### Virtual Environment Activation Fails on Windows

**Problem:**
```
cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Module Import Errors

**Problem:**
```python
ModuleNotFoundError: No module named 'aiohttp'
```

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -e .
```

## Uninstalling

### Remove Package

```bash
pip uninstall simple-repo-downloader
```

### Remove Virtual Environment

```bash
# Deactivate first
deactivate

# Delete the venv directory
rm -rf venv  # Linux/macOS
# or
rmdir /s venv  # Windows
```

### Remove Repository

```bash
cd ..
rm -rf simple-repo-downloader
```

## Next Steps

After installation:

1. Read the [Quick Start Guide](QUICKSTART.md)
2. See [CLI Usage Examples](docs/examples/cli-usage.md)
3. Set up [Authentication](README.md#authentication)
4. Try downloading some repositories!

## Getting Help

If you encounter issues:

1. Check this troubleshooting section
2. Review the [README](README.md)
3. Open an issue on [GitHub](https://github.com/abudhahir/simple-repo-downloader/issues)
4. Include:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce

---

**Installation complete!** 🎉 Ready to download repositories.
