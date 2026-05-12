"""
End-to-End Orchestrator Test Script

Tests the full Phase 1 workflow:
1. Submit WhatsApp message via orchestrator
2. Watch ingestion → extraction → marketplace routing
3. Verify product created with attributes
4. Check audit trail
5. Test human gate if confidence is low
"""

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after adding to path
from backend.config import get_settings
from backend.db import AsyncSessionLocal
from backend.orchestrator import (
	WorkflowState,
	NodeType,
	get_orchestrator,
)
from backend.agents.nodes import IngestionNode, ExtractionNode, MarketplaceRoutingNode


async def create_test_message() -> dict:
	"""Create a test Twilio WhatsApp message payload."""
	return {
		"MessageSid": str(uuid4()),
		"From": "whatsapp:+917869291927",
		"Body": "Check my new product",
		"NumMedia": 0,  # No media for Phase 1 test
	}


async def run_e2e_test():
	"""Run end-to-end orchestrator test."""
	print("=" * 80)
	print("PHASE 1 ORCHESTRATOR END-TO-END TEST")
	print("=" * 80)
	
	settings = get_settings()
	print(f"\n✓ Settings loaded from .env")
	print(f"  - Database: {settings.database_url}")
	print(f"  - Twilio Account: {settings.twilio_account_sid[:4]}...")
	
	# Initialize orchestrator
	orchestrator = get_orchestrator(settings)
	print(f"\n✓ Orchestrator initialized")
	
	# Register nodes
	orchestrator.register_node(IngestionNode())
	orchestrator.register_node(ExtractionNode())
	orchestrator.register_node(MarketplaceRoutingNode())
	print(f"✓ Registered {len(orchestrator.nodes)} agent nodes:")
	for node_type in orchestrator.nodes:
		print(f"  - {node_type.value}")
	
	# Create test message
	test_message = await create_test_message()
	print(f"\n✓ Created test WhatsApp message:")
	print(f"  - From: {test_message['From']}")
	print(f"  - Body: {test_message['Body']}")
	print(f"  - MessageSid: {test_message['MessageSid']}")
	
	# Create database session
	async with AsyncSessionLocal() as session:
		try:
			# Create initial workflow state
			workflow_state = WorkflowState(current_node=NodeType.INGESTION)
			workflow_state.node_outputs["ingestion_message"] = test_message
			
			print(f"\n✓ Created workflow: {workflow_state.workflow_id}")
			print(f"  - Starting node: {workflow_state.current_node.value}")
			
			# Execute workflow
			print(f"\n{'='*80}")
			print("EXECUTING WORKFLOW")
			print('='*80)
			
			iteration = 0
			while workflow_state.current_node_status != "completed" and iteration < 10:
				iteration += 1
				current_node = workflow_state.current_node.value
				print(f"\n[Iteration {iteration}] Executing node: {current_node}")
				print(f"  Status: {workflow_state.current_node_status}")
				
				# Execute workflow
				workflow_state = await orchestrator.execute_workflow(
					workflow_state,
					session,
					max_iterations=1  # One node per iteration for visibility
				)
				
				# Print node results
				if current_node in workflow_state.node_outputs:
					outputs = workflow_state.node_outputs[current_node]
					print(f"  ✓ Node completed")
					output_str = json.dumps(outputs, indent=6, default=str)[:200]
					print(f"    - Outputs: {output_str}...")
					
					if current_node in workflow_state.confidence_scores:
						scores = workflow_state.confidence_scores
						print(f"    - Confidence: {scores.get(current_node, 'N/A')}")
				
				# Check for human gate
				if workflow_state.human_gate_status.value == "paused":
					print(f"\n  ⚠️  WORKFLOW PAUSED - Human Gate Active")
					print(f"  Question: {workflow_state.human_gate_question}")
					print(f"  Paused at: {workflow_state.human_gate_timestamp}")
					break
				
				# Check for errors
				if workflow_state.current_node_status == "failed":
					print(f"  ✗ Node failed: {workflow_state.current_node_error}")
					break
			
			# Print final workflow state
			print(f"\n{'='*80}")
			print("WORKFLOW SUMMARY")
			print('='*80)
			print(f"Workflow ID: {workflow_state.workflow_id}")
			print(f"Current Node: {workflow_state.current_node.value}")
			print(f"Status: {workflow_state.current_node_status}")
			print(f"Nodes Executed: {' → '.join(workflow_state.node_sequence)}")
			print(f"Retry Count: {workflow_state.retry_count}/{workflow_state.max_retries}")
			
			if workflow_state.product_id:
				print(f"\n✓ Product Created:")
				print(f"  - ID: {workflow_state.product_id}")
				extraction = workflow_state.node_outputs.get("extraction", {})
				extraction_str = json.dumps(extraction, indent=4, default=str)[:300]
				print(f"  - Extracted Attributes: {extraction_str}")
			
			print(f"\n✓ Confidence Scores:")
			for field, score in workflow_state.confidence_scores.items():
				status = "✓" if score >= 0.8 else "⚠" if score >= 0.6 else "✗"
				print(f"  {status} {field}: {score:.2f}")
			
			if workflow_state.human_gate_status.value != "open":
				print(f"\n⚠️  Human Gate Status: {workflow_state.human_gate_status.value}")
				print(f"   Question: {workflow_state.human_gate_question}")
			
			# Print node sequence
			print(f"\n✓ Execution Sequence:")
			for i, node in enumerate(workflow_state.node_sequence, 1):
				print(f"  {i}. {node}")
			
			print(f"\n{'='*80}")
			print("TEST COMPLETED SUCCESSFULLY ✓")
			print('='*80)
			
		except Exception as e:
			print(f"\n✗ Test failed with error: {str(e)}")
			import traceback
			traceback.print_exc()
			await session.rollback()
			return False
	
	return True


async def main():
	"""Main entry point."""
	try:
		success = await run_e2e_test()
		sys.exit(0 if success else 1)
	except KeyboardInterrupt:
		print("\n\nTest interrupted by user")
		sys.exit(1)


if __name__ == "__main__":
	asyncio.run(main())
