
from __future__ import annotations

import copy
from typing import Any
from collections.abc import Mapping
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnableSerializable, Runnable
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from ai.prompt import DEBATE_PROMPT_SYSTEM, DEBATE_PROMPT_HUMAN

class AICourt:
    __logger: Any
    __llm_solid: ChatGoogleGenerativeAI | ChatOpenAI | ChatOllama
    __llm_flexible: ChatGoogleGenerativeAI | ChatOpenAI | ChatOllama
    __debaters: list[AIDebater]
    __cycle: int

    def __init__(self,
                 logger: Any,
                 llm_solid: ChatGoogleGenerativeAI | ChatOpenAI | ChatOllama,
                 llm_flexible: ChatGoogleGenerativeAI | ChatOpenAI | ChatOllama,
                 cycle: int = 3,
                 *args: tuple[str, str]
                ):
        self.__logger = logger
        self.__llm_solid = llm_solid
        self.__llm_flexible = llm_flexible

        # prepare the debate prompts
        self.__debaters = []
        if len(args) < 2:
            self.__logger.warning(f"Number of prompts: {len(args)}")
            raise ValueError("At least two prompts are required.")
        for i, prompt in enumerate(args):
            if i == 0:
                # the first debater is the most flexible one
                self.__debaters.append(AIDebater(self.__llm_flexible, i, prompt))
            else:
                # other debaters are more solid ones
                self.__debaters.append(AIDebater(self.__llm_solid, i, prompt))

        # number of debate cycles
        self.__cycle = cycle

    async def debate(self, input:dict)->str:
        # initial prompts
        # Initial prompt means the first response from each_agent based on the same context and question.
        # Get the initial chains from each debater
        initial_chains: dict[str, Runnable] = {}
        for debater in self.__debaters:
            initial_chains.update(debater.initial_chain())
        initial_parallel_prompts: RunnableParallel = RunnableParallel(initial_chains)

        # run initial prompts parallelly
        result = initial_parallel_prompts.invoke(input)


        # start debate cycles
        for _ in range(self.__cycle):
            # prepare debate chains
            debate_chains: dict[str, Runnable] = {}
            for debater in self.__debaters:
                debate_chains.update(debater.debate_chain(input))
            debate_parallel_prompts: RunnableParallel = RunnableParallel(debate_chains)
            # create inputs for debate chains
            input_dbt:dict = copy.deepcopy(input)
            for debater in self.__debaters:
                input_dbt.update({
                    debater.debate_previous_answer_key(): result[debater.debater_key()]
                })
                # collect other debaters' answers except itself
                input_dbt.update({
                    debater.debate_other_answer_key(): "\n\n".join([
                        f"answer[{i}]: {result[d.debater_key()]}" for i, d in enumerate(self.__debaters) if d != debater
                    ])
                })

            # run debate chains parallelly
            result = debate_parallel_prompts.invoke(input_dbt)

            for key, val in result.items():
                self.__logger.debug(f"{key}:\n\{val}\n-------------------\n\n")

        return result[self.__debaters[1].debater_key()]


class AIDebater:
    __id: int
    __initial_prompt: ChatPromptTemplate
    __debate_prompt: ChatPromptTemplate
    __initial_chain: RunnableSerializable
    __debate_chain: RunnableSerializable

    def __init__(self,
                 llm: ChatGoogleGenerativeAI | ChatOpenAI | ChatOllama,
                 debater_id: int,
                 prompt: tuple[str, str]):
        self.__id = debater_id
        initial_prompt = prompt
        # prepare the debate prompts
        debate_prompt = (
            DEBATE_PROMPT_SYSTEM.format(
                ORIGINAL_SYSTEM_PROMPT = initial_prompt[0]
            ),
            # simply add the original human prompt after the debate prompt human
            # that's because we just append debate prompt after the original prompt
            DEBATE_PROMPT_HUMAN + "\n" + initial_prompt[1]
        )
        self.__initial_prompt = ChatPromptTemplate.from_messages([
            ("system", self.__escape_braces(initial_prompt[0])),
            ("human", initial_prompt[1])
        ])

        self.__debate_prompt = ChatPromptTemplate.from_messages([
            ("system", self.__escape_braces(debate_prompt[0])),
            ("human", debate_prompt[1])
        ])

        self.__initial_chain = self.__initial_prompt | llm | StrOutputParser()
        self.__debate_chain = self.__debate_prompt | llm | StrOutputParser()

    def initial_chain(self)->Mapping[str, Runnable]:
        """Get the initial chain."""
        return {
            f"debate_{self.__id}": self.__initial_chain
        }

    def debate_chain(self, input_template:dict)->Mapping[str, Runnable]:
        """Get the debate chain with the given input templates."""
        input_template_form = self.__debate_template_form(input_template)
        return {
            self.debater_key(): (input_template_form | self.__debate_chain)
        }

    def debate_previous_answer_key(self) -> str:
        """Gets the key for the previous answer in the debate."""
        return f"debate_{self.__id}_previous_answer"

    def debate_other_answer_key(self) -> str:
        """Gets the key for the other answers in the debate."""
        return f"debate_{self.__id}_other_answers"
    
    def debater_key(self) -> str:
        """Gets the key for the debater."""
        return f"debate_{self.__id}"

    def __escape_braces(self, s: str) -> str:
        s = s.replace("{", "{{").replace("}", "}}")
        return s

    def __debate_template_form(self, input:dict)->dict:
        debate_template_form = {}
        for key in input.keys():
            debate_template_form[key] = itemgetter(key)
        debate_template_form["previous_answer"] = itemgetter(self.debate_previous_answer_key())
        debate_template_form["other_answers"] = itemgetter(self.debate_other_answer_key())
        return debate_template_form
