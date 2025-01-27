from termcolor import cprint
from ai4ensic.utils import load_data
from ai4ensic.driver import ForensicDriver
from ai4ensic.prompts import INSTRUCTION_TEMPLATE
from ai4ensic.agent import SummariseReActAgent
from ai4ensic.working_memory import ReActScratchpad
from ai4ensic.llm import LLMClient
from ai4ensic.tools.report import FinalAnswer
from ai4ensic.tools.pcap import ExtractFrame
from ai4ensic.tools.cve import CVEDescriptor, WebQuickSearch
import os
from dotenv import load_dotenv
load_dotenv()

# Set environment variables for project and scripts directories
OPENAI_KEY = os.environ.get("OPENAIKEY")

# Initialize the Tools
tools = [ExtractFrame, WebQuickSearch, CVEDescriptor, FinalAnswer]

# Initialize LLM
llm = LLMClient(api_key=OPENAI_KEY, model='gpt-4o')

# Initialize the WorkingMemory
working_memory = ReActScratchpad()

# Initialize the Agent
agent = SummariseReActAgent(
    prompt_template=INSTRUCTION_TEMPLATE,
    llm=llm,
    working_memory=working_memory,
    tools=tools,
    logpath=''
)


pcaps = load_data()  # Load the games
game = pcaps[0]  # Get the first task

# Initialize driver
driver = ForensicDriver(game=game)

# The task assigned to the agent
task = '''Analyze a PCAP (Packet Capture) file and identify possible exploited CVEs.

Do the following steps in sequence:
1. Identify the vulnerable service
2. Once detected, identify evidence of the vulnerability in the PCAP
3. Once done, search online for a possible CVE
4. Once you found a CVE online, always confirm the evidence in the PCAP.

Repeat the procedure until you are not sure.
'''

observation, done = driver.reset(task=task)
agent.reset(task=observation)  # Reset the agent

epochs = 1
cprint(f'Observation: {observation}', 'green')
while not done and epochs <= 50:
    print(f'\n=== Step {epochs} ===')

    # Agent step
    agent_out = agent.step(observation)

    # Environment step
    observation, done = driver.step(agent_out.action)
    cprint(f'Observation: {observation}', 'green')

    # Evaluate the current step
    step = f'Action:{agent_out.action}\nObservation: {observation}'

    epochs += 1
agent.agent_finish(observation)
