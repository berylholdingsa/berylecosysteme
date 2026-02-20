# Configuration des Environnements de Déploiement
# Ce fichier définit les paramètres pour chaque environnement

# Environnements supportés
ENVIRONMENTS = ["development", "staging", "production"]

# Configuration par environnement
ENV_CONFIG = {
    "development": {
        "namespace": "beryl-dev",
        "replicas": {
            "beryl-core-api": 1,
            "graphql-gateway": 1,
            "event-bus": 1
        },
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "200m", "memory": "256Mi"}
        },
        "ingress": {
            "host": "dev-api.beryl-ecosystem.com",
            "tls": False
        },
        "monitoring": {
            "enabled": True,
            "retention": "7d"
        },
        "security": {
            "network_policies": True,
            "rbac": True
        }
    },
    "staging": {
        "namespace": "beryl-staging",
        "replicas": {
            "beryl-core-api": 2,
            "graphql-gateway": 2,
            "event-bus": 2
        },
        "resources": {
            "requests": {"cpu": "250m", "memory": "256Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"}
        },
        "ingress": {
            "host": "staging-api.beryl-ecosystem.com",
            "tls": True,
            "cert_issuer": "letsencrypt-staging"
        },
        "monitoring": {
            "enabled": True,
            "retention": "30d"
        },
        "security": {
            "network_policies": True,
            "rbac": True
        }
    },
    "production": {
        "namespace": "beryl-prod",
        "replicas": {
            "beryl-core-api": 3,
            "graphql-gateway": 3,
            "event-bus": 3
        },
        "resources": {
            "requests": {"cpu": "500m", "memory": "512Mi"},
            "limits": {"cpu": "1000m", "memory": "1Gi"}
        },
        "ingress": {
            "host": "api.beryl-ecosystem.com",
            "tls": True,
            "cert_issuer": "letsencrypt-prod"
        },
        "monitoring": {
            "enabled": True,
            "retention": "90d"
        },
        "security": {
            "network_policies": True,
            "rbac": True,
            "audit": True
        }
    }
}

# Configuration commune à tous les environnements
COMMON_CONFIG = {
    "image": {
        "registry": "ghcr.io",
        "repository": "generalhaypi/beryl_ecosysteme/beryl-core-api",
        "pull_policy": "Always"
    },
    "ports": {
        "http": 8000,
        "metrics": 9090,
        "health": 8080
    },
    "health_checks": {
        "liveness": {
            "path": "/health/live",
            "port": 8080,
            "initial_delay": 30,
            "period": 10
        },
        "readiness": {
            "path": "/health/ready",
            "port": 8080,
            "initial_delay": 5,
            "period": 5
        }
    },
    "hpa": {
        "min_replicas": 1,
        "max_replicas": 10,
        "cpu_target": 70,
        "memory_target": 80
    },
    "pdb": {
        "min_available": 1
    },
    "affinity": {
        "pod_anti_affinity": {
            "required_during_scheduling_ignored_during_execution": [
                {
                    "label_selector": {
                        "match_expressions": [
                            {
                                "key": "app",
                                "operator": "In",
                                "values": ["beryl-core-api", "graphql-gateway"]
                            }
                        ]
                    },
                    "topology_key": "kubernetes.io/hostname"
                }
            ]
        }
    }
}

# Configuration des secrets par environnement
SECRETS_CONFIG = {
    "development": {
        "jwt_secret_key": "dev-jwt-secret-key-32-chars-minimum",
        "database_url": "postgresql://beryl_dev:dev_password@postgres-dev:5432/beryl_dev",
        "redis_url": "redis://redis-dev:6379/0",
        "kafka_bootstrap_servers": "kafka-dev:9092",
        "external_apis": {
            "fintech_mamba": "http://fintech-dev:8080",
            "mobility_ai": "http://mobility-dev:8080",
            "esg_community": "http://esg-dev:8080",
            "social_ai": "http://social-dev:8080"
        }
    },
    "staging": {
        "jwt_secret_key": "staging-jwt-secret-key-32-chars-minimum",
        "database_url": "postgresql://beryl_staging:staging_password@postgres-staging:5432/beryl_staging",
        "redis_url": "redis://redis-staging:6379/0",
        "kafka_bootstrap_servers": "kafka-staging:9092",
        "external_apis": {
            "fintech_mamba": "http://fintech-staging:8080",
            "mobility_ai": "http://mobility-staging:8080",
            "esg_community": "http://esg-staging:8080",
            "social_ai": "http://social-staging:8080"
        }
    },
    "production": {
        "jwt_secret_key": "prod-jwt-secret-key-32-chars-minimum-secure-random",
        "database_url": "postgresql://beryl_prod:prod_password@postgres-prod:5432/beryl_prod",
        "redis_url": "redis://redis-prod:6379/0",
        "kafka_bootstrap_servers": "kafka-prod:9092",
        "external_apis": {
            "fintech_mamba": "http://fintech-prod:8080",
            "mobility_ai": "http://mobility-prod:8080",
            "esg_community": "http://esg-prod:8080",
            "social_ai": "http://social-prod:8080"
        }
    }
}

# Configuration des alertes par environnement
ALERTS_CONFIG = {
    "development": {
        "enabled": False,
        "channels": []
    },
    "staging": {
        "enabled": True,
        "channels": ["slack-staging", "email-devops"],
        "rules": {
            "high_error_rate": {"threshold": 10, "duration": "5m"},
            "high_latency": {"threshold": 5000, "duration": "5m"},
            "pod_crash": {"threshold": 3, "duration": "10m"}
        }
    },
    "production": {
        "enabled": True,
        "channels": ["slack-prod", "email-devops", "pagerduty"],
        "rules": {
            "high_error_rate": {"threshold": 5, "duration": "5m"},
            "high_latency": {"threshold": 2000, "duration": "5m"},
            "pod_crash": {"threshold": 1, "duration": "5m"},
            "resource_usage": {"cpu_threshold": 90, "memory_threshold": 90}
        }
    }
}

# Configuration des backups par environnement
BACKUP_CONFIG = {
    "development": {
        "enabled": False,
        "schedule": "",
        "retention": "0d"
    },
    "staging": {
        "enabled": True,
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "retention": "7d"
    },
    "production": {
        "enabled": True,
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "retention": "30d",
        "offsite": True
    }
}

# Configuration des certificats TLS
TLS_CONFIG = {
    "development": {
        "enabled": False
    },
    "staging": {
        "enabled": True,
        "issuer": {
            "name": "letsencrypt-staging",
            "server": "https://acme-staging-v02.api.letsencrypt.org/directory",
            "email": "devops@beryl-ecosystem.com"
        }
    },
    "production": {
        "enabled": True,
        "issuer": {
            "name": "letsencrypt-prod",
            "server": "https://acme-v02.api.letsencrypt.org/directory",
            "email": "devops@beryl-ecosystem.com"
        }
    }
}