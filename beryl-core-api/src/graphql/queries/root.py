"""Root Query type for GraphQL schema."""

import graphene
from datetime import datetime


class Query(graphene.ObjectType):
    """Root query type for Béryl ecosystem."""
    
    health = graphene.String(description="Health check endpoint")
    
    def resolve_health(self, info):
        """Health check."""
        return "Béryl GraphQL Gateway - OK"
