---
inclusion: always
---

# Python Execution Requirements for DeathStrandsing Project

## CRITICAL: All Python commands MUST be executed in WSL environment

This project runs in a Windows environment but ALL Python code execution, testing, and package management MUST be done through WSL (Windows Subsystem for Linux).

### Required Command Format

**ALWAYS use this exact pattern for Python commands:**

```bash
wsl bash -c "source venv/bin/activate && python3 [your-command-here]"
```

### Specific Examples

#### Running Tests
```bash
# Correct ✅
wsl bash -c "source venv/bin/activate && python3 -m pytest tests/unit/test_file.py -v"

# Wrong ❌ - Never use these
python -m pytest tests/unit/test_file.py -v
pytest tests/unit/test_file.py -v
wsl python3 -m pytest tests/unit/test_file.py -v
```

#### Installing Packages
```bash
# Correct ✅
wsl bash -c "source venv/bin/activate && pip install package-name"

# Wrong ❌
pip install package-name
wsl pip install package-name
```

#### Running Python Scripts
```bash
# Correct ✅
wsl bash -c "source venv/bin/activate && python3 script.py"

# Wrong ❌
python script.py
wsl python3 script.py
```

### Why This Matters

1. **Virtual Environment**: The project uses a Python virtual environment located at `venv/` that must be activated
2. **WSL Environment**: The project is configured to run in WSL, not native Windows Python
3. **Python Version**: Must use `python3` explicitly, not just `python`
4. **Dependencies**: All project dependencies are installed in the WSL virtual environment

### Before Running ANY Python Command

1. ✅ Check if you're using WSL: `wsl bash -c`
2. ✅ Check if you're activating venv: `source venv/bin/activate`
3. ✅ Check if you're using python3: `python3`

### Common Mistakes to Avoid

- Running pytest directly without WSL
- Using `python` instead of `python3`
- Forgetting to activate the virtual environment
- Running commands in Windows PowerShell instead of WSL

### If You Forget This Pattern

If you run a Python command and get "No module named pytest" or similar errors, you've likely forgotten to use the WSL + venv pattern. Always go back and use the correct format.

**Remember: EVERY SINGLE Python command in this project must follow the WSL + venv pattern.**