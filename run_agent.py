from termcolor import cprint
from ai4ensic.utils import load_data
from ai4ensic.driver import ForensicDriver
from ai4ensic.prompts import INSTRUCTION_TEMPLATE
from ai4ensic.agent import ReActAgent, AutonomousAgent, SummariseReActAgent
from ai4ensic.working_memory import ReActScratchpad
from ai4ensic.llm import LLMClient
from ai4ensic.tools.report import FinalAnswer, FinalReport
from ai4ensic.tools.pcap import ExtractFrame, ExpandFrameData, ListFrames
from ai4ensic.tools.logs import ReadLogFile
from ai4ensic.tools.cve import CVEDescriptor, WebQuickSearch, GetCVEList
from ai4ensic.procedures import ReportScratchpadProcedure
from ai4ensic.prompts import SCRATCHPAD_SUMMARY_TEMPLATE
import os
from dotenv import load_dotenv
import argparse
import pandas as pd
import openai
import re

load_dotenv()

def get_occurrences(input_string, start_substring='', end_substring='\n'):
    # Create a regular expression pattern based on the provided start and end substrings
    try:
        if end_substring=='':
            index = input_string.find(start_substring)
            if index == -1:
                return ""
            return input_string[index + len(start_substring):]
        else:
            pattern = re.escape(start_substring) + r'(.*?)' + re.escape(end_substring)
            # Find all occurrences of text between the start and end substrings
            matches = re.findall(pattern, input_string)
            return matches[0].strip()  # Return a list of all occurrences
    except Exception as e:
        return "No Answer"

def main(args):

    # Set environment variables for project and scripts directories
    OPENAI_KEY = os.environ.get("OPENAIKEY")
    openai.api_key = OPENAI_KEY

    # Initialize the Tools
    tools = [ExtractFrame, FinalReport, WebQuickSearch, ReadLogFile] # ReadLogFile, GetCVEList

    pcaps = load_data()  # Load the games

    if args.epochs_to_reset>args.max_iterations:
        reset='noReset'
    else:
        reset='Reset'

    results_path = f'results/{args.reasoning}_{args.LLM}.csv'
    dir_path = 'results'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Directory '{dir_path}' created!")
    else:
        print(f"Directory '{dir_path}' already exists.")

    if os.path.isfile(results_path):
        print("Results file exists.")
        results = pd.read_csv(results_path)
        columns = results.columns
        results.drop(columns=[x for x in columns if 'Unnamed' in x], inplace=True)
    else:
        print("Results file does not exist.")
        results = pd.DataFrame(columns=['cve', 'service', 'successful', 'is_vulnerable', 'evidence', 'n_iterations', 'error'])

    
    log_path = f'log/{args.reasoning}'
    if not os.path.exists(log_path):
        os.makedirs(log_path)   
    
    for i in range(len(pcaps)):

        # Initialize LLM
        llm = LLMClient(api_key=OPENAI_KEY, model=args.LLM)

        # Initialize the WorkingMemory
        working_memory = ReActScratchpad()

        if args.reasoning=='react':
            # Initialize the Agent
            agent = ReActAgent(
                prompt_template=INSTRUCTION_TEMPLATE,
                llm=llm,
                working_memory=working_memory,
                tools=tools,
                logpath=f'{log_path}/{i}'
            )
        elif args.reasoning=='react_summary':
            agent = SummariseReActAgent(
                prompt_template=INSTRUCTION_TEMPLATE,
                llm=llm,
                working_memory=working_memory,
                tools=tools,
                logpath=f'{log_path}/{i}'
            )
        elif args.reasoning=='complete':
            agent = AutonomousAgent(
                prompt_template=INSTRUCTION_TEMPLATE,
                llm = llm,
                working_memory = working_memory,
                tools = tools,
                logpath=f'{log_path}/{i}'
            )
        else:
            raise ValueError(f'Reasoning strategy ({args.reasoning}) not yet implemented!')
        
        game = pcaps[i]  
        print(game)

        # Initialize driver
        driver = ForensicDriver(game=game, llm=llm, query_strategy=args.query_strategy)

        # The task assigned to the agent
        task = """
Analyze the provided PCAP (Packet Capture) and logs files to accomplish the following tasks:

1. Identify the name of the service or application involved.
2. Determine the relevant CVE (Common Vulnerabilities and Exposures) based on the captured data.
3. Gather evidence of malicious activities associated with the identified CVE.
4. Assess whether the service or application is vulnerable to the identified attack.
5. Evaluate whether the attack was successful.

Guidelines:
- Begin by thoroughly analyzing the PCAP and logs files to extract relevant information.
- After the exploratory analysis, ensure that the CVE identification is accurate by cross-referencing details from external sources with the evidence found in the PCAP.
- Use the online search tool only after the exploratory analysis has been completed to verify the findings and gather additional information.
"""

        observation, done = driver.reset(task=task)
        agent.reset(task=observation)  
        error_flag = False
        try: 
            epochs = 1
            cprint(f'Observation: {observation}', 'green')
            while not done and epochs <= args.max_iterations:
                try:
                    print(f'\n=== Step {epochs} ===')
                    # every t epochs the agent is reset and a summary of the previous discoveries is provided to the new one.
                    if epochs%args.epochs_to_reset==0 and epochs!=1 and args.reasoning!='react':
                        reset_observation, done = driver.reset(task=task)
                        summary_procedure = ReportScratchpadProcedure(agent.llm, SCRATCHPAD_SUMMARY_TEMPLATE)
                        scratchpad = agent.working_memory.to_messages()
                        summarized_scratchpad = summary_procedure.run(reset_observation, scratchpad).report
                        observation = f'{reset_observation}\n\nThis is the last observation you got from the environment:\n{observation}\n\nThis what you know so far:\n{summarized_scratchpad}'
                        cprint(f'Summarized scratchpad: {observation}', 'blue')
                        agent.reset(task=observation) 
                    if epochs>=(args.max_iterations-1):
                        observation += f'{observation}\n\nWARNING: You are not allowed to explore the PCAP anymore, you have to provide the report with the information you gathered so far.'
                        print(observation)
                    agent_out = agent.step(observation)

                    # Environment step
                    observation, done = driver.step(agent_out.action)
                    cprint(f'Observation: {observation}', 'green')

                    # Evaluate the current step
                    step = f'Action:{agent_out.action}\nObservation: {observation}'

                    epochs += 1
                except Exception as e:
                    done=True
                    observation = e
                    print(e)
                    error_flag=True
            agent.agent_finish(observation)

            final_answer = observation

        except Exception as e:
            print(e)
            final_answer = ''
            done=False

        error = observation if error_flag else False
        if done:
            d = {'cve': get_occurrences(final_answer, "Identified CVE: "), 
                'service': get_occurrences(final_answer, "Affected Service: "), 
                'successful': get_occurrences(final_answer, "Attack: "), 
                'is_vulnerable': get_occurrences(final_answer, "Is Service Vulnerable: "),
                'evidence': get_occurrences(final_answer, "Critical PCAP entries: ", ""), 
                'n_iterations':epochs,
                'error': error}
        else:
             placeholder = 'No answer'
             d = {'cve': placeholder, 
                'service': placeholder, 
                'successful': placeholder, 
                'is_vulnerable': placeholder,
                'evidence': placeholder, 
                'n_iterations':epochs,
                'error': False}           
        
        results = pd.concat([results, pd.DataFrame([d])], ignore_index=False)
        results.to_csv(results_path, sep=';')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use this script to run an LLM Agent with the goal of analyzing a PCAP file.")
    parser.add_argument("--LLM", type=str, default='gpt-4o', help="The name of the LLM to use.")
    parser.add_argument("--max_iterations", type=int, default=50, help="The maximum number of iterations the agent can make.")
    parser.add_argument("--reasoning", type=str, default='react', help='The reasoining strategy emplyed by the agent')
    parser.add_argument("--epochs_to_reset", type=int, default=100, help='Number of epochs before the entire scratchpad is summarized.')
    parser.add_argument("--query_strategy", type=str, default='standard', help='The query strategy to use for the web search.')
    args = parser.parse_args()
    main(args)
