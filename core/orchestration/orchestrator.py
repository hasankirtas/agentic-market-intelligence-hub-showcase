from typing import Dict, Any, List

class Orchestrator:
    def __init__(self):
        self.agents = {}
        
    def register_agent(self, name: str, agent: Any):
        self.agents[name] = agent

    async def execute_sequential(self, initial_state: Dict[str, Any], agents: List[str], workflow_id: str = None) -> Dict[str, Any]:
        """
        Simulate sequential execution of agents.
        In this mock implementation, we iterate through the requested agents
        and collect their simulated outputs.
        """
        results = {}
        # Simple simulation: just run each agent with the initial state
        # In a real system, the output of one would feed the input of the next.
        current_state = initial_state
        
        for agent_name in agents:
            agent = self.agents.get(agent_name)
            if agent:
                 # In simulation, agents just return their pre-canned data
                 res = await agent.run(current_state)
                 results[agent_name] = res
        
        return {"agent_results": results, "status": "completed", "workflow_id": workflow_id}
