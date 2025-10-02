import os
import subprocess

var_name = "BOT_TOKEN"

# Run a subprocess and capture its env for this var
result = subprocess.run(
    ["python", "-c", f"import os; print(os.environ.get('{var_name}', 'NOT SET'))"],
    capture_output=True,
    text=True,
    env=os.environ  # Inherits your current env
)
print(f"Subprocess sees {var_name}: {result.stdout.strip()}")