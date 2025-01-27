from ..tools import *
from ..working_memory import ReActChain
from .base_procedure import BaseProcedure
from typing import Dict, Any, Type, Union
from pydantic import BaseModel, Field, create_model


class ReActModel(BaseModel):
    thought: str = Field(...)
    action: Any = Field(...)

    class Config:
        @staticmethod
        def json_schema_extra(schema: Dict[str, Any], model: Type['ReActModel']) -> None:
            for prop in schema.get('properties', {}).values():
                prop.pop('title', None)

    @classmethod
    def create(cls, actions):
        return create_model(
            cls.__name__,
            action=(Union[tuple(actions)], Field(...)),
            __base__=cls
        )


class ReActProcedure(BaseProcedure):
    def run(self, context: str, scratchpad: list, last_step: ReActChain, actions: list):
        # Format the prompt
        prompt = self.prompt_template.format(
            context=context,
            last_step=last_step.to_str()
        )

        # Invoke LLM with the defined Action model
        llm_out = self.llm.invoke(
            response_model=ReActModel.create(actions),
            system_prompt=prompt,
            messages=scratchpad
        )

        return llm_out
