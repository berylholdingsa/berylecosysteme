"""GraphQL gateway route."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.graphql.schema import schema
from src.observability.logger import logger

router = APIRouter()


class GraphQLQuery(BaseModel):
    """GraphQL query request."""
    query: str
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None


class GraphQLResponse(BaseModel):
    """GraphQL response."""
    data: Optional[Dict[str, Any]]
    errors: Optional[list]


@router.post("/graphql", response_model=GraphQLResponse)
async def graphql_endpoint(request: GraphQLQuery):
    """
    GraphQL endpoint.
    
    Unified gateway for all domains:
    - Fintech queries/mutations
    - Mobility queries/mutations
    - ESG queries
    - Social queries/mutations
    """
    try:
        logger.info("GraphQL request received")
        
        result = await schema.execute(
            request.query,
            variable_values=request.variables,
            operation_name=request.operation_name
        )
        
        if result.errors:
            logger.error(f"GraphQL errors: {result.errors}")
            return GraphQLResponse(
                data=result.data,
                errors=[str(err) for err in result.errors]
            )
        
        return GraphQLResponse(data=result.data, errors=None)
        
    except Exception as e:
        logger.error(f"GraphQL error: {str(e)}")
        raise HTTPException(status_code=500, detail="GraphQL execution failed")


@router.get("/graphql/playground")
async def graphql_playground():
    """GraphQL playground (Apollo GraphQL IDE)."""
    return {
        "message": "Use POST /api/v1/graphql to execute queries",
        "playground": "https://studio.apollographql.com/"
    }
