from pydantic import BaseModel

class ReadLogFile(BaseModel):
    """Read the log file"""

    def run(self, log_file_paths):
        try:
            content = ""
            for log_file_path in log_file_paths:
                with open(log_file_path, 'r', encoding="utf-8", errors="replace") as file:
                    content = file.read()
                content += "\n\n"
        except Exception as e:
            content = f"Error: {e}"
        return content