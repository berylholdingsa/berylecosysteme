#!/usr/bin/env python3
"""
Validation des configurations de déploiement
Vérifie la cohérence et la validité des configurations avant déploiement
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class ValidationResult:
    level: ValidationLevel
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None

class DeploymentValidator:
    """Validateur de configuration de déploiement"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.results: List[ValidationResult] = []

    def validate_all(self) -> List[ValidationResult]:
        """Validation complète de toutes les configurations"""
        self.results = []

        # Validation des fichiers Kubernetes
        self._validate_kubernetes_manifests()

        # Validation des workflows GitHub Actions
        self._validate_github_workflows()

        # Validation du Dockerfile
        self._validate_dockerfile()

        # Validation du script de déploiement
        self._validate_deploy_script()

        # Validation des configurations Python
        self._validate_python_configs()

        # Validation de la sécurité
        self._validate_security_configs()

        return self.results

    def _validate_kubernetes_manifests(self):
        """Validation des manifests Kubernetes"""
        k8s_dir = self.workspace_root / "k8s"

        if not k8s_dir.exists():
            self._add_result(ValidationLevel.ERROR, "Dossier k8s/ manquant")
            return

        # Validation des namespaces
        namespaces_dir = k8s_dir / "namespaces"
        if namespaces_dir.exists():
            for yaml_file in namespaces_dir.glob("*.yaml"):
                self._validate_yaml_file(yaml_file, "namespace")

        # Validation des déploiements
        deployments_dir = k8s_dir / "deployments"
        if deployments_dir.exists():
            for yaml_file in deployments_dir.glob("*.yaml"):
                self._validate_deployment_file(yaml_file)

        # Validation des services
        services_dir = k8s_dir / "services"
        if services_dir.exists():
            for yaml_file in services_dir.glob("*.yaml"):
                self._validate_service_file(yaml_file)

        # Validation de l'ingress
        ingress_dir = k8s_dir / "ingress"
        if ingress_dir.exists():
            for yaml_file in ingress_dir.glob("*.yaml"):
                self._validate_ingress_file(yaml_file)

        # Validation des secrets et configmaps
        for config_type in ["secrets", "configmaps"]:
            config_dir = k8s_dir / config_type
            if config_dir.exists():
                for yaml_file in config_dir.glob("*.yaml"):
                    self._validate_config_file(yaml_file, config_type)

    def _validate_yaml_file(self, file_path: Path, resource_type: str):
        """Validation générique des fichiers YAML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            if not content:
                self._add_result(ValidationLevel.ERROR,
                               f"Fichier YAML vide: {file_path}",
                               file_path)

            # Validation de la structure de base
            if 'apiVersion' not in content:
                self._add_result(ValidationLevel.ERROR,
                               f"apiVersion manquant dans {file_path}",
                               file_path)

            if 'kind' not in content:
                self._add_result(ValidationLevel.ERROR,
                               f"kind manquant dans {file_path}",
                               file_path)

            if content.get('kind') != resource_type:
                # Vérifier si c'est juste une différence de casse
                expected = resource_type.capitalize()
                found = content.get('kind', '')
                if expected.lower() != found.lower():
                    self._add_result(ValidationLevel.WARNING,
                                   f"Type de ressource inattendu dans {file_path}: "
                                   f"attendu {expected}, trouvé {found}",
                                   file_path)

        except yaml.YAMLError as e:
            self._add_result(ValidationLevel.ERROR,
                           f"Erreur YAML dans {file_path}: {e}",
                           file_path)
        except Exception as e:
            self._add_result(ValidationLevel.ERROR,
                           f"Erreur lors de la lecture de {file_path}: {e}",
                           file_path)

    def _validate_deployment_file(self, file_path: Path):
        """Validation spécifique des déploiements"""
        self._validate_yaml_file(file_path, "deployment")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            spec = content.get('spec', {})
            template = spec.get('template', {})
            pod_spec = template.get('spec', {})

            # Vérification des bonnes pratiques
            containers = pod_spec.get('containers', [])
            if not containers:
                self._add_result(ValidationLevel.ERROR,
                               f"Aucun conteneur défini dans {file_path}",
                               file_path)
                return

            for i, container in enumerate(containers):
                # Vérification des resources
                resources = container.get('resources', {})
                if not resources:
                    self._add_result(ValidationLevel.WARNING,
                                   f"Resources non définies pour le conteneur {i} dans {file_path}",
                                   file_path)

                # Vérification des health checks
                if 'livenessProbe' not in container:
                    self._add_result(ValidationLevel.WARNING,
                                   f"Liveness probe manquant pour le conteneur {i} dans {file_path}",
                                   file_path)

                if 'readinessProbe' not in container:
                    self._add_result(ValidationLevel.WARNING,
                                   f"Readiness probe manquant pour le conteneur {i} dans {file_path}",
                                   file_path)

                # Vérification des security contexts
                security_context = container.get('securityContext', {})
                if not security_context.get('runAsNonRoot', False):
                    self._add_result(ValidationLevel.WARNING,
                                   f"Conteneur {i} peut tourner en root dans {file_path}",
                                   file_path)

        except Exception as e:
            self._add_result(ValidationLevel.ERROR,
                           f"Erreur lors de la validation du déploiement {file_path}: {e}",
                           file_path)

    def _validate_service_file(self, file_path: Path):
        """Validation des services"""
        self._validate_yaml_file(file_path, "service")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            spec = content.get('spec', {})

            # Vérification du type de service
            service_type = spec.get('type', 'ClusterIP')
            if service_type not in ['ClusterIP', 'NodePort', 'LoadBalancer']:
                self._add_result(ValidationLevel.WARNING,
                               f"Type de service non standard dans {file_path}: {service_type}",
                               file_path)

            # Vérification des ports
            ports = spec.get('ports', [])
            if not ports:
                self._add_result(ValidationLevel.ERROR,
                               f"Aucun port défini dans le service {file_path}",
                               file_path)

        except Exception as e:
            self._add_result(ValidationLevel.ERROR,
                           f"Erreur lors de la validation du service {file_path}: {e}",
                           file_path)

    def _validate_ingress_file(self, file_path: Path):
        """Validation de l'Ingress"""
        self._validate_yaml_file(file_path, "ingress")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            spec = content.get('spec', {})

            # Vérification TLS
            tls = spec.get('tls', [])
            if not tls:
                self._add_result(ValidationLevel.WARNING,
                               f"Pas de configuration TLS dans {file_path}",
                               file_path)

            # Vérification des règles
            rules = spec.get('rules', [])
            if not rules:
                self._add_result(ValidationLevel.ERROR,
                               f"Aucune règle définie dans l'Ingress {file_path}",
                               file_path)

        except Exception as e:
            self._add_result(ValidationLevel.ERROR,
                           f"Erreur lors de la validation de l'Ingress {file_path}: {e}",
                           file_path)

    def _validate_config_file(self, file_path: Path, config_type: str):
        """Validation des ConfigMaps et Secrets"""
        resource_type = "ConfigMap" if config_type == "configmaps" else "Secret"
        self._validate_yaml_file(file_path, resource_type)

    def _validate_github_workflows(self):
        """Validation des workflows GitHub Actions"""
        workflows_dir = self.workspace_root / ".github" / "workflows"

        if not workflows_dir.exists():
            self._add_result(ValidationLevel.WARNING, "Dossier .github/workflows/ manquant")
            return

        for workflow_file in workflows_dir.glob("*.yml"):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)

                # Validation de base
                if 'name' not in content:
                    self._add_result(ValidationLevel.WARNING,
                                   f"Nom manquant dans le workflow {workflow_file}",
                                   workflow_file)

                # Vérifier les déclencheurs - gérer le cas spécial GitHub Actions
                has_triggers = False
                if 'on' in content:
                    has_triggers = True
                elif True in content:  # GitHub Actions peut parser 'on' comme True
                    has_triggers = True
                elif 'trigger' in content:  # Alternative
                    has_triggers = True

                if not has_triggers:
                    self._add_result(ValidationLevel.ERROR,
                                   f"Déclencheurs manquants dans le workflow {workflow_file}",
                                   workflow_file)

                jobs = content.get('jobs', {})
                if not jobs:
                    self._add_result(ValidationLevel.ERROR,
                                   f"Aucun job défini dans le workflow {workflow_file}",
                                   workflow_file)

            except yaml.YAMLError as e:
                self._add_result(ValidationLevel.ERROR,
                               f"Erreur YAML dans le workflow {workflow_file}: {e}",
                               workflow_file)

    def _validate_dockerfile(self):
        """Validation du Dockerfile"""
        dockerfile_path = self.workspace_root / "Dockerfile"

        if not dockerfile_path.exists():
            self._add_result(ValidationLevel.ERROR, "Dockerfile manquant")
            return

        try:
            with open(dockerfile_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Vérifications de sécurité
            if "FROM" not in content.upper():
                self._add_result(ValidationLevel.ERROR,
                               "Instruction FROM manquante dans le Dockerfile",
                               dockerfile_path)

            if "USER" not in content.upper():
                self._add_result(ValidationLevel.WARNING,
                               "Pas d'instruction USER dans le Dockerfile (recommandé pour la sécurité)",
                               dockerfile_path)

            # Vérification multi-stage
            if content.upper().count("FROM") < 2:
                self._add_result(ValidationLevel.INFO,
                               "Dockerfile mono-stage détecté. Considérez un build multi-stage pour optimiser la taille de l'image",
                               dockerfile_path)

        except Exception as e:
            self._add_result(ValidationLevel.ERROR,
                           f"Erreur lors de la lecture du Dockerfile: {e}",
                           dockerfile_path)

    def _validate_deploy_script(self):
        """Validation du script de déploiement"""
        deploy_script = self.workspace_root / "deploy.sh"

        if not deploy_script.exists():
            self._add_result(ValidationLevel.ERROR, "Script deploy.sh manquant")
            return

        try:
            with open(deploy_script, 'r', encoding='utf-8') as f:
                content = f.read()

            # Vérifications de base
            if "#!/usr/bin/env bash" not in content and "#!/bin/bash" not in content:
                self._add_result(ValidationLevel.WARNING,
                               "Shebang manquant dans deploy.sh",
                               deploy_script)

            # Vérification des fonctions importantes
            required_functions = ["check_dependencies", "setup_namespace", "deploy_infrastructure"]
            for func in required_functions:
                if f"function {func}" not in content and f"{func}()" not in content:
                    self._add_result(ValidationLevel.WARNING,
                                   f"Fonction {func} manquante dans deploy.sh",
                                   deploy_script)

        except Exception as e:
            self._add_result(ValidationLevel.ERROR,
                           f"Erreur lors de la lecture de deploy.sh: {e}",
                           deploy_script)

    def _validate_python_configs(self):
        """Validation des configurations Python"""
        config_dir = self.workspace_root / "config"

        if not config_dir.exists():
            self._add_result(ValidationLevel.WARNING, "Dossier config/ manquant")
            return

        # Validation du fichier environments.py
        env_file = config_dir / "environments.py"
        if env_file.exists():
            try:
                # Import du module pour validation
                import sys
                sys.path.insert(0, str(config_dir.parent))

                # Validation basique de la syntaxe
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "ENVIRONMENTS" not in content:
                    self._add_result(ValidationLevel.WARNING,
                                   "Constante ENVIRONMENTS manquante dans environments.py",
                                   env_file)

                if "ENV_CONFIG" not in content:
                    self._add_result(ValidationLevel.WARNING,
                                   "Configuration ENV_CONFIG manquante dans environments.py",
                                   env_file)

            except Exception as e:
                self._add_result(ValidationLevel.ERROR,
                               f"Erreur dans environments.py: {e}",
                               env_file)

    def _validate_security_configs(self):
        """Validation des configurations de sécurité"""
        # Vérification des secrets non committés
        secrets_file = self.workspace_root / "k8s" / "secrets" / "beryl-secrets.yaml"
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)

                # Vérification que les secrets ne sont pas en clair
                if content.get('data'):
                    for key, value in content['data'].items():
                        if not value or len(value) < 10:  # Valeur très courte = suspect
                            self._add_result(ValidationLevel.WARNING,
                                           f"Secret potentiellement faible pour {key} dans {secrets_file}",
                                           secrets_file)

            except Exception as e:
                self._add_result(ValidationLevel.ERROR,
                               f"Erreur lors de la validation des secrets: {e}",
                               secrets_file)

        # Vérification des network policies
        network_policy_file = self.workspace_root / "k8s" / "network-policies.yaml"
        if not network_policy_file.exists():
            self._add_result(ValidationLevel.WARNING,
                           "Fichier network-policies.yaml manquant")

    def _add_result(self, level: ValidationLevel, message: str,
                   file_path: Optional[Path] = None, line_number: Optional[int] = None):
        """Ajout d'un résultat de validation"""
        self.results.append(ValidationResult(
            level=level,
            message=message,
            file_path=str(file_path) if file_path else None,
            line_number=line_number
        ))

    def print_results(self):
        """Affichage des résultats de validation"""
        if not self.results:
            print("✅ Aucune erreur de validation trouvée!")
            return

        errors = [r for r in self.results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in self.results if r.level == ValidationLevel.WARNING]
        infos = [r for r in self.results if r.level == ValidationLevel.INFO]

        if errors:
            print(f"❌ {len(errors)} erreurs trouvées:")
            for result in errors:
                file_info = f" ({result.file_path})" if result.file_path else ""
                print(f"  - {result.message}{file_info}")

        if warnings:
            print(f"⚠️  {len(warnings)} avertissements:")
            for result in warnings:
                file_info = f" ({result.file_path})" if result.file_path else ""
                print(f"  - {result.message}{file_info}")

        if infos:
            print(f"ℹ️  {len(infos)} informations:")
            for result in infos:
                file_info = f" ({result.file_path})" if result.file_path else ""
                print(f"  - {result.message}{file_info}")

def main():
    """Point d'entrée principal"""
    # Utiliser le répertoire courant au lieu de __file__.parent.parent
    workspace_root = Path.cwd()

    validator = DeploymentValidator(workspace_root)
    results = validator.validate_all()

    print("🔍 Validation de la configuration de déploiement")
    print("=" * 50)

    validator.print_results()

    # Code de sortie basé sur les erreurs
    errors = [r for r in results if r.level == ValidationLevel.ERROR]
    if errors:
        print(f"\n❌ Validation échouée avec {len(errors)} erreurs")
        sys.exit(1)
    else:
        print("\n✅ Validation réussie!")
        sys.exit(0)

if __name__ == "__main__":
    main()