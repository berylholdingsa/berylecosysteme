"""GraphQL Schema definition."""

import graphene
from src.graphql.queries.root import Query
from src.graphql.mutations.root import Mutation
from src.observability.logger import logger


# Create GraphQL schema
schema = graphene.Schema(query=Query, mutation=Mutation)


async def execute_graphql_query(query_string: str, variables: dict = None):
    """Execute GraphQL query."""
    logger.info(f"Executing GraphQL query")
    
    result = await schema.execute(query_string, variable_values=variables)
    
    if result.errors:
        logger.error(f"GraphQL errors: {result.errors}")
    
    return result


async def execute_graphql_mutation(mutation_string: str, variables: dict = None):
    """Execute GraphQL mutation."""
    logger.info(f"Executing GraphQL mutation")
    
    result = await schema.execute(mutation_string, variable_values=variables)
    
    if result.errors:
        logger.error(f"GraphQL errors: {result.errors}")
    
    return result
