"""
Sentinell Agent - The Brain

LangGraph-based agent that autonomously detects, diagnoses, and fixes issues.

State Machine:
detect -> retrieve_docs -> plan -> human_approval -> act -> verify
"""
import logging
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from .tools import ALL_TOOLS, read_logs, exec_command, restart_container
from .rag import get_rag

logger = logging.getLogger(__name__)


# Agent State
class AgentState(TypedDict):
    """State passed between agent nodes."""
    # Input
    problem_description: str
    container_name: str

    # Detection
    logs: str
    detected_issue: str

    # Retrieval
    relevant_docs: str

    # Planning
    diagnosis: str
    proposed_fix: str
    fix_steps: list[str]

    # Human approval
    human_approved: bool
    human_feedback: str

    # Execution
    execution_log: list[str]
    fix_applied: bool

    # Verification
    verification_result: str
    issue_resolved: bool

    # Meta
    current_step: str
    error: str


class SentinellAgent:
    """The autonomous SRE agent."""

    def __init__(self, model_name: str = "claude-3-haiku-20240307"):
        """
        Initialize the Sentinell agent.

        Args:
            model_name: Claude model to use (default: claude-3-haiku-20240307 for speed/cost)
        """
        self.model = ChatAnthropic(model=model_name, temperature=0)
        self.rag = get_rag()

        # Build the state graph
        self.graph = self._build_graph()
        logger.info(f"🧠 Sentinell Agent initialized with {model_name}")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("detect", self._detect_node)
        workflow.add_node("retrieve_docs", self._retrieve_docs_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("verify", self._verify_node)

        # Set entry point
        workflow.set_entry_point("detect")

        # Add edges
        workflow.add_edge("detect", "retrieve_docs")
        workflow.add_edge("retrieve_docs", "plan")
        workflow.add_edge("plan", "human_approval")

        # Conditional edge based on human approval
        workflow.add_conditional_edges(
            "human_approval",
            self._should_execute,
            {
                "execute": "act",
                "abort": END
            }
        )

        workflow.add_edge("act", "verify")
        workflow.add_edge("verify", END)

        return workflow.compile()

    def _detect_node(self, state: AgentState) -> AgentState:
        """
        Detection node: Analyze logs and identify the issue.
        """
        logger.info("🔍 [DETECT] Analyzing logs...")
        state["current_step"] = "detect"

        try:
            # Read logs from the container
            container_name = state["container_name"]
            logs = read_logs.invoke({"container_name": container_name, "tail": 100})
            state["logs"] = logs

            # Use LLM to detect issue
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert SRE analyzing container logs.
Identify the main issue from the logs. Be specific about:
- What is failing
- Error messages
- Patterns in the logs

Keep it concise and technical."""),
                HumanMessage(content=f"""Container: {container_name}
Problem reported: {state['problem_description']}

Logs:
{logs}

What is the specific issue?""")
            ])

            response = self.model.invoke(prompt.format_messages())
            state["detected_issue"] = response.content

            logger.info(f"✅ [DETECT] Issue identified: {response.content[:100]}...")

        except Exception as e:
            logger.error(f"❌ [DETECT] Error: {e}")
            state["error"] = str(e)
            state["detected_issue"] = f"Detection failed: {e}"

        return state

    def _retrieve_docs_node(self, state: AgentState) -> AgentState:
        """
        Retrieval node: Query RAG for relevant documentation.
        """
        logger.info("📚 [RETRIEVE] Searching knowledge base...")
        state["current_step"] = "retrieve_docs"

        try:
            issue = state["detected_issue"]
            relevant_docs = self.rag.get_relevant_context(issue)
            state["relevant_docs"] = relevant_docs

            logger.info(f"✅ [RETRIEVE] Found relevant documentation")

        except Exception as e:
            logger.error(f"❌ [RETRIEVE] Error: {e}")
            state["error"] = str(e)
            state["relevant_docs"] = "No documentation found."

        return state

    def _plan_node(self, state: AgentState) -> AgentState:
        """
        Planning node: Create a diagnosis and fix plan.
        """
        logger.info("🎯 [PLAN] Creating fix plan...")
        state["current_step"] = "plan"

        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert SRE creating a fix plan.

Based on the issue and documentation, provide:
1. A clear diagnosis
2. Specific steps to fix the issue
3. Expected outcome

Be precise and actionable. Only suggest fixes you are confident about."""),
                HumanMessage(content=f"""Issue Detected:
{state['detected_issue']}

Relevant Documentation:
{state['relevant_docs']}

Container: {state['container_name']}

Provide:
1. DIAGNOSIS: What exactly is wrong
2. FIX PLAN: Step-by-step commands to fix it
3. EXPECTED OUTCOME: What should happen after the fix""")
            ])

            response = self.model.invoke(prompt.format_messages())
            plan_content = response.content

            state["diagnosis"] = plan_content
            state["proposed_fix"] = plan_content

            # Parse steps (simple line-based parsing)
            steps = []
            for line in plan_content.split('\n'):
                if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                    steps.append(line.strip())

            state["fix_steps"] = steps if steps else ["Fix plan available in diagnosis"]

            logger.info(f"✅ [PLAN] Fix plan created with {len(steps)} steps")

        except Exception as e:
            logger.error(f"❌ [PLAN] Error: {e}")
            state["error"] = str(e)
            state["diagnosis"] = f"Planning failed: {e}"
            state["proposed_fix"] = ""
            state["fix_steps"] = []

        return state

    def _human_approval_node(self, state: AgentState) -> AgentState:
        """
        Human approval node: Wait for human to approve/reject the plan.

        This is a placeholder - in the API, we'll return here and wait for approval.
        """
        logger.info("👤 [APPROVAL] Waiting for human approval...")
        state["current_step"] = "human_approval"

        # In actual implementation, this returns to API and waits
        # For now, we mark as pending
        if "human_approved" not in state:
            state["human_approved"] = False
            state["human_feedback"] = "Pending approval"

        return state

    def _should_execute(self, state: AgentState) -> Literal["execute", "abort"]:
        """Decide whether to execute the fix or abort."""
        if state.get("human_approved", False):
            return "execute"
        else:
            return "abort"

    def _act_node(self, state: AgentState) -> AgentState:
        """
        Execution node: Apply the fix.
        """
        logger.info("⚙️ [ACT] Applying fix...")
        state["current_step"] = "act"

        execution_log = []

        try:
            # This is simplified - in reality, we'd parse the fix plan
            # and execute specific tools based on the diagnosis

            container_name = state["container_name"]

            # Example: If it's an nginx issue, try to reload
            if "nginx" in container_name.lower():
                # Test nginx config
                result = exec_command.invoke({
                    "container_name": container_name,
                    "command": "nginx -t"
                })
                execution_log.append(f"Config test: {result}")

                # If config is ok, reload
                if "successful" in result.lower() or "ok" in result.lower():
                    reload_result = exec_command.invoke({
                        "container_name": container_name,
                        "command": "nginx -s reload"
                    })
                    execution_log.append(f"Reload: {reload_result}")
                    state["fix_applied"] = True
                else:
                    # Config has errors - would need to patch
                    execution_log.append("Config has errors - would need manual patching")
                    state["fix_applied"] = False
            else:
                # Generic fix: restart container
                restart_result = restart_container.invoke({"container_name": container_name})
                execution_log.append(f"Restart: {restart_result}")
                state["fix_applied"] = True

            state["execution_log"] = execution_log
            logger.info(f"✅ [ACT] Fix applied: {state['fix_applied']}")

        except Exception as e:
            logger.error(f"❌ [ACT] Error: {e}")
            state["error"] = str(e)
            state["execution_log"] = [f"Execution failed: {e}"]
            state["fix_applied"] = False

        return state

    def _verify_node(self, state: AgentState) -> AgentState:
        """
        Verification node: Check if the fix worked.
        """
        logger.info("✔️ [VERIFY] Verifying fix...")
        state["current_step"] = "verify"

        try:
            # Read logs again to see if error is gone
            container_name = state["container_name"]
            new_logs = read_logs.invoke({"container_name": container_name, "tail": 50})

            # Use LLM to verify
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are verifying if an issue was fixed. Compare logs and determine if the issue is resolved."),
                HumanMessage(content=f"""Original Issue:
{state['detected_issue']}

Fix Applied:
{state['execution_log']}

New Logs:
{new_logs}

Is the issue resolved? Answer with: RESOLVED or NOT_RESOLVED, followed by explanation.""")
            ])

            response = self.model.invoke(prompt.format_messages())
            verification = response.content

            state["verification_result"] = verification
            state["issue_resolved"] = "RESOLVED" in verification.upper()

            logger.info(f"✅ [VERIFY] Verification complete: {state['issue_resolved']}")

        except Exception as e:
            logger.error(f"❌ [VERIFY] Error: {e}")
            state["error"] = str(e)
            state["verification_result"] = f"Verification failed: {e}"
            state["issue_resolved"] = False

        return state

    def analyze(self, problem_description: str, container_name: str) -> AgentState:
        """
        Run the agent on a problem.

        Args:
            problem_description: Human description of the problem
            container_name: Name of the affected container

        Returns:
            Final agent state
        """
        initial_state = AgentState(
            problem_description=problem_description,
            container_name=container_name,
            logs="",
            detected_issue="",
            relevant_docs="",
            diagnosis="",
            proposed_fix="",
            fix_steps=[],
            human_approved=False,
            human_feedback="",
            execution_log=[],
            fix_applied=False,
            verification_result="",
            issue_resolved=False,
            current_step="init",
            error=""
        )

        logger.info(f"🚀 Starting analysis for {container_name}: {problem_description}")

        try:
            # Run until human approval node
            final_state = self.graph.invoke(initial_state)
            return final_state

        except Exception as e:
            logger.error(f"❌ Agent error: {e}")
            initial_state["error"] = str(e)
            initial_state["current_step"] = "error"
            return initial_state

    def approve_and_execute(self, state: AgentState, approved: bool, feedback: str = "") -> AgentState:
        """
        Continue execution after human approval.

        Args:
            state: Current agent state (from human_approval node)
            approved: Whether human approved the fix
            feedback: Optional feedback from human

        Returns:
            Final agent state after execution
        """
        state["human_approved"] = approved
        state["human_feedback"] = feedback

        logger.info(f"👤 Human decision: {'APPROVED' if approved else 'REJECTED'}")

        if not approved:
            logger.info("❌ Fix rejected by human")
            return state

        try:
            # Continue from human_approval node
            final_state = self.graph.invoke(state)
            return final_state

        except Exception as e:
            logger.error(f"❌ Agent error during execution: {e}")
            state["error"] = str(e)
            state["current_step"] = "error"
            return state
