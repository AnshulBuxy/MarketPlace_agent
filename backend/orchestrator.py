"""
Agent Orchestrator - Core engine for agent workflow execution.

Implements:
- WorkflowState: Data model for workflow state and transitions
- AgentNodeContract: Interface for agent nodes  
- ModelRouter: LLM selection based on task type
- ToolRegistry: Centralized tool interface for agents
- HumanGateService: Pause/resume logic for human-in-the-loop
- AgentOrchestrator: Graph runner using LangGraph for state management
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from .services.storage import StorageService

logger = logging.getLogger(__name__)


# ============================================================================
# 1. WORKFLOW STATE MODELS
# ============================================================================

class NodeType(str, Enum):
	"""Agent node types in the workflow."""
	INGESTION = "ingestion"
	EXTRACTION = "extraction"
	MARKETPLACE_ROUTING = "marketplace_routing"
	PRICING = "pricing"
	CATALOG_GENERATION = "catalog_generation"
	PUBLISHING = "publishing"
	NOTIFICATION = "notification"


class HumanGateStatus(str, Enum):
	"""Status of human-in-the-loop gate."""
	OPEN = "open"  # Waiting for human input
	PAUSED = "paused"  # Workflow paused
	APPROVED = "approved"  # Human approved
	REJECTED = "rejected"  # Human rejected
	INFO_PROVIDED = "info_provided"  # Human provided clarification


class WorkflowState(BaseModel):
	"""Complete workflow state for a product."""
	
	workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
	product_id: Optional[str] = None
	artisan_id: Optional[str] = None
	inbound_message_id: Optional[str] = None
	contact_number: Optional[str] = None
	
	current_node: NodeType = NodeType.INGESTION
	current_node_status: str = "pending"  # pending, running, completed, failed
	current_node_error: Optional[str] = None
	
	# Node outputs - stored as JSON for flexibility
	node_outputs: dict[str, Any] = Field(default_factory=dict)
	
	# Confidence scores per field
	confidence_scores: dict[str, float] = Field(default_factory=dict)
	
	# Human gate state
	human_gate_status: HumanGateStatus = HumanGateStatus.OPEN
	human_gate_question: Optional[str] = None  # Clarification question
	human_gate_response: Optional[str] = None  # Human's response
	human_gate_timestamp: Optional[datetime] = None
	
	# Retry tracking
	retry_count: int = 0
	max_retries: int = 3
	
	# Audit trail
	node_sequence: list[str] = Field(default_factory=list)  # Track which nodes ran
	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: datetime = Field(default_factory=datetime.utcnow)
	
	# Next node to execute
	next_node: Optional[NodeType] = None
	
	def to_json(self) -> str:
		"""Serialize state to JSON."""
		return json.dumps(self.model_dump(mode="json"), default=str)
	
	@classmethod
	def from_json(cls, json_str: str) -> WorkflowState:
		"""Deserialize state from JSON."""
		return cls(**json.loads(json_str))


# ============================================================================
# 2. AGENT NODE CONTRACT
# ============================================================================

class AgentNodeInput(BaseModel):
	"""Input contract for agent nodes."""
	workflow_state: WorkflowState
	session: Any = None  # AsyncSession - allow arbitrary types
	settings: Any = None  # Settings object
	
	model_config = {"arbitrary_types_allowed": True}


class AgentNodeOutput(BaseModel):
	"""Output contract for agent nodes."""
	success: bool
	next_node: Optional[NodeType] = None
	error: Optional[str] = None
	node_outputs: dict[str, Any] = Field(default_factory=dict)
	confidence_scores: dict[str, float] = Field(default_factory=dict)
	human_gate_question: Optional[str] = None  # If node needs clarification


class AgentNodeContract:
	"""Interface for agent nodes."""
	
	def __init__(self, node_type: NodeType):
		self.node_type = node_type
	
	async def execute(self, node_input: AgentNodeInput) -> AgentNodeOutput:
		"""Execute agent logic. Must be overridden."""
		raise NotImplementedError(f"execute not implemented for {self.node_type}")


# ============================================================================
# 3. MODEL ROUTER - LLM Selection Service
# ============================================================================

class ModelConfig(BaseModel):
	"""Configuration for LLM usage."""
	provider: str  # "gemini", "huggingface", "groq"
	model_name: str
	temperature: float = 0.7
	max_tokens: int = 1000
	system_prompt: Optional[str] = None


class ModelRouter:
	"""Routes tasks to appropriate LLM based on requirements."""
	
	def __init__(self):
		"""Initialize model router with default mappings."""
		self.task_models: dict[str, ModelConfig] = {
			"extraction": ModelConfig(
				provider="gemini",
				model_name="gemini-1.5-flash",
				temperature=0.3,
				max_tokens=2000,
				system_prompt="You are an expert product attribute extractor. Extract structured attributes from product images and descriptions."
			),
			"marketplace_routing": ModelConfig(
				provider="gemini",
				model_name="gemini-1.5-flash",
				temperature=0.2,
				max_tokens=500,
				system_prompt="You are a marketplace expert. Route products to the best marketplace."
			),
			"pricing": ModelConfig(
				provider="groq",  # Fast LLM for pricing
				model_name="mixtral-8x7b-32768",
				temperature=0.1,
				max_tokens=300,
				system_prompt="You are a pricing expert. Suggest optimal prices for products."
			),
			"catalog_generation": ModelConfig(
				provider="gemini",
				model_name="gemini-1.5-flash",
				temperature=0.5,
				max_tokens=1500,
				system_prompt="You are a catalog expert. Generate engaging product descriptions and titles."
			),
		}
	
	def get_model(self, task_name: str) -> ModelConfig:
		"""Get model config for task."""
		return self.task_models.get(task_name, self.task_models["extraction"])
	
	def set_model(self, task_name: str, config: ModelConfig) -> None:
		"""Override model for a task."""
		self.task_models[task_name] = config


# ============================================================================
# 4. TOOL REGISTRY - Centralized Tool Interface
# ============================================================================

class ToolRegistry:
	"""Registry of all tools available to agents."""
	
	def __init__(self, session: AsyncSession, settings: Any):
		self.session = session
		self.settings = settings
		self.tools: dict[str, Callable] = {}
		self._register_default_tools()
	
	def _register_default_tools(self) -> None:
		"""Register default tools."""
		# Tools for agent use - these are service methods available as tools
		# Will be expanded in Phase 2 with actual LLM integration
		self.tools["whatsapp_send"] = self._whatsapp_send_wrapper
	
	async def _whatsapp_send_wrapper(self, to_number: str, body: str) -> dict:
		"""Wrapper for sending WhatsApp messages."""
		try:
			from .services.whatsapp import send_twilio_whatsapp_message
			logger.info("WhatsApp send: to=%s body=%s", to_number, (body or "")[:160])
			result = await send_twilio_whatsapp_message(
				self.settings,
				to_number,
				body
			)
			logger.info("WhatsApp sent: to=%s sid=%s", to_number, result.message_sid)
			return {"success": True, "message_sid": result.message_sid}
		except Exception as e:
			logger.error("WhatsApp send failed: to=%s error=%s", to_number, str(e))
			return {"success": False, "error": str(e)}
	
	def register(self, name: str, func: Callable) -> None:
		"""Register a tool."""
		self.tools[name] = func
	
	async def call(self, tool_name: str, **kwargs) -> Any:
		"""Call a tool by name."""
		if tool_name not in self.tools:
			raise ValueError(f"Tool not found: {tool_name}")
		
		tool = self.tools[tool_name]
		try:
			result = tool(**kwargs)
			if hasattr(result, "__await__"):
				return await result
			return result
		except Exception as e:
			logger.error(f"Tool {tool_name} failed: {str(e)}")
			raise


# ============================================================================
# 5. HUMAN GATE SERVICE - Pause/Resume Logic
# ============================================================================

class HumanGateService:
	"""Manages human-in-the-loop gates."""
	
	def __init__(self):
		self.paused_workflows: dict[str, WorkflowState] = {}
		self.gate_responses: dict[str, str] = {}
	
	def trigger_clarification_gate(
		self,
		state: WorkflowState,
		question: str,
		confidence_threshold: float = 0.7
	) -> bool:
		"""Check if clarification gate should be triggered based on confidence."""
		if not state.confidence_scores:
			return False
		
		avg_confidence = sum(state.confidence_scores.values()) / len(state.confidence_scores)
		if avg_confidence < confidence_threshold:
			state.human_gate_status = HumanGateStatus.PAUSED
			state.human_gate_question = question
			state.human_gate_timestamp = datetime.utcnow()
			self.paused_workflows[state.workflow_id] = state
			logger.info(f"Workflow {state.workflow_id} paused for clarification")
			return True
		return False
	
	def trigger_approval_gate(self, state: WorkflowState, description: str = "") -> None:
		"""Trigger approval gate before publishing."""
		state.human_gate_status = HumanGateStatus.PAUSED
		state.human_gate_question = f"Approve before publishing: {description}"
		state.human_gate_timestamp = datetime.utcnow()
		self.paused_workflows[state.workflow_id] = state
		logger.info(f"Workflow {state.workflow_id} paused for approval")
	
	def resolve_gate(self, workflow_id: str, response: str, approved: bool = True) -> Optional[WorkflowState]:
		"""Resolve a human gate with response."""
		state = self.paused_workflows.get(workflow_id)
		if not state:
			return None
		
		state.human_gate_response = response
		state.human_gate_status = HumanGateStatus.APPROVED if approved else HumanGateStatus.REJECTED
		self.gate_responses[workflow_id] = response
		
		if workflow_id in self.paused_workflows:
			del self.paused_workflows[workflow_id]
		
		logger.info(f"Workflow {workflow_id} gate resolved: {state.human_gate_status}")
		return state
	
	def get_paused_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
		"""Get a paused workflow."""
		return self.paused_workflows.get(workflow_id)
	
	def list_paused_workflows(self) -> list[WorkflowState]:
		"""List all paused workflows."""
		return list(self.paused_workflows.values())


# ============================================================================
# 6. AGENT ORCHESTRATOR - Graph Runner
# ============================================================================

class AgentOrchestrator:
	"""Main orchestrator for agent workflow execution using LangGraph patterns."""
	
	def __init__(self, settings: Any):
		self.settings = settings
		self.model_router = ModelRouter()
		self.human_gate_service = HumanGateService()
		self.nodes: dict[NodeType, AgentNodeContract] = {}
		self.logger = logging.getLogger(__name__)
	
	def register_node(self, node: AgentNodeContract) -> None:
		"""Register an agent node."""
		self.nodes[node.node_type] = node
		self.logger.info(f"Registered node: {node.node_type}")

	async def _persist_state(self, session: AsyncSession, state: WorkflowState) -> None:
		"""Persist workflow state for history and API visibility."""
		from .models.workflow_state import WorkflowRun
		payload = state.model_dump(mode="json")
		stored = await session.get(WorkflowRun, state.workflow_id)
		if stored:
			stored.status = state.current_node_status
			stored.current_node = state.current_node.value
			stored.human_gate_status = state.human_gate_status.value
			stored.contact_number = state.contact_number
			stored.product_id = state.product_id
			stored.state_json = payload
		else:
			stored = WorkflowRun(
				workflow_id=state.workflow_id,
				status=state.current_node_status,
				current_node=state.current_node.value,
				human_gate_status=state.human_gate_status.value,
				contact_number=state.contact_number,
				product_id=state.product_id,
				state_json=payload,
			)
			session.add(stored)
		await session.flush()
	
	async def execute_workflow(
		self,
		state: WorkflowState,
		session: AsyncSession,
		max_iterations: int = 10
	) -> WorkflowState:
		"""
		Execute workflow from current state.
		
		Handles:
		- Node execution with retries
		- Human gate pausing/resuming
		- State transitions
		- Audit trail
		"""
		self.logger.info(
			"Workflow start: id=%s current_node=%s status=%s",
			state.workflow_id,
			state.current_node,
			state.current_node_status,
		)
		iteration = 0
		
		while iteration < max_iterations and state.current_node_status != "completed":
			iteration += 1
			self.logger.info(
				"Workflow iteration: id=%s iteration=%s node=%s status=%s",
				state.workflow_id,
				iteration,
				state.current_node,
				state.current_node_status,
			)
			
			# Check if workflow was paused at human gate
			if state.human_gate_status == HumanGateStatus.PAUSED and state.human_gate_response:
				state.human_gate_status = HumanGateStatus.INFO_PROVIDED
				self.logger.info(
					"Workflow resume from gate: id=%s response=%s",
					state.workflow_id,
					(state.human_gate_response or "")[:120],
				)
			
			# Get node
			node = self.nodes.get(state.current_node)
			if not node:
				state.current_node_status = "failed"
				state.current_node_error = f"Node not registered: {state.current_node}"
				self.logger.error(state.current_node_error)
				break
			
			# Create tool registry for this execution
			tool_registry = ToolRegistry(session, self.settings)
			
			# Execute node with retries
			try:
				node_input = AgentNodeInput(
					workflow_state=state,
					session=session,
					settings=self.settings
				)
				self.logger.info(
					"Node start: workflow=%s node=%s",
					state.workflow_id,
					state.current_node,
				)
				
				output = await node.execute(node_input)
				
				# Process output
				if output.success:
					state.current_node_status = "completed"
					self.logger.info(
						"Node success: workflow=%s node=%s next=%s",
						state.workflow_id,
						state.current_node,
						output.next_node,
					)
					state.node_outputs[state.current_node.value] = output.node_outputs
					state.confidence_scores.update(output.confidence_scores)
					state.node_sequence.append(state.current_node.value)
					if output.node_outputs.get("contact_number"):
						state.contact_number = output.node_outputs.get("contact_number")
					if output.node_outputs.get("product_id"):
						state.product_id = output.node_outputs.get("product_id")
					
					# Check if human gate needed
					if output.human_gate_question:
						self.human_gate_service.trigger_clarification_gate(
							state,
							output.human_gate_question,
							confidence_threshold=0.7
						)
						state.human_gate_question = output.human_gate_question
						if output.next_node:
							state.current_node = output.next_node
							state.current_node_status = "pending"
						self.logger.info(
							"Gate triggered: workflow=%s node=%s question=%s",
							state.workflow_id,
							state.current_node,
							(output.human_gate_question or "")[:160],
						)
						if state.contact_number:
							try:
								enhanced_url = output.node_outputs.get("enhanced_media_url")
								if enhanced_url:
									storage = StorageService(self.settings)
									preview_url = storage.presign_s3_url(enhanced_url, expires_in=3600)
									from .services.whatsapp import send_twilio_whatsapp_media_message
									await send_twilio_whatsapp_media_message(
										self.settings,
										to_number=state.contact_number,
										body="Enhanced preview attached.",
										media_url=preview_url,
									)
									self.logger.info(
										"Enhanced preview sent: workflow=%s to=%s",
										state.workflow_id,
										state.contact_number,
									)
								await tool_registry.call(
									"whatsapp_send",
									to_number=state.contact_number,
									body=output.human_gate_question,
								)
								self.logger.info(
									"Gate prompt sent: workflow=%s to=%s",
									state.workflow_id,
									state.contact_number,
								)
							except Exception as exc:
								self.logger.error(f"Failed to send gate prompt: {exc}")
						await self._persist_state(session, state)
						break  # Pause workflow
					
					# Transition to next node
					if output.next_node:
						state.current_node = output.next_node
						state.current_node_status = "pending"
					else:
						state.current_node_status = "completed"
						break
				
				else:
					# Node failed
					state.retry_count += 1
					if state.retry_count >= state.max_retries:
						state.current_node_status = "failed"
						state.current_node_error = output.error
						self.logger.error(f"Node {state.current_node} failed after retries: {output.error}")
						break
					else:
						self.logger.warning(f"Node {state.current_node} failed, retrying. Attempt {state.retry_count}/{state.max_retries}")
						state.current_node_status = "pending"
				
			except Exception as e:
				state.retry_count += 1
				if state.retry_count >= state.max_retries:
					state.current_node_status = "failed"
					state.current_node_error = str(e)
					self.logger.error(f"Exception in node {state.current_node}: {str(e)}")
					break
				else:
					self.logger.warning(f"Exception in node {state.current_node}, retrying: {str(e)}")
					state.current_node_status = "pending"
			
			state.updated_at = datetime.utcnow()
			await self._persist_state(session, state)
			self.logger.info(
				"Workflow state saved: id=%s node=%s status=%s",
				state.workflow_id,
				state.current_node,
				state.current_node_status,
			)
		
		return state
	
	def get_human_gate_service(self) -> HumanGateService:
		"""Get human gate service for admin APIs."""
		return self.human_gate_service
	
	def get_model_router(self) -> ModelRouter:
		"""Get model router for task-specific LLM selection."""
		return self.model_router


# Global orchestrator instance
_orchestrator_instance: Optional[AgentOrchestrator] = None


def get_orchestrator(settings: Any = None) -> AgentOrchestrator:
	"""Get or create global orchestrator instance."""
	global _orchestrator_instance
	if _orchestrator_instance is None:
		if settings is None:
			from .config import get_settings
			settings = get_settings()
		_orchestrator_instance = AgentOrchestrator(settings)
	return _orchestrator_instance
