from typing import Dict, Any, Type
from pydantic import BaseModel, Field
from .base_procedure import BaseProcedure


class ReportScratchpadModel(BaseModel):
    report: str = Field(..., title='report')

    class Config:
        @staticmethod
        def json_schema_extra(schema: Dict[str, Any], model: Type['ReportScratchpadModel']) -> None:
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)


class ReportScratchpadProcedure(BaseProcedure):
    """A reasoning procedure that invokes the LLM to produce a task-oriented 
    report of the agent scratchpad.

    This class extends the BaseProcedure to handle reasoning and summary production. 
    It leverages the raw agent scratchpad and the task instructions to produce 
    a task-oriented summary using the LLM.

    Args:
        llm (LLMClient): The LLM client responsible for executing tasks based 
            on the prompt.
        prompt_template (str): The prompt template that will be formatted and 
            used as input to the LLM.

    Attributes:
        llm (LLMClient): The LLM client responsible for executing tasks based 
            on the prompt.
        prompt_template (str): The prompt template that will be formatted and 
            used as input to the LLM.

    Methods:
        run(context, scratchpad): Generates a task-oriented summary based on 
            the given inputs using the LLM.
    """

    def run(self, context: str, scratchpad: list):
        """Execute the report reasoning procedure based on the current task and
        agent scratchpad

        Args:
            context (str): The description of the current task
            scratchpad (list): The agent scratchpad formatted as messages list

        Returns:
            SummaryModel: The SummaryModel formatted by the LLM
        """
        # Format the prompt
        prompt = self.prompt_template.format(
            context=context
        )
        
        # Invoke LLM
        llm_out = self.llm.invoke(
            response_model=ReportScratchpadModel,
            system_prompt=prompt,
            messages=scratchpad
        )

        return llm_out
