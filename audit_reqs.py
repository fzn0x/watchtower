import os
import re
import glob

def get_all_imports(directory):
    imports = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Match "import package" or "from package import ..."
                    matches = re.findall(r"^(?:import|from)\s+([a-zA-Z0-9_]+)", content, re.MULTILINE)
                    for m in matches:
                        imports.add(m)
    return imports

watchtower_imports = get_all_imports("watchtower")
print("Found imports in watchtower directory:")
for imp in sorted(watchtower_imports):
    if imp != "watchtower":
        print(f"- {imp}")

with open("requirements.txt", "r") as f:
    reqs = f.read().lower()

missing = []
for imp in watchtower_imports:
    # Basic check - might need more mapping for complex package names
    if imp in ["os", "json", "argparse", "logging", "shutil", "importlib", "urllib", "re", "operator", "typing", "sys", "glob"]:
        continue
    
    # Mapping common imports to requirements
    check_name = imp.lower()
    if check_name == "pydantic":
        pass
    elif check_name == "sqlalchemy":
        pass
    elif check_name == "fpdf":
        check_name = "fpdf2"
    elif check_name == "dotenv":
        check_name = "python-dotenv"
    elif check_name.startswith("langchain"):
        check_name = "langchain"
    elif check_name == "langgraph":
        pass
    elif check_name == "requests":
        pass
    
    if check_name not in reqs:
        missing.append(imp)

if missing:
    print("\nLikely missing from requirements.txt:")
    for m in missing:
        print(f"- {m}")
else:
    print("\nNo obvious missing requirements found.")
