from pydantic import BaseModel, Field
import subprocess
    
class ExpandFrameData(BaseModel):
    """Show the payload contained in a frame."""
    frame_number: int = Field(...)

    def run(self, pcap_file):
        try:
            result = subprocess.run(
                ['tshark', '-r', pcap_file, '-Y', f"frame.number=={self.frame_number}", '-T', 'fields', '-e', 'data'],
                capture_output=True,
                text=True,
                check=True
            )
            out = result.stdout
        except subprocess.CalledProcessError as e:
            out = f"Error: {e}"
        if len(out)==0:
            out = "The frame does not contain DATA."
        return out