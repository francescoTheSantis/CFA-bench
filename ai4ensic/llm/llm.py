import time
import instructor
from openai import OpenAI
# import google.generativeai as GoogleAI
from ..procedures import BaseProcedure

# System prompt for the gpt-4o based structured output adapter
ADAPTER_PROMPT = """You are an AI assistant specializing in parsing and \
structuring free-form text. Your task is to analyze the following free text \
output from another AI system and convert it into a structured format.
"""


def get_free_text_system_prompt(system_prompt: str, response_model: BaseProcedure):
    """Convert the structured output response model to a free text prompt, 
    then append the resulting prompt as additional instruction to the existing
    system prompt.

    Args:
        system_prompt (str): original system prompt
        response_model (BaseProcedure): structured output response model

    Returns:
        str: the final free text system prompt
    """
    # Extract the required parameters
    params = '\n'.join([f'{x}: ' for x in response_model.schema()['required']])
    # Describe the available tools if the response model is an ActionModel
    if response_model.schema()['title'] == 'ActionModel':
        # Extract the tools name
        tools = [x for x in response_model.schema()["$defs"].keys()]
        text = f'Remember that action is one among {tools}.'
        text += 'Action description:'

        # Describe the tools usage
        for tool in response_model.schema()["$defs"].keys():
            # Extract the tool description
            description = response_model.schema()["$defs"][tool]["description"]
            text += f'\n\t{tool}: {description}'

            # Extract the tools parameters
            text += '\n\tParameters:'
            params = response_model.schema()['$defs'][tool]['properties']
            for k, v in params.items():
                if 'description' in v:
                    text += f'\n\t\t{k}: {v["description"]}'
                else:
                    text += f'\n\t\t{k}'
        # Format the new system prompt
        system_prompt = f'{system_prompt}\n{text}'

    # For another response model, simply add a reminder
    else:
        system_prompt = f'{system_prompt}\n\nRemember to always use only the '\
            f'following keywords without adding additional text:\n{params}'

    return system_prompt


class LLMClient():
    """A client for interacting with various Large Language Models (LLMs).

    This class provides a unified interface for working with different LLM providers,
    currently supporting OpenAI's GPT models and Google's Gemini models.

    Args:
        api_key (str): The third party API key for authentication
        model (str): The name of the LLM to use.

    Attributes:
        client (instructor.client.Instructor): The instructor-based LLM client.
        model (str): The name of the LLM being used.

    Methods:
        invoke(response_model, system_prompt, messages): Invokes the LLM with 
            the given parameters.
    """

    def __init__(self, api_key: str, model: str):
        # Use OpenAI LLM
        if 'gpt' in model:
            self.client = instructor.from_openai(
                OpenAI(api_key=api_key),
                temperature=0,
                seed=0
            )

        # Use OpenAI o3 with a gpt-4o adapter for structured output
        elif 'o3' in model:
            self.adapter = LLMClient(api_key=api_key, model="gpt-4o")
            self.client = OpenAI(api_key=api_key)

        # Use Gemini LLM
        elif 'gemini' in model:
            self.client = instructor.from_gemini(
                client=GoogleAI.GenerativeModel(
                    model_name=f"models/{model}",
                ),
                mode=instructor.Mode.GEMINI_JSON,
            )
        self.model = model

    def adapt_structured_output(self, llm_out, response_model: BaseProcedure):
        """When using a LLM not supporting structured output, use a gpt-4o based
        adapter (which supports structured output) to convert the free-text 
        output of the LLM to a formatted response model.

        Args:
            llm_out: formatted free-text LLM output
            response_model (BaseProcedure): response model to which the output must
                be adapted

        Returns:
            BaseProcedure: The free-text LLM output converted to structured output 
        """
        # Extract the content of the free text LLM output
        llm_out = llm_out.choices[-1].message.content

        # Create a user message with the free text LLM output
        messages = [{"role": "user", "content": llm_out}]

        # Invoke the gpt-4o based adapter
        adapted_llm_out = self.adapter.invoke(
            response_model=response_model,
            system_prompt=ADAPTER_PROMPT,
            messages=messages
        )
        return adapted_llm_out

    def invoke(self, response_model: BaseProcedure, system_prompt: str, messages: list = []):
        """Invokes the LLM with the given parameters.

        This method formats the prompt, sends it to the appropriate LLM,
        and returns the model's response.

        Args:
            response_model (BaseProcedure): The expected response model structure.
            system_prompt (str): The system prompt to guide the LLM's behavior.
            messages (list, optional): A list of message dictionaries to include 
                in the conversation. Defaults to [].

        Returns:
            pydantic.BaseModel: The response model formatted by the LLM 
        """
        # Invoke OpenAI GPT LLMs
        if 'gpt' in self.model:
            # Format the prompt
            prompt = [{'role': 'system', 'content': system_prompt}]
            prompt += messages

            # Invoke the LLM
            llm_out = self.client.chat.completions.create(
                model=self.model,
                response_model=response_model,
                messages=prompt,
                max_retries=5
            )

        # Use OpenAI 3 with the gpt-4o based adapter for structured output
        elif 'o3' in self.model:
            # Convert the response model to a free text system prompt
            free_text_prompt = get_free_text_system_prompt(
                system_prompt=system_prompt,
                response_model=response_model
            )

            # Format the free text prompt
            prompt = [{'role': 'user', 'content': free_text_prompt}]
            prompt += messages

            # Invoke the free-text LLM
            llm_out = self.client.chat.completions.create(
                model=self.model,
                messages=prompt
            )

            # Convert the free text LLM output to structured output
            llm_out = self.adapt_structured_output(llm_out, response_model)

        # Invoke Gemini LLMs
        elif 'gemini' in self.model:
            # Format the prompt
            prompt += [{'role': 'user', 'content': 'Execution:'}]

            time.sleep(5)  # Wait 5 seconds to respect the request limits

            # Invoke the LLM
            llm_out = self.client.messages.create(
                response_model=response_model,
                messages=prompt
            )

        return llm_out
