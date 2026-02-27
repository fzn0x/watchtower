import subprocess
import logging

def run_cli_tool(command: list[str], timeout: int = 300) -> str:
    try:
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        output = result.stdout
        if result.stderr:
            output += f"\nStderr: {result.stderr}"
        if len(output) > 5000:
            output = output[:5000] + "\n...[TRUNCATED]"
        return output
    except Exception as e:
        return f"Error executing tool: {e}"
