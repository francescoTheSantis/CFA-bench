from scapy.all import rdpcap
import os
from dotenv import load_dotenv
load_dotenv()

# Set environment variables for project and scripts directories
PROJECT = os.environ.get("PROJECT")


class ForensicDriver():
    def __init__(self, game, llm, query_strategy):
        self.game = game
        
        event_pcap_files = [f for f in os.listdir(f'data/raw/eventID_{self.game['event']}') if f.endswith('.pcap')]
        if event_pcap_files:
            self.pcap_file = os.path.join(f'data/raw/eventID_{self.game['event']}', event_pcap_files[0])
        else:
            raise FileNotFoundError(f"No .pcap file found for eventID_{self.game['event']}")   

        event_log_files = [f for f in os.listdir(f'data/raw/eventID_{self.game['event']}') if f.endswith('.log')]
        if event_log_files:
            self.log_file = [os.path.join(f'data/raw/eventID_{self.game['event']}', x) for x in event_pcap_files]
        else:
            raise FileNotFoundError(f"No .pcap file found for eventID_{self.game['event']}")  

        #self.pcap_file = f"data/raw/CVE-{self.game['cve']}.pcap"
        #self.log_file = f"{PROJECT}/data/raw/CVE-{self.game['cve']}.log"
        self.llm = llm
        self.query_strategy = query_strategy

    def reset(self, task: str):
        packets = rdpcap(self.pcap_file)
        pkt_len = len(packets)
        obs = f'{task}\nThe current PCAP file has {pkt_len} packets (frames)'
        out = [f"Frame {i+1}: {pkt.summary()}" for i,
               pkt in enumerate(packets)]
        out = '\n'.join(out)
        obs = f'{obs}\n{out}'
        return obs, False

    def step(self, tool):
        """Executes a step of the pentest based on the provided tool.

        Args:
            tool: The tool to be executed.

        Returns:
            tuple: The output from the tool execution and a boolean indicating 
            if the pentest is done.
        """
        done = False

        if tool.__class__.__name__ in ['ListFrames', 'ExtractFrame', 'ExpandFrame', 'ExpandFrameData']:
            observation = tool.run(self.pcap_file)
        elif tool.__class__.__name__ == 'ReadLogFile':
            observation = tool.run(self.log_file)
        elif tool.__class__.__name__ in ['CVEDescriptor', 'GetCVEList']:
            observation = tool.run()
        elif tool.__class__.__name__ == 'WebQuickSearch':
            observation = tool.run(self.llm, self.query_strategy)
        elif tool.__class__.__name__ in ['FinalReport']:
            observation = tool.run()
            done = True
        elif tool.__class__.__name__ in ['FinalAnswer']:
            if 'CVE' not in tool.cve_identifier:
                tool.cve_identifier = f'CVE-{tool.cve_identifier}'
            if tool.cve_identifier == f'CVE-{self.game["cve"]}':
                observation = 'You Won!'
                done = True
            else:
                observation = 'Wrong CVE. Try again.'

        return observation, done
