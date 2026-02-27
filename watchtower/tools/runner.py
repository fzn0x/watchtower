import subprocess
import logging

def run_cli_tool(command: list[str], timeout: int = 300, auth_metadata: dict = None) -> str:
    try:
        # Inject auth headers/cookies if provided (implementation varies per tool, 
        # but runner provides the logic for common patterns)
        if auth_metadata:
            for key, val in auth_metadata.items():
                if "httpx" in command[0] or "curl" in command[0]:
                    command.extend(["-H", f"{key}: {val}"])
                elif "sqlmap" in command[0]:
                    if key.lower() == "cookie":
                        command.extend(["--cookie", val])
                    else:
                        command.extend(["--headers", f"{key}: {val}"])

        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = stdout
        if stderr:
            output += f"\nStderr: {stderr}"

        if len(output) > 5000:
            # Smart Truncation: Prioritize lines with security keywords
            keywords = ["vulnerability", "critical", "[+]", "finding", "exposed", "error", "warning"]
            lines = output.splitlines()
            important_lines = [l for l in lines if any(k in l.lower() for k in keywords)]
            
            if len(important_lines) > 20:
                truncated = "\n".join(important_lines[:50]) + "\n...[TRUNCATED - Showing Important Hits Only]"
            else:
                truncated = output[:2500] + "\n...[TRUNCATED MIDDLE]...\n" + output[-2500:]
            
            return truncated
            
        return output
    except Exception as e:
        return f"Error executing tool: {e}"
