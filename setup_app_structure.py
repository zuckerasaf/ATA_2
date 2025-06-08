import os
import json

# Load config.json
config_path = os.path.join('src', 'utils', 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

paths = config['paths']

# Create DB directory and subdirectories
db_path = paths['db_path']
test_path = paths['test_path']
result_path = paths['result_path']
run_log_path = paths['run_log_path']

# Ensure all directories exist
os.makedirs(db_path, exist_ok=True)
os.makedirs(test_path, exist_ok=True)
os.makedirs(result_path, exist_ok=True)

# Ensure run_log.txt exists
if not os.path.exists(run_log_path):
    with open(run_log_path, 'w') as f:
        f.write('')

print("Application folder structure has been set up successfully.")