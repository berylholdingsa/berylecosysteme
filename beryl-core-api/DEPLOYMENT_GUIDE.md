# 🚀 Guide de Déploiement Rapide - Beryl Core API

## Prérequis Système

### Cluster Kubernetes
```bash
# Vérifier la version
kubectl version --short

# Vérifier les nodes
kubectl get nodes

# Installer les prérequis
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
```

### Outils Locaux
```bash
# Installer les outils
brew install kubectl helm kustomize  # macOS
# ou
apt-get install kubectl helm  # Ubuntu

# Vérifier
kubectl version --client
helm version
```

## 🏗️ Déploiement Complet

### 1. Configuration
```bash
# Cloner le repository
git clone https://github.com/generalhaypi/beryl_ecosysteme.git
cd beryl_ecosysteme/beryl-core-api

# Variables d'environnement
export ENVIRONMENT=staging
export REGISTRY=ghcr.io/generalhaypi/beryl_ecosysteme/beryl-core-api
export KUBE_CONTEXT=your-cluster-context

# Validation des configurations
python3 validate_config.py
```

### 2. Build & Push Image
```bash
# Build multi-stage
docker build -t $REGISTRY:latest .

# Push vers registry
docker push $REGISTRY:latest

# Ou via GitHub Actions (recommandé)
git tag v1.0.0
git push origin v1.0.0
```

### 3. Déploiement Automatique
```bash
# Rendre exécutable
chmod +x deploy.sh

# Déploiement complet
./deploy.sh

# Suivre le déploiement
kubectl get pods -n beryl-staging -w
```

### 4. Vérifications Post-Déploiement
```bash
# Status des déploiements
kubectl get deployments -n beryl-staging

# Health checks
curl https://staging-api.beryl-ecosystem.com/health
curl https://staging-graphql.beryl-ecosystem.com/health

# Métriques
curl https://staging-api.beryl-ecosystem.com/metrics

# Logs
kubectl logs -f deployment/beryl-core-api -n beryl-staging
```

## 🔧 Commandes Utiles

### Monitoring
```bash
# Dashboard Kubernetes
kubectl proxy
# Accéder à http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

# Métriques des pods
kubectl top pods -n beryl-staging

# Événements récents
kubectl get events -n beryl-staging --sort-by=.metadata.creationTimestamp
```

### Debugging
```bash
# Logs détaillés
kubectl logs -f deployment/beryl-core-api -n beryl-staging --previous

# Debug d'un pod
kubectl exec -it deployment/beryl-core-api -n beryl-staging -- /bin/bash

# Port forwarding pour tests locaux
kubectl port-forward deployment/beryl-core-api 8000:8000 -n beryl-staging
```

### Maintenance
```bash
# Rollback
kubectl rollout undo deployment/beryl-core-api -n beryl-staging

# Scale manuel
kubectl scale deployment beryl-core-api --replicas=5 -n beryl-staging

# Restart forcé
kubectl rollout restart deployment/beryl-core-api -n beryl-staging
```

## 🌍 Déploiement Multi-Environnements

### Development
```bash
export ENVIRONMENT=development
export REGISTRY=ghcr.io/generalhaypi/beryl_ecosysteme/beryl-core-api
./deploy.sh
# Accès: http://dev-api.beryl-ecosystem.com
```

### Staging
```bash
export ENVIRONMENT=staging
export REGISTRY=ghcr.io/generalhaypi/beryl_ecosysteme/beryl-core-api
./deploy.sh
# Accès: https://staging-api.beryl-ecosystem.com
```

### Production
```bash
export ENVIRONMENT=production
export REGISTRY=ghcr.io/generalhaypi/beryl_ecosysteme/beryl-core-api
./deploy.sh
# Accès: https://api.beryl-ecosystem.com
```

## 🔒 Sécurité & Conformité

### Secrets Management
```bash
# Créer les secrets avant déploiement
kubectl create secret generic beryl-secrets \
  --from-literal=jwt-secret-key="$(openssl rand -hex 32)" \
  --from-literal=database-password="secure-password" \
  --namespace=beryl-staging
```

### TLS Certificates
```bash
# Vérifier les certificats
kubectl get certificates -n beryl-staging

# Debug cert-manager
kubectl describe certificate beryl-tls -n beryl-staging
```

### Network Policies
```bash
# Tester les politiques réseau
kubectl get networkpolicies -n beryl-staging

# Debug connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
# Puis: wget http://beryl-core-api.beryl-staging.svc.cluster.local:8000/health
```

## 📊 Observabilité

### Métriques Prometheus
```bash
# Accéder à Prometheus
kubectl port-forward svc/prometheus-service 9090:9090 -n beryl-monitoring

# Queries importantes
# - Taux d'erreur: rate(beryl_api_requests_total{status=~"5.."}[5m])
# - Latence: histogram_quantile(0.95, rate(beryl_api_request_duration_seconds_bucket[5m]))
# - Throughput: rate(beryl_api_requests_total[5m])
```

### Logs ELK
```bash
# Accéder à Kibana
kubectl port-forward svc/kibana 5601:5601 -n beryl-monitoring

# Queries importantes
# - Erreurs: level:ERROR
# - Performance: response_time:>1000
# - Audit: audit:true
```

### Tracing Jaeger
```bash
# Accéder à Jaeger
kubectl port-forward svc/jaeger-query 16686:16686 -n beryl-monitoring

# Chercher par tags
# - service:beryl-core-api
# - operation:graphql_query
# - error:true
```

## 🚨 Troubleshooting

### Pod CrashLoopBackOff
```bash
# Diagnostiquer
kubectl describe pod <pod-name> -n beryl-staging
kubectl logs <pod-name> -n beryl-staging --previous

# Causes communes:
# - Variables d'environnement manquantes
# - Secrets non créés
# - Health checks échouées
# - Resources insuffisantes
```

### Service Unavailable
```bash
# Vérifier les endpoints
kubectl get endpoints -n beryl-staging

# Vérifier les services
kubectl describe service beryl-core-api -n beryl-staging

# Causes communes:
# - Pods non prêts
# - Labels incorrects
# - Network policies bloquantes
```

### Ingress Not Working
```bash
# Vérifier l'ingress
kubectl describe ingress beryl-ingress -n beryl-staging

# Vérifier le contrôleur ingress
kubectl get pods -n ingress-nginx

# Causes communes:
# - Host non configuré
# - TLS secret manquant
# - Annotations incorrectes
```

### High Resource Usage
```bash
# Monitorer les resources
kubectl top pods -n beryl-staging

# Vérifier les limites
kubectl describe deployment beryl-core-api -n beryl-staging

# Solutions:
# - Ajuster les requests/limits
# - Scale horizontal
# - Optimiser l'application
```

## 📞 Support & Escalade

### Niveaux de Support
1. **Documentation** : Vérifier ce guide et INFRASTRUCTURE_README.md
2. **Logs/Métriques** : Utiliser les dashboards de monitoring
3. **Equipe DevOps** : Escalader via Slack/Teams
4. **Vendor Support** : Kubernetes, cert-manager, etc.

### Runbooks d'Urgence
- [Incident Response](./docs/incident-response.md)
- [Disaster Recovery](./docs/disaster-recovery.md)
- [Security Incident](./docs/security-incident.md)

---

## ✅ Checklist Déploiement

### Pré-déploiement
- [ ] Cluster Kubernetes opérationnel
- [ ] NGINX Ingress installé
- [ ] cert-manager configuré
- [ ] Secrets créés
- [ ] Images buildées et poussées
- [ ] Configurations validées (`validate_config.py`)

### Pendant le déploiement
- [ ] `deploy.sh` exécuté avec succès
- [ ] Pods en cours de création
- [ ] Services exposés
- [ ] Ingress configuré

### Post-déploiement
- [ ] Health checks OK
- [ ] Métriques collectées
- [ ] Logs visibles
- [ ] Tests d'intégration passés
- [ ] Monitoring alertes configurées

### Production Go-Live
- [ ] Tests de charge exécutés
- [ ] Performance baselines respectées
- [ ] Equipe notifiée
- [ ] Runbooks disponibles
- [ ] Support 24/7 assuré

**🎯 Infrastructure prête pour la production !**