# PythonAnywhere Setup Instructions

## Installing Packages on PythonAnywhere

PythonAnywhere can be tricky with package installation. Follow these steps:

### Step 1: Check Your Python Version

In the PythonAnywhere **Bash console**, run:
```bash
python3 --version
# or
python3.10 --version
# or
python3.11 --version
```

### Step 2: Install Using the Correct pip Command

**For Python 3.10:**
```bash
pip3.10 install --user assemblyai python-dotenv
```

**For Python 3.11:**
```bash
pip3.11 install --user assemblyai python-dotenv
```

**For Python 3.9:**
```bash
pip3.9 install --user assemblyai python-dotenv
```

**Or install all requirements:**
```bash
pip3.10 install --user -r requirements.txt
```

### Step 3: Verify Installation

In the PythonAnywhere **Python console** (matching your web app's Python version), test:
```python
import assemblyai
print(assemblyai.__version__)
```

### Step 4: If Still Not Working - Check Web App Settings

1. Go to **Web** tab in PythonAnywhere
2. Click on your web app
3. Check the **Python version** (e.g., Python 3.10, 3.11)
4. Make sure you're installing packages for that **exact version**

### Step 5: Alternative - Install in Virtual Environment

If you're using a virtual environment:

1. **Activate your virtual environment:**
```bash
source /home/yourusername/.virtualenvs/yourvenv/bin/activate
```

2. **Install packages:**
```bash
pip install assemblyai python-dotenv
```

3. **Make sure your web app is configured to use this virtual environment** in the Web tab.

### Step 6: Reload Your Web App

After installing packages:
1. Go to **Web** tab
2. Click the green **Reload** button for your web app

### Common Issues and Solutions

#### Issue: "No module named 'assemblyai'" after installation

**Solution 1:** Make sure you're using the correct Python version
```bash
# Check which Python your web app uses
# Then install with matching pip version
pip3.10 install --user assemblyai
```

**Solution 2:** Check if package is installed
```bash
pip3.10 list | grep assemblyai
```

**Solution 3:** Add to PYTHONPATH (if needed)
In your web app's WSGI file, you might need to add:
```python
import sys
sys.path.insert(0, '/home/yourusername/.local/lib/python3.10/site-packages')
```

#### Issue: ImportError in web app but works in console

This usually means:
- Web app is using a different Python version than console
- Web app is using a virtual environment that doesn't have the package
- Package was installed for a different user

**Solution:** Install in the same environment your web app uses.

### Quick Test Script

Create a test file to verify everything works:

```python
# test_assemblyai.py
try:
    import assemblyai as aai
    print(f"✅ AssemblyAI imported successfully! Version: {aai.__version__}")
except ImportError as e:
    print(f"❌ Failed to import AssemblyAI: {e}")
    print("Run: pip3.10 install --user assemblyai")
```

Run it in your PythonAnywhere console:
```bash
python3.10 test_assemblyai.py
```

### Environment Variables Setup

1. Create a `.env` file in your project root:
```bash
cd /home/yourusername/path/to/your/project
nano .env
```

2. Add your AssemblyAI API key:
```
ASSEMBLYAI_API_KEY=key
```

3. Make sure `python-dotenv` is installed (it's in requirements.txt now)

### Final Checklist

- [ ] Installed `assemblyai` with correct pip version (pip3.10, pip3.11, etc.)
- [ ] Installed `python-dotenv` 
- [ ] Verified import works in Python console matching your web app version
- [ ] Created `.env` file with `ASSEMBLYAI_API_KEY`
- [ ] Reloaded your web app
- [ ] Checked error logs in PythonAnywhere dashboard

### Still Having Issues?

1. **Check the error logs:**
   - Go to **Web** tab → Click your web app → **Error log** link
   - Look for the full traceback

2. **Check server logs:**
   - Go to **Tasks** tab → Check any scheduled tasks or background processes

3. **Verify Python version match:**
   - Web app Python version = Console Python version = pip version used

If you're still stuck, share:
- Your Python version (from web app settings)
- The exact error message from the error log
- Output of `pip3.10 list | grep assemblyai` (or matching version)

