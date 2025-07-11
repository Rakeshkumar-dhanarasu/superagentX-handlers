import pytest
from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.prompt import PromptTemplate
from superagentx_handlers import GCPLoadBalancerHandler
from superagentx_handlers.twitter import logger

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/pipe/gcp/test_gcp_loadbalancer_pipe.py::TestGCPLBPipe::test_gcp_lb_pipe
'''

@pytest.fixture
def pipe_client_init() -> dict:
    # llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}
    llm_config = {'model': 'gpt-4o', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    response = {'llm': llm_client}
    return response

class TestGCPLBPipe:

    async def test_gcp_lb_pipe(self, pipe_client_init: dict):
        llm_client: LLMClient = pipe_client_init.get('llm')
        aws_sg_handler = GCPLoadBalancerHandler()
        prompt_template = PromptTemplate(system_message=f"You are an GCP LoadBalancer for GRC.")
        engine = Engine(
            llm=llm_client,
            prompt_template=prompt_template,
            handler=aws_sg_handler
        )
        aws_sg_agent = Agent(
            name=f"GCP LoadBalancer Agent",
            goal="Generate the response and data based on the user input.",
            role=f"You are a GRC Evidence Collection Expert.",
            llm=llm_client,
            prompt_template=prompt_template,
            max_retry=2,
            engines=[engine],
        )
        pipe = AgentXPipe(
            agents=[aws_sg_agent]
        )
        prompt = f"""
        If the task has implementing or creating, you just collect evidence the data implemented or created not try to implement.
        """
        query_instruct = "Is HTTPS or SSL enforced for all external-facing LBs (HTTP(S), SSL proxy)?"
        result = await pipe.flow(
            query_instruction=f"{prompt}\n\nTool:GCP LoadBalancer\n\nTask:{query_instruct}"
        )
        logger.info(result)

