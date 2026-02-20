"""Root Mutation type for GraphQL schema."""

import graphene


class Mutation(graphene.ObjectType):
    """Root mutation type for Béryl ecosystem."""
    
    ping = graphene.String(description="Ping mutation")
    
    def resolve_ping(self, info):
        """Ping mutation."""
        return "Pong"
