"""
Orchestrator API endpoints for workflow management.

Provides:
- POST /orchestrator/workflows - Start new workflow
- GET /orchestrator/workflows/{workflow_id} - Get workflow status
- POST /orchestrator/workflows/{workflow_id}/gate - Resolve human gate
- GET /orchestrator/workflows - List all workflows
- GET /orchestrator/paused - List paused workflows
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from ..db import get_session
from ..config import get_settings
from ..orchestrator import (
	WorkflowState,
	NodeType,
	get_orchestrator,
	AgentNodeInput,
)
from ..agents.nodes import IngestionNode, ExtractionNode, MarketplaceRoutingNode
from ..models.workflow_state import WorkflowRun

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

# Store workflows in memory for Phase 1 (will move to DB in Phase 2)
_workflows: dict[str, WorkflowState] = {}


def _to_state(row: WorkflowRun) -> WorkflowState:
	"""Convert a persisted workflow run to WorkflowState."""
	return WorkflowState.from_json(json.dumps(row.state_json))


@router.on_event("startup")
async def initialize_orchestrator():
	"""Initialize orchestrator and register nodes."""
	from ..config import get_settings
	settings = get_settings()
	orchestrator = get_orchestrator(settings)
	
	# Register agent nodes
	orchestrator.register_node(IngestionNode())
	orchestrator.register_node(ExtractionNode())
	orchestrator.register_node(MarketplaceRoutingNode())
	
	logger.info("Orchestrator initialized with nodes")


@router.post("/workflows", response_model=WorkflowState)
async def start_workflow(
	product_id: str | None = None,
	inbound_message_id: str | None = None,
	ingestion_message: dict | None = None,
	session: AsyncSession = Depends(get_session),
):
	"""
	Start a new workflow.
	
	Either provide:
	- product_id: to start from extraction on existing product
	- inbound_message_id: to load and ingest message from DB
	- ingestion_message: Twilio payload dict to start ingestion
	"""
	settings = get_settings()
	orchestrator = get_orchestrator(settings)
	
	# Create workflow state
	state = WorkflowState(
		product_id=product_id,
		inbound_message_id=inbound_message_id,
		current_node=NodeType.INGESTION,
	)
	
	# Pre-populate ingestion message if provided
	if ingestion_message:
		state.node_outputs["ingestion_message"] = ingestion_message
	
	# Execute workflow
	try:
		state = await orchestrator.execute_workflow(state, session)
		_workflows[state.workflow_id] = state
		return state
	except Exception as e:
		logger.error(f"Workflow failed: {str(e)}")
		state.current_node_status = "failed"
		state.current_node_error = str(e)
		return state


@router.get("/workflows/{workflow_id}", response_model=WorkflowState)
async def get_workflow(workflow_id: str, session: AsyncSession = Depends(get_session)):
	"""Get workflow status."""
	stored = await session.get(WorkflowRun, workflow_id)
	if stored:
		return _to_state(stored)
	workflow = _workflows.get(workflow_id)
	if not workflow:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Workflow not found"
		)
	return workflow


@router.post("/workflows/{workflow_id}/gate")
async def resolve_human_gate(
	workflow_id: str,
	response: str,
	approved: bool = True,
	session: AsyncSession = Depends(get_session),
):
	"""
	Resolve a human-in-the-loop gate and resume workflow.
	
	Args:
	- response: Human's response/clarification
	- approved: Whether human approved or rejected
	"""
	settings = get_settings()
	orchestrator = get_orchestrator(settings)
	human_gate_service = orchestrator.get_human_gate_service()
	
	# Resolve gate
	state = human_gate_service.resolve_gate(workflow_id, response, approved)
	if not state:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Paused workflow not found"
		)
	
	# If approved, resume execution
	if approved:
		try:
			state = await orchestrator.execute_workflow(state, session)
			_workflows[state.workflow_id] = state
			return {"status": "resumed", "workflow": state}
		except Exception as e:
			logger.error(f"Resume failed: {str(e)}")
			return {"status": "error", "error": str(e)}
	else:
		return {"status": "rejected", "workflow": state}


@router.get("/workflows", response_model=list[WorkflowState])
async def list_workflows(limit: int = 100, session: AsyncSession = Depends(get_session)):
	"""List all workflows."""
	result = await session.execute(
		select(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(limit)
	)
	rows = result.scalars().all()
	if rows:
		return [_to_state(row) for row in rows]
	workflows = list(_workflows.values())
	return workflows[-limit:]


@router.get("/paused", response_model=list[WorkflowState])
async def list_paused_workflows():
	"""List paused workflows awaiting human input."""
	settings = get_settings()
	orchestrator = get_orchestrator(settings)
	human_gate_service = orchestrator.get_human_gate_service()
	return human_gate_service.list_paused_workflows()


@router.get("/health")
async def orchestrator_health():
	"""Health check for orchestrator."""
	settings = get_settings()
	orchestrator = get_orchestrator(settings)
	return {
		"status": "healthy",
		"nodes_registered": len(orchestrator.nodes),
		"workflows_active": len(_workflows),
	}
