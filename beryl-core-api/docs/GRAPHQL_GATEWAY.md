# GraphQL Gateway - Béryl Ecosystem

## Overview

Unified GraphQL gateway providing access to all domains:
- **Fintech**: Wallets, transactions, payments
- **Mobility**: Rides, vehicles, fleet
- **ESG**: Scores, health, sustainability
- **Social**: Posts, feed, recommendations

## Architecture

```
GraphQL Gateway (Single Entry Point)
    ↓
Query/Mutation Resolvers
    ↓
Domain Orchestration Layers
    ↓
Domain Adapters → External APIs
    ↓
Event Bus (Async Communication)
```

## Example Queries

### Get User Wallet (Fintech)
```graphql
query {
  userWallet(userId: "user_123") {
    id
    balance
    currency
    status
    transactions(limit: 10) {
      id
      amount
      type
      createdAt
    }
  }
}
```

### Get User Rides (Mobility)
```graphql
query {
  userRides(userId: "user_123") {
    id
    startLocation
    endLocation
    distance
    status
    createdAt
  }
}
```

### Get ESG Profile (ESG)
```graphql
query {
  userEsgProfile(userId: "user_123") {
    userId
    esgScore {
      environmental
      social
      governance
      overall
    }
    carbonFootprint
    greenScore
  }
}
```

### Get Personalized Feed (Social)
```graphql
query {
  userFeed(userId: "user_123", pagination: {limit: 20, offset: 0}) {
    userId
    items {
      id
      content
      authorId
      engagementScore
      likesCount
      commentsCount
    }
    totalItems
    generatedAt
  }
}
```

## Example Mutations

### Process Payment (Fintech)
```graphql
mutation {
  processPayment(input: {
    userId: "user_123"
    amount: 50.0
    method: "wallet"
  }) {
    success
    message
  }
}
```

### Create Ride (Mobility)
```graphql
mutation {
  createRide(input: {
    userId: "user_123"
    startLocation: "Paris"
    endLocation: "Lyon"
  }) {
    id
    status
    cost
  }
}
```

### Create Post (Social)
```graphql
mutation {
  createPost(input: {
    userId: "user_123"
    content: "Just completed a sustainable ride!"
    contentType: "text"
  }) {
    id
    content
    authorId
    createdAt
  }
}
```

## Installation

### Add GraphQL dependencies to pyproject.toml:

```toml
graphene = "^3.3"
graphene-django = "^3.1"
strawberry-graphql = "^0.200"  # Alternative to Graphene
```

### Install:
```bash
pip install graphene strawberry-graphql graphene-django
```

## Integration Points

### 1. Query Resolvers
Connect to orchestration layers:
```python
async def resolve_user_wallet(self, info, user_id):
    # Call Fintech adapter
    orchestrator = FintechPaymentWorkflow()
    wallet = await orchestrator.get_wallet(user_id)
    return wallet
```

### 2. Mutation Resolvers
Trigger domain workflows + events:
```python
async def resolve_process_payment(self, info, input):
    # Call Fintech workflow
    workflow = FintechPaymentWorkflow()
    result = await workflow.process_payment(
        user_id=input.user_id,
        amount=input.amount
    )
    # Event is automatically published
    return result
```

### 3. Event Subscriptions (Real-time)
```graphql
subscription {
  onTransactionCompleted(userId: "user_123") {
    transactionId
    amount
    status
  }
}
```

## Schema Structure

### User (Root Entity)
```
User
├── id: String!
├── email: String!
├── wallet: Wallet (Fintech)
├── rides: [Ride] (Mobility)
├── posts: [Post] (Social)
└── esgProfile: EsgProfile (ESG)
```

### Cross-Domain Queries
- Query by user ID returns data from all domains
- Each domain can subscribe to events from others
- No direct cross-domain calls (event-driven)

## Performance Optimizations

1. **DataLoader** - Batch queries to prevent N+1 problems
2. **Caching** - Cache frequently accessed data
3. **Pagination** - Always paginate large result sets
4. **Filtering** - Push filters to adapters
5. **Lazy Loading** - Load related data on demand

## Security

1. **Authentication**: JWT tokens in `Authorization` header
2. **Authorization**: Field-level permissions
3. **Rate Limiting**: Per-user rate limits
4. **Input Validation**: Pydantic models for all inputs
5. **CORS**: Configure allowed origins

## Monitoring

All GraphQL operations are logged:
- Query type and complexity
- Execution time
- Errors and exceptions
- User ID and correlation ID

## Next Steps

1. Install graphene dependencies
2. Connect resolvers to orchestration layers
3. Add field-level auth
4. Implement subscriptions with WebSocket
5. Add query complexity analysis
6. Setup GraphQL caching layer
