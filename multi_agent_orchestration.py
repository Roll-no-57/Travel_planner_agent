from Planning_agent import ReactAgent
from tool_decorator import Tool
from colorama import Fore, Style
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AgentRole(Enum):
    """Define different agent roles"""
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist" 
    VALIDATOR = "validator"

@dataclass
class AgentMessage:
    """Standardized message format between agents"""
    sender: str
    receiver: str
    content: str
    message_type: str
    metadata: Dict[str, Any] = None
    
class AgentRegistry:
    """Simple registry to manage agents"""
    def __init__(self):
        self.agents: Dict[str, 'MultiAgent'] = {}
    
    def register(self, agent: 'MultiAgent'):
        self.agents[agent.name] = agent
        
    def get_agent(self, name: str) -> Optional['MultiAgent']:
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        return list(self.agents.keys())

class MultiAgent(ReactAgent):
    """Extended ReactAgent with multi-agent capabilities"""
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        tools: Tool | list[Tool] = None,
        model: str = "gemini-2.0-flash-exp",
        system_prompt: str = "",
        registry: AgentRegistry = None,
        specialization: str = None
    ):
        # Initialize the base ReactAgent
        super().__init__(tools or [], model, system_prompt)
        
        self.name = name
        self.role = role
        self.specialization = specialization
        self.registry = registry
        self.message_history: List[AgentMessage] = []
        
        # Role-specific system prompt enhancement
        self._enhance_system_prompt()
        
        # Register with registry if provided
        if self.registry:
            self.registry.register(self)
    
    def _enhance_system_prompt(self):
        """Enhance system prompt based on agent role"""
        role_prompts = {
            AgentRole.COORDINATOR: """
You are a Coordinator Agent. Your role is to:
1. Break down complex tasks into subtasks
2. Delegate tasks to appropriate specialist agents
3. Synthesize results from multiple agents
4. Ensure overall task completion

When you need help from other agents, use the delegate_task tool.
""",
            AgentRole.SPECIALIST: f"""
You are a Specialist Agent with expertise in: {self.specialization or 'general tasks'}
Your role is to:
1. Handle specialized tasks in your domain
2. Provide expert analysis and recommendations
3. Collaborate with other agents when needed
4. Report back to coordinators with detailed results
""",
            AgentRole.VALIDATOR: """
You are a Validator Agent. Your role is to:
1. Review and validate outputs from other agents
2. Ensure quality and consistency
3. Flag potential issues or improvements
4. Provide quality assurance for the final output
"""
        }
        
        self.system_prompt += role_prompts.get(self.role, "")
    
    def send_message(self, receiver: str, content: str, message_type: str = "task") -> bool:
        """Send message to another agent"""
        if not self.registry:
            print(Fore.RED + f"No registry available for agent {self.name}")
            return False
            
        receiver_agent = self.registry.get_agent(receiver)
        if not receiver_agent:
            print(Fore.RED + f"Agent {receiver} not found in registry")
            return False
        
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            content=content,
            message_type=message_type
        )
        
        # Store in sender's history
        self.message_history.append(message)
        
        # Deliver to receiver
        return receiver_agent.receive_message(message)
    
    def receive_message(self, message: AgentMessage) -> bool:
        """Receive message from another agent"""
        print(Fore.GREEN + f"{self.name} received message from {message.sender}: {message.content}")
        self.message_history.append(message)
        return True
    
    def delegate_task(self, task: str, target_agent: str = None) -> str:
        """Delegate a task to another agent"""
        if not target_agent:
            # Auto-select based on available agents and task
            target_agent = self._select_best_agent(task)
        
        if target_agent:
            self.send_message(target_agent, task, "delegation")
            # Get the target agent and run the task
            agent = self.registry.get_agent(target_agent)
            if agent:
                return agent.run(task, max_rounds=5)
        
        return f"Could not delegate task: {task}"
    
    def _select_best_agent(self, task: str) -> Optional[str]:
        """Simple agent selection logic"""
        if not self.registry:
            return None
            
        # Simple keyword-based selection
        task_lower = task.lower()
        
        for agent_name, agent in self.registry.agents.items():
            if agent.name == self.name:  # Skip self
                continue
                
            if agent.specialization:
                if any(keyword in task_lower for keyword in agent.specialization.lower().split()):
                    return agent_name
        
        # Return any available agent
        available_agents = [name for name in self.registry.list_agents() if name != self.name]
        return available_agents[0] if available_agents else None

class MultiAgentOrchestrator:
    """Simple orchestrator for multi-agent workflows"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.coordinator: Optional[MultiAgent] = None
    
    def add_agent(self, agent: MultiAgent):
        """Add agent to the system"""
        agent.registry = self.registry
        self.registry.register(agent)
        
        # Set the first coordinator agent as default
        if agent.role == AgentRole.COORDINATOR and not self.coordinator:
            self.coordinator = agent
    
    def create_trip_planning_system(self):
        """Create a specialized trip planning multi-agent system"""
        
        # Coordinator Agent
        coordinator = MultiAgent(
            name="trip_coordinator",
            role=AgentRole.COORDINATOR,
            tools=[],  # Add delegation tools here
            specialization="trip planning coordination"
        )
        
        # Specialist Agents
        hotel_agent = MultiAgent(
            name="hotel_specialist",
            role=AgentRole.SPECIALIST,
            tools=[],  # Add hotel-related tools
            specialization="hotel booking and accommodation"
        )
        
        activity_agent = MultiAgent(
            name="activity_specialist", 
            role=AgentRole.SPECIALIST,
            tools=[],  # Add activity-related tools
            specialization="activities and attractions"
        )
        
        transport_agent = MultiAgent(
            name="transport_specialist",
            role=AgentRole.SPECIALIST,
            tools=[],  # Add transport-related tools
            specialization="transportation and logistics"
        )
        
        # Validator Agent
        validator = MultiAgent(
            name="trip_validator",
            role=AgentRole.VALIDATOR,
            tools=[],
            specialization="trip plan validation"
        )
        
        # Add all agents to the system
        agents = [coordinator, hotel_agent, activity_agent, transport_agent, validator]
        for agent in agents:
            self.add_agent(agent)
        
        return agents
    
    def process_complex_query(self, query: str, max_iterations: int = 3) -> str:
        """Process a complex query using multiple agents"""
        if not self.coordinator:
            return "No coordinator agent available"
        
        print(Fore.BLUE + f"\n=== Multi-Agent Processing: {query} ===")
        
        # Start with coordinator
        result = self.coordinator.run(query, max_rounds=10)
        
        # Simple iteration for refinement
        for i in range(max_iterations - 1):
            # Get feedback from validator if available
            validator = self.registry.get_agent("trip_validator")
            if validator:
                validation_query = f"Please validate and suggest improvements for: {result}"
                validation_result = validator.run(validation_query, max_rounds=5)
                
                # Refine based on validation
                refinement_query = f"Based on this feedback: {validation_result}, improve the original result: {result}"
                result = self.coordinator.run(refinement_query, max_rounds=5)
        
        return result

# Example usage and setup
def create_simple_multi_agent_system():
    """Create a simple multi-agent system for demonstration"""
    
    orchestrator = MultiAgentOrchestrator()
    agents = orchestrator.create_trip_planning_system()
    
    print(Fore.GREEN + f"Created multi-agent system with {len(agents)} agents:")
    for agent in agents:
        print(Fore.YELLOW + f"- {agent.name} ({agent.role.value}): {agent.specialization}")
    
    return orchestrator

# Tool for delegation (to be added to coordinator agents)
@dataclass 
class DelegationTool:
    """Tool for delegating tasks to other agents"""
    
    def delegate_to_specialist(self, task: str, specialist_type: str) -> str:
        """
        Delegate a task to a specialist agent
        
        Args:
            task: The task to delegate
            specialist_type: Type of specialist needed (hotel, activity, transport)
        """
        # This would be implemented as a proper tool
        return f"Delegating '{task}' to {specialist_type} specialist"

# Example workflow
def example_multi_agent_workflow():
    """Example of how to use the multi-agent system"""
    
    print(Fore.CYAN + Style.BRIGHT + "\n=== Multi-Agent Trip Planning Demo ===\n")
    
    # Create the system
    orchestrator = create_simple_multi_agent_system()
    
    # Process a complex query
    query = "Plan a 5-day trip to Japan for 2 people, budget $3000, interested in culture and food"
    result = orchestrator.process_complex_query(query)
    
    print(Fore.GREEN + f"\nFinal Result:\n{result}")
    
    return result

if __name__ == "__main__":
    example_multi_agent_workflow()