import json
from ..llm import LLMClient
from ..working_memory import ReActChain
from ..working_memory import ReActScratchpad


class BaseAgent():
    """A base class for implementing AI agents with reasoning and acting 
    capabilities.

    This class provides the fundamental structure for an AI agent that can 
    perform tasks, maintain working memory, use tools, and log its actions.

    Args:
        prompt_template (str): A template string for formatting the agent's prompt.
        llm (LLMClient): An instance of the LLM client for generating responses.
        working_memory (ReActScratchpad): An instance to manage the agent's working memory.
        tools (list): A list of tool functions available to the agent.
        logpath (str, optional): Path to save logs. Defaults to None.

    Attributes:
        prompt_template (str): The template for formatting the agent's prompt.
        working_memory (ReActScratchpad): The agent's working memory.
        llm (LLMClient): The LLM client used by the agent.
        tools (dict): A dictionary of available tools, keyed by their names.
        logpath (str): Path for saving logs.
        task (str): The current task assigned to the agent.
        prompt (str): The formatted prompt for the current task.
        last_step (ReActChain): The most recent step in the agent's reasoning chain.
        start (bool): Flag indicating if this is the start of a new task.

    Methods:
        reset(task): Resets the agent's state for a new task.
        update_memory(observation): Updates the agent's working memory with a new observation.
        write_logs(fpath): Writes the agent's memory logs to a file.
        agent_finish(observation): Finalizes the agent's task with a final observation.
        step(observation): Performs a single step in the agent's reasoning process.
    """

    def __init__(self, prompt_template: str, llm: LLMClient, working_memory: ReActScratchpad, tools: list, logpath: str = None):
        self.prompt_template = prompt_template
        self.working_memory = working_memory
        self.llm = llm
        self.tools = {x.__name__: x for x in tools}
        self.logpath = logpath

        self.task = None
        self.prompt = None
        self.last_step = ReActChain.format()
        self.start = True

    def reset(self, task: str):
        """Resets the agent's state for a new task.

        Args:
            task (str): The new task to be assigned to the agent.
        """
        self.task = task
        self.prompt = self.prompt_template.format(input=task)

    def update_memory(self, observation: str):
        """Updates the agent's working memory with a new observation.

        Args:
            observation (str): The new observation to be added to the working memory.
        """
        self.last_step.observation = observation

        self.working_memory.update(self.last_step)
        if self.logpath:
            self.write_logs(self.logpath)

    def write_logs(self, fpath: str):
        """Writes the agent's memory logs to a JSON file.

        Args:
            fpath (str): The file path where the logs should be written.
        """
        obj = {
            'steps': self.working_memory.to_log()
        }
        with open(f'{fpath}.json', 'w') as file:
            file.write(json.dumps(obj))

    def agent_finish(self, observation: str):
        """Finalizes the agent's task with a final observation.

        This method is called when the agent has completed its task.

        Args:
            observation (str): The final observation to be added to the working memory.
        """
        self.update_memory(observation)

    def step(self, observation: str):
        """Performs a single step in the agent's reasoning process.

        This method should be implemented by subclasses to define the agent's behavior
        for each step of its task.

        Args:
            observation (str): The current observation for this step.

        Returns:
            ReActChain: The updated last step of the agent's reasoning chain.
        """
        return self.last_step
