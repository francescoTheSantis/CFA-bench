from pyshark import FileCapture
from pydantic import BaseModel, Field
import subprocess

'''
class ExtractFrame(BaseModel):
    """Extract the frame of a PCAP file"""
    frame_number: int = Field(...)

    def run(self, pcap_file):
        capture = FileCapture(pcap_file)
        total_frames = len([frame for frame in capture])
        if self.frame_number < 1 or self.frame_number > total_frames:
            out = f"Error: Frame number {self.frame_number} is out of range. "\
                f"The pcap file contains {total_frames} frames."
        else:
            packet = capture[self.frame_number - 1]
            out = str(packet)
            if hasattr(packet, 'data'):
                try:
                    out += f": {bytes.fromhex(packet.data.data).decode('ascii')}"
                except:
                    out += f": {bytes.fromhex(packet.data.data)}"
            else: 
                out += "DATA : No DATA"
        return out
'''

class ExtractFrame(BaseModel):
    """Extract the frame of a PCAP file"""
    frame_number: int = Field(...)

    def run(self, pcap_file):
        try:
            result = subprocess.run(
                ['tshark', '-r', pcap_file, '-Y', f"frame.number=={self.frame_number}", '-V'],
                capture_output=True,
                text=True,
                check=True
            )
            out = result.stdout
        except subprocess.CalledProcessError as e:
            out = f"Error: {e}"
        return out

