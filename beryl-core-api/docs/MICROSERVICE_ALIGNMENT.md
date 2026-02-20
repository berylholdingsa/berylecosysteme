# Microservice Alignment Plan

## Overview
This document outlines the contracts and integration points for aligning the Beryl Core API Gateway with ecosystem microservices.

## Current Architecture
- **Beryl Core API**: Central Gateway with Zero-Trust enforcement
- **Domain Adapters**: Client libraries for external service communication
- **Domains**: fintech, mobility, ESG, social

## Target Microservices Alignment

### 1. beryl_e-mobility (Mobility Domain)
**Purpose**: Electric vehicle fleet management and optimization

**Contract Requirements**:
- **Endpoint**: `/api/v1/mobility/fleet`
- **Authentication**: JWT with `mobility` scope required
- **Input**: Fleet location data, battery levels, demand predictions
- **Output**: Fleet optimization recommendations, charging schedules
- **Client Method**: `MobilityAIClient.optimize_fleet()`
- **Return Type**: `FleetOptimization` object with attributes:
  - `charging_schedule`: List[ChargingSlot]
  - `route_optimization`: Dict[str, Any]
  - `battery_predictions`: List[BatteryLevel]

**Integration Steps**:
1. Update MobilityAIClient to call beryl_e-mobility API
2. Add fleet optimization endpoint to Gateway
3. Update scope validation for `/mobility/fleet`
4. Add integration tests

### 2. berylcommunity (ESG + Social Domains)
**Purpose**: Community engagement and ESG tracking

**Contract Requirements**:
- **Endpoints**:
  - `/api/v1/esg/community` (ESG scope)
  - `/api/v1/social/community` (social scope)
- **Authentication**: JWT with appropriate domain scope
- **Input**: User engagement data, ESG metrics
- **Output**: Community insights, personalized content
- **Client Methods**:
  - `EsgCommunityClient.get_community_insights()`
  - `SocialAIClient.get_community_feed()`
- **Return Types**:
  - `CommunityInsights`: ESG impact metrics, community engagement
  - `CommunityFeed`: Social content recommendations

**Integration Steps**:
1. Update EsgCommunityClient and SocialAIClient
2. Add community endpoints to Gateway
3. Implement cross-domain data sharing (ESG ↔ Social)
4. Add comprehensive integration tests

### 3. beryl_engine (Fintech Domain)
**Purpose**: Financial transaction processing and analytics

**Contract Requirements**:
- **Endpoint**: `/api/v1/fintech/transactions`
- **Authentication**: JWT with `fintech` scope required
- **Input**: Transaction data, user financial profiles
- **Output**: Transaction analysis, risk assessments
- **Client Method**: `FintechClient.analyze_transactions()`
- **Return Type**: `TransactionAnalysis` object with attributes:
  - `risk_score`: float
  - `anomalies`: List[Anomaly]
  - `recommendations`: List[str]

**Integration Steps**:
1. Update FintechClient for transaction analysis
2. Add transaction endpoints to Gateway
3. Implement real-time risk monitoring
4. Add compliance and audit logging

## Implementation Priority
1. **High Priority**: beryl_e-mobility (mobility domain alignment)
2. **Medium Priority**: beryl_engine (fintech domain expansion)
3. **Low Priority**: berylcommunity (ESG/social integration)

## Testing Strategy
- **Unit Tests**: Client method validation
- **Integration Tests**: End-to-end Gateway ↔ Microservice
- **Contract Tests**: Real API validation in staging
- **Load Tests**: Performance validation with real services

## Security Considerations
- All microservice communications must go through Gateway
- JWT tokens propagated with appropriate scopes
- Audit logging for all cross-service calls
- Rate limiting and circuit breakers

## Next Steps
1. Implement beryl_e-mobility integration
2. Update client libraries with real API calls
3. Add comprehensive monitoring and alerting
4. Document API contracts for each microservice