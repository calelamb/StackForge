import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

from data.sample_data_loader import get_connection
from engine.intent_parser import parse_intent
from engine.executor import execute_app_components
from engine.validator import validate_and_explain
from engine.governance import run_governance_checks

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="StackForge Engine",
    description="AI Data App Factory Engine Layer",
    version="0.1.0",
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ParseIntentRequest(BaseModel):
    user_message: str
    existing_app: Optional[Dict[str, Any]] = None


class ExecuteAppRequest(BaseModel):
    app_definition: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    role: str = "analyst"


class AppResponse(BaseModel):
    app_definition: Dict[str, Any]
    execution_results: Dict[str, Any]
    validation: Dict[str, Any]
    governance: Dict[str, Any]


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.post("/parse_intent")
async def endpoint_parse_intent(request: ParseIntentRequest) -> Dict[str, Any]:
    """
    Parse user message into an app_definition.

    Input: Natural language query
    Output: JSON app definition (visualizations + filters)
    """
    try:
        logger.info(f"Parsing intent: {request.user_message[:50]}...")
        app_definition = parse_intent(
            request.user_message,
            existing_app=request.existing_app,
        )
        return {"success": True, "app_definition": app_definition}
    except Exception as e:
        logger.error(f"Parse intent failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/execute_app")
async def endpoint_execute_app(request: ExecuteAppRequest) -> AppResponse:
    """
    Execute an app definition: run all queries, validate, check governance.

    Input: app_definition + filters + role
    Output: Execution results + validation report + governance checks
    """
    try:
        logger.info(f"Executing app: {request.app_definition.get('app_title')}")

        conn = get_connection()

        # 1. Execute queries
        execution_results = execute_app_components(
            conn,
            request.app_definition,
            filters=request.filters,
        )

        # 2. Validate
        validation = validate_and_explain(
            request.app_definition,
            execution_results,
        )

        # 3. Governance
        governance = run_governance_checks(
            request.app_definition,
            role=request.role,
            execution_results=execution_results,
        )

        # Convert DataFrames to dict for JSON serialization
        for component_id, result in execution_results.items():
            if "data" in result and hasattr(result["data"], "to_dict"):
                result["data"] = result["data"].to_dict(orient="records")

        return AppResponse(
            app_definition=request.app_definition,
            execution_results=execution_results,
            validation=validation,
            governance=governance,
        )

    except Exception as e:
        logger.error(f"Execute app failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "StackForge Engine"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
