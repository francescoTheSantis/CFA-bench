from pydantic import BaseModel

class ReadLogFile(BaseModel):
    """Read the log file"""

    def run(self, log_file_path):
        try:
            with open(log_file_path, 'r') as file:
                content = file.read()
        except Exception as e:
            content = f"Error: {e}"
        return content