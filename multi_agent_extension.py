import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from Planning_agent import ReactAgent
from tool_decorator import Tool
from colorama import Fore, Style
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime

class AgentRole(Enum):
    """Define different agent roles"""
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist" 
    VALIDATOR = "validator"

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    """Task definition for parallel execution"""
    id: str
    agent_name: str
    content: str
    priority: int = 1
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

@dataclass
class AgentMessage:
    """Standardized message format between agents"""
    sender: str
    receiver: str
    content: str
    message_type: str
    task_id: str = None
    metadata: Dict[str, Any] = None

class ParallelAgentRegistry:
    """Thread-safe registry for parallel agent execution"""
    def __init__(self):
        self.agents: Dict[str, 'HierarchicalAgent'] = {}
        self._lock = threading.Lock()
    
    def register(self, agent: 'HierarchicalAgent'):
        with self._lock:
            self.agents[agent.name] = agent
            
    def get_agent(self, name: str) -> Optional['HierarchicalAgent']:
        with self._lock:
            return self.agents.get(name)
    
    def get_specialists_by_type(self, specialization_keyword: str) -> List['HierarchicalAgent']:
        """Get all specialist agents matching a keyword"""
        with self._lock:
            return [
                agent for agent in self.agents.values() 
                if (agent.role == AgentRole.SPECIALIST and 
                    agent.specialization and 
                    specialization_keyword.lower() in agent.specialization.lower())
            ]
    
    def list_agents(self) -> List[str]:
        with self._lock:
            return list(self.agents.keys())

class HierarchicalAgent(ReactAgent):
    """Extended ReactAgent with hierarchical and parallel capabilities"""
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        tools: Union[Tool, List[Tool]] = None,
        model: str = "gemini-2.0-flash-exp",
        system_prompt: str = "",
        registry: ParallelAgentRegistry = None,
        specialization: str = None,
        parent_agent: str = None
    ):
        # Initialize the base ReactAgent
        super().__init__(tools or [], model, system_prompt)
        
        self.name = name
        self.role = role
        self.specialization = specialization
        self.registry = registry
        self.parent_agent = parent_agent
        self.child_agents: List[str] = []
        self.message_history: List[AgentMessage] = []
        self.active_tasks: Dict[str, Task] = {}
        self._task_lock = threading.Lock()
        
        # Role-specific system prompt enhancement
        self._enhance_system_prompt()
        
        # Register with registry if provided
        if self.registry:
            self.registry.register(self)
    
    def _enhance_system_prompt(self):
        """Enhance system prompt based on agent role and hierarchy"""
        base_prompts = {
            AgentRole.COORDINATOR: f"""
You are a Coordinator Agent named {self.name}. Your role is to:
1. Break down complex tasks into subtasks for parallel execution
2. Coordinate multiple specialist agents working simultaneously  
3. Manage dependencies between tasks
4. Synthesize results from parallel executions
5. Ensure overall task completion and quality

You can delegate tasks to multiple specialists simultaneously for faster execution.
When planning trips, delegate hotel and activity searches in parallel to save time.
""",
            AgentRole.SPECIALIST: f"""
You are a Specialist Agent named {self.name} with expertise in: {self.specialization or 'general tasks'}
Your role is to:
1. Handle specialized tasks efficiently in your domain
2. Work in parallel with other specialists
3. Report detailed results back to coordinators
4. Collaborate when cross-domain expertise is needed

You are part of a hierarchical system and may work simultaneously with other specialists.
""",
            AgentRole.VALIDATOR: f"""
You are a Validator Agent named {self.name}. Your role is to:
1. Review and validate outputs from multiple agents
2. Ensure consistency across parallel executions
3. Identify and flag integration issues between specialist results
4. Provide comprehensive quality assurance
"""
        }
        
        self.system_prompt += base_prompts.get(self.role, "")
    
    def add_child_agent(self, child_name: str):
        """Add a child agent to this agent's hierarchy"""
        if child_name not in self.child_agents:
            self.child_agents.append(child_name)
    
    def execute_task(self, task: Task) -> Task:
        """Execute a single task and return updated task with results"""
        print(Fore.CYAN + f"[{self.name}] Starting task: {task.id}")
        
        with self._task_lock:
            self.active_tasks[task.id] = task
            task.status = TaskStatus.IN_PROGRESS
            task.start_time = datetime.now()
        
        try:
            # Execute the task using the base ReactAgent's run method
            result = self.run(task.content, max_rounds=8)
            
            with self._task_lock:
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.end_time = datetime.now()
                
            print(Fore.GREEN + f"[{self.name}] Completed task: {task.id}")
            return task
            
        except Exception as e:
            with self._task_lock:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                task.end_time = datetime.now()
                
            print(Fore.RED + f"[{self.name}] Failed task {task.id}: {e}")
            return task

class HierarchicalTripOrchestrator:
    """Hierarchical orchestrator with parallel execution capabilities"""
    
    def __init__(self, max_workers: int = 4):
        self.registry = ParallelAgentRegistry()
        self.coordinator: Optional[HierarchicalAgent] = None
        self.max_workers = max_workers
        self.task_counter = 0
    
    def add_agent(self, agent: HierarchicalAgent, parent_name: str = None):
        """Add agent to the hierarchical system"""
        agent.registry = self.registry
        self.registry.register(agent)
        
        # Set parent-child relationships
        if parent_name:
            parent = self.registry.get_agent(parent_name)
            if parent:
                parent.add_child_agent(agent.name)
                agent.parent_agent = parent_name
        
        # Set the first coordinator agent as default
        if agent.role == AgentRole.COORDINATOR and not self.coordinator:
            self.coordinator = agent
    
    def create_hierarchical_trip_system(self):
        """Create a hierarchical trip planning system with parallel capabilities"""
        
        # Root Coordinator
        coordinator = HierarchicalAgent(
            name="trip_coordinator",
            role=AgentRole.COORDINATOR,
            tools=[],  # Add your existing tools here
            specialization="trip planning coordination"
        )
        
        # Parallel Specialist Agents
        hotel_agent = HierarchicalAgent(
            name="hotel_specialist",
            role=AgentRole.SPECIALIST,
            tools=[],  # Add get_hotels_tool here
            specialization="hotel accommodation booking"
        )
        
        activity_agent = HierarchicalAgent(
            name="activity_specialist", 
            role=AgentRole.SPECIALIST,
            tools=[],  # Add get_activity_tool here
            specialization="activities attractions entertainment"
        )
        
        transport_agent = HierarchicalAgent(
            name="transport_specialist",
            role=AgentRole.SPECIALIST,
            tools=[],  # Add transport tools here
            specialization="transportation logistics travel"
        )
        
        search_agent = HierarchicalAgent(
            name="search_specialist",
            role=AgentRole.SPECIALIST,
            tools=[],  # Add get_search_results_tool, get_raw_website_content_tool
            specialization="web search information gathering"
        )
        
        # Validator Agent
        validator = HierarchicalAgent(
            name="trip_validator",
            role=AgentRole.VALIDATOR,
            tools=[],
            specialization="trip plan validation quality assurance"
        )
        
        # Build hierarchy
        self.add_agent(coordinator)  # Root
        
        # Add specialists under coordinator
        self.add_agent(hotel_agent, "trip_coordinator")
        self.add_agent(activity_agent, "trip_coordinator") 
        self.add_agent(transport_agent, "trip_coordinator")
        self.add_agent(search_agent, "trip_coordinator")
        
        # Add validator under coordinator
        self.add_agent(validator, "trip_coordinator")
        
        print(Fore.GREEN + f"Created hierarchical system:")
        print(Fore.YELLOW + f"├── {coordinator.name} (Coordinator)")
        print(Fore.YELLOW + f"│   ├── {hotel_agent.name} (Specialist)")
        print(Fore.YELLOW + f"│   ├── {activity_agent.name} (Specialist)")  
        print(Fore.YELLOW + f"│   ├── {transport_agent.name} (Specialist)")
        print(Fore.YELLOW + f"│   ├── {search_agent.name} (Specialist)")
        print(Fore.YELLOW + f"│   └── {validator.name} (Validator)")
        
        return [coordinator, hotel_agent, activity_agent, transport_agent, search_agent, validator]
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        self.task_counter += 1
        return f"task_{self.task_counter}_{int(time.time())}"
    
    def execute_parallel_tasks(self, tasks: List[Task]) -> Dict[str, Task]:
        """Execute multiple tasks in parallel"""
        print(Fore.BLUE + f"\n=== Executing {len(tasks)} tasks in parallel ===")
        
        completed_tasks = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in tasks:
                agent = self.registry.get_agent(task.agent_name)
                if agent:
                    future = executor.submit(agent.execute_task, task)
                    future_to_task[future] = task
                else:
                    print(Fore.RED + f"Agent {task.agent_name} not found for task {task.id}")
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    completed_task = future.result()
                    completed_tasks[completed_task.id] = completed_task
                except Exception as e:
                    print(Fore.RED + f"Task {task.id} generated an exception: {e}")
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    completed_tasks[task.id] = task
        
        return completed_tasks
    
    def plan_trip_hierarchically(self, query: str, destination: str = None) -> str:
        """Plan a trip using hierarchical parallel execution"""
        if not self.coordinator:
            return "No coordinator agent available"
        
        print(Fore.BLUE + Style.BRIGHT + f"\n=== Hierarchical Trip Planning ===")
        print(Fore.CYAN + f"Query: {query}")
        
        # Phase 1: Initial destination research (if needed)
        if not destination:
            search_task = Task(
                id=self._generate_task_id(),
                agent_name="search_specialist",
                content=f"Research and recommend destinations based on: {query}"
            )
            search_results = self.execute_parallel_tasks([search_task])
            destination_info = search_results[search_task.id].result
            print(Fore.GREEN + f"Destination research completed: {destination_info[:200]}...")
        
        # Phase 2: Parallel specialist tasks
        parallel_tasks = [
            Task(
                id=self._generate_task_id(),
                agent_name="hotel_specialist", 
                content=f"Find the best accommodation options for: {query}. Focus on hotels, pricing, and availability."
            ),
            Task(
                id=self._generate_task_id(),
                agent_name="activity_specialist",
                content=f"Find exciting activities and attractions for: {query}. Include ratings, descriptions, and booking info."
            ),
            Task(
                id=self._generate_task_id(),
                agent_name="transport_specialist",
                content=f"Research transportation options for: {query}. Include flights, local transport, and logistics."
            )
        ]
        
        print(Fore.YELLOW + f"Executing {len(parallel_tasks)} specialist tasks in parallel...")
        specialist_results = self.execute_parallel_tasks(parallel_tasks)
        
        # Phase 3: Synthesis by coordinator
        synthesis_content = f"""
Original Query: {query}

Specialist Results:
Hotel Specialist: {specialist_results[parallel_tasks[0].id].result}

Activity Specialist: {specialist_results[parallel_tasks[1].id].result}

Transport Specialist: {specialist_results[parallel_tasks[2].id].result}

Please synthesize these results into a comprehensive trip plan with proper JSON structure as specified in your system prompt.
"""
        
        synthesis_task = Task(
            id=self._generate_task_id(),
            agent_name="trip_coordinator",
            content=synthesis_content
        )
        
        print(Fore.YELLOW + f"Coordinator synthesizing results...")
        synthesis_results = self.execute_parallel_tasks([synthesis_task])
        final_plan = synthesis_results[synthesis_task.id].result
        
        # Phase 4: Validation
        validation_task = Task(
            id=self._generate_task_id(),
            agent_name="trip_validator",
            content=f"Validate and improve this trip plan: {final_plan}"
        )
        
        print(Fore.YELLOW + f"Validator reviewing final plan...")
        validation_results = self.execute_parallel_tasks([validation_task])
        
        # Final output
        print(Fore.GREEN + Style.BRIGHT + f"\n=== Trip Planning Complete ===")
        
        return final_plan
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get statistics about task execution"""
        stats = {
            "total_agents": len(self.registry.agents),
            "specialists": len([a for a in self.registry.agents.values() if a.role == AgentRole.SPECIALIST]),
            "coordinators": len([a for a in self.registry.agents.values() if a.role == AgentRole.COORDINATOR]),
            "validators": len([a for a in self.registry.agents.values() if a.role == AgentRole.VALIDATOR])
        }
        return stats

# Example usage
def demo_hierarchical_parallel_system():
    """Demonstrate the hierarchical parallel system"""
    
    print(Fore.CYAN + Style.BRIGHT + "\n=== Hierarchical Parallel Trip Planning Demo ===\n")
    
    # Create the system
    orchestrator = HierarchicalTripOrchestrator(max_workers=6)
    agents = orchestrator.create_hierarchical_trip_system()
    
    # Display system stats
    stats = orchestrator.get_execution_stats()
    print(Fore.BLUE + f"System Stats: {stats}")
    
    # Test query
    query = "Plan a 5-day cultural trip to Japan for 2 people, budget $4000, interested in temples, food tours, and traditional experiences"
    
    start_time = time.time()
    result = orchestrator.plan_trip_hierarchically(query)
    end_time = time.time()
    
    print(Fore.GREEN + f"\nExecution Time: {end_time - start_time:.2f} seconds")
    print(Fore.GREEN + f"\nFinal Trip Plan:\n{result}")
    
    return result

# Tool integration example
def integrate_with_existing_tools(orchestrator: HierarchicalTripOrchestrator):
    """Show how to integrate your existing tools"""
    
    # Get agents and add your existing tools
    hotel_agent = orchestrator.registry.get_agent("hotel_specialist")
    activity_agent = orchestrator.registry.get_agent("activity_specialist") 
    search_agent = orchestrator.registry.get_agent("search_specialist")
    
    if hotel_agent:
        # hotel_agent.tools.append(get_hotels_tool)  # Add your hotel tool
        pass
        
    if activity_agent:
        # activity_agent.tools.append(get_activity_tool)  # Add your activity tool
        pass
        
    if search_agent:
        # search_agent.tools.extend([get_search_results_tool, get_raw_website_content_tool])
        pass
    
    print(Fore.GREEN + "Tools integrated with specialized agents")

if __name__ == "__main__":
    demo_hierarchical_parallel_system()