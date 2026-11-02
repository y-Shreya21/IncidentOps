# Layer 7: Cloud Infrastructure & Deployment Architecture

## 1. Cloud Target: AWS Elastic Container Service (ECS)

In production enterprise environments, **AI IncidentOps** is deployed as containerized services orchestrated via AWS ECS Fargate, providing high availability, auto-scaling, and isolation without EC2 server maintenance overhead.

```mermaid
graph TD
    User([SRE / Incident Operator]) --> CloudFront[AWS CloudFront CDN]
    CloudFront --> ALB[Application Load Balancer]
    
    subgraph VPC ["AWS Virtual Private Cloud (Multi-AZ)"]
        subgraph PublicSubnets ["Public Subnets"]
            ALB
        end
        
        subgraph PrivateSubnets ["Private App Subnets"]
            ALB -->|Port 3000| ECS_Frontend["ECS Service: React Operations Dashboard"]
            ALB -->|Port 8000| ECS_Backend["ECS Service: FastAPI Multi-Agent Engine"]
        end
        
        subgraph DataSubnets ["Isolated Data Subnets"]
            ECS_Backend --> RDS[("Amazon RDS PostgreSQL (Multi-AZ)")]
            ECS_Backend --> ElastiCache[("Amazon ElastiCache Redis Cluster")]
        end
    end
    
    ECS_Backend --> CloudWatch["Amazon CloudWatch Logs & Metrics"]
    ECS_Backend --> SecretsManager["AWS Secrets Manager (API Keys & Credentials)"]
```

## 2. Infrastructure Services Specification
- **AWS ECS (Fargate)**: Serverless task execution for the FastAPI backend and React frontend.
- **Amazon RDS for PostgreSQL (Multi-AZ)**: Managed relational persistence with automated daily snapshots and point-in-time recovery.
- **Amazon ElastiCache for Redis**: In-memory caching for topology registries and runbook catalogs.
- **AWS Secrets Manager**: Secure management of model credentials (`OPENAI_API_KEY`) and JWT secrets (`JWT_SECRET`).
- **Amazon CloudWatch**: Centralized log streaming and alerting alarms for API latencies $> 2000\text{ms}$.

## 3. Cost Considerations & Auto-Scaling Policy
- Minimum 2 tasks across distinct Availability Zones for high availability.
- Scale-out trigger: CPU utilization $> 75\%$ or request count per target $> 1000\text{ req/min}$.
