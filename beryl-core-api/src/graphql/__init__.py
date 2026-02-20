"""GraphQL gateway for Béryl ecosystem."""
from .types.schema import *
from .queries.root import Query
from .mutations.root import Mutation
__all__ = ["Query", "Mutation"]
