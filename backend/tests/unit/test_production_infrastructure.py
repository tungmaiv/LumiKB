"""Unit tests for production infrastructure configuration.

Story 7.4: Production Deployment Configuration
AC-7.4.1: docker-compose.prod.yml with production settings
AC-7.4.2: Kubernetes manifests
AC-7.4.3: Secrets from environment variables

Tests validate:
- docker-compose.prod.yml structure and settings
- Kubernetes manifest structure
- Environment template completeness
"""

from pathlib import Path

import pytest
import yaml

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


# Paths relative to project root
# __file__ is backend/tests/unit/test_production_infrastructure.py
# So parent.parent.parent gives us backend/, and one more parent gives project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DOCKER_COMPOSE_PROD = (
    PROJECT_ROOT / "infrastructure" / "docker" / "docker-compose.prod.yml"
)
K8S_DIR = PROJECT_ROOT / "infrastructure" / "k8s"
ENV_TEMPLATE = PROJECT_ROOT / "infrastructure" / ".env.prod.template"


class TestDockerComposeProd:
    """Tests for docker-compose.prod.yml configuration."""

    @pytest.fixture
    def compose_config(self) -> dict:
        """Load docker-compose.prod.yml as dictionary."""
        if not DOCKER_COMPOSE_PROD.exists():
            pytest.skip("docker-compose.prod.yml not found")

        with open(DOCKER_COMPOSE_PROD) as f:
            return yaml.safe_load(f)

    def test_file_exists(self) -> None:
        """Test that docker-compose.prod.yml exists."""
        assert DOCKER_COMPOSE_PROD.exists(), f"File not found: {DOCKER_COMPOSE_PROD}"

    def test_all_services_have_restart_policy(self, compose_config: dict) -> None:
        """Test that all services have restart policy set to 'always' or 'unless-stopped'."""
        services = compose_config.get("services", {})
        valid_policies = ["always", "unless-stopped"]

        for service_name, service_config in services.items():
            restart = service_config.get("restart")
            assert (
                restart in valid_policies
            ), f"Service '{service_name}' missing or invalid restart policy: {restart}"

    def test_all_services_have_healthcheck(self, compose_config: dict) -> None:
        """Test that all services have health checks configured."""
        services = compose_config.get("services", {})

        for service_name, service_config in services.items():
            healthcheck = service_config.get("healthcheck")
            assert (
                healthcheck is not None
            ), f"Service '{service_name}' missing healthcheck configuration"
            assert (
                "test" in healthcheck
            ), f"Service '{service_name}' healthcheck missing 'test' command"

    def test_services_have_resource_limits(self, compose_config: dict) -> None:
        """Test that services have resource limits defined."""
        services = compose_config.get("services", {})

        for service_name, service_config in services.items():
            deploy = service_config.get("deploy", {})
            resources = deploy.get("resources", {})
            limits = resources.get("limits", {})

            # Check for CPU and memory limits
            assert (
                "cpus" in limits or "memory" in limits
            ), f"Service '{service_name}' missing resource limits"

    def test_services_use_json_file_logging(self, compose_config: dict) -> None:
        """Test that services use json-file logging driver with rotation."""
        services = compose_config.get("services", {})

        for service_name, service_config in services.items():
            logging_config = service_config.get("logging", {})
            driver = logging_config.get("driver")

            assert (
                driver == "json-file"
            ), f"Service '{service_name}' should use json-file logging driver, got: {driver}"

            options = logging_config.get("options", {})
            assert (
                "max-size" in options
            ), f"Service '{service_name}' logging missing max-size option"
            assert (
                "max-file" in options
            ), f"Service '{service_name}' logging missing max-file option"

    def test_required_services_present(self, compose_config: dict) -> None:
        """Test that all required services are defined."""
        services = compose_config.get("services", {})
        required_services = [
            "postgres",
            "redis",
            "minio",
            "qdrant",
            "api",
            "celery-worker",
        ]

        for required in required_services:
            assert required in services, f"Required service '{required}' not found"

    def test_api_service_uses_health_endpoint(self, compose_config: dict) -> None:
        """Test that API service healthcheck uses /health endpoint."""
        services = compose_config.get("services", {})
        api_config = services.get("api", {})
        healthcheck = api_config.get("healthcheck", {})
        test_cmd = healthcheck.get("test", [])

        # Convert list to string for easier checking
        test_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert (
            "/health" in test_str
        ), f"API healthcheck should use /health endpoint, got: {test_str}"

    def test_no_hardcoded_passwords(self, compose_config: dict) -> None:
        """Test that no hardcoded passwords exist in compose file."""
        compose_str = yaml.dump(compose_config)

        # Check for common hardcoded password patterns
        forbidden_patterns = [
            "password123",
            "admin123",
            "secret123",
            "lumikb_dev_password",  # Development default
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in compose_str.lower()
            ), f"Hardcoded password pattern found: {pattern}"

    def test_secrets_use_env_vars(self, compose_config: dict) -> None:
        """Test that secrets use environment variable interpolation."""
        compose_str = yaml.dump(compose_config)

        # Should use ${VAR} syntax for secrets
        assert (
            "${POSTGRES_PASSWORD}" in compose_str or "${POSTGRES_USER}" in compose_str
        )
        assert (
            "${MINIO_ROOT_PASSWORD}" in compose_str
            or "${MINIO_ROOT_USER}" in compose_str
        )
        assert (
            "${SECRET_KEY}" in compose_str
            or "${JWT_SECRET}" in compose_str
            or "${LITELLM_MASTER_KEY}" in compose_str
        )

    def test_network_configured(self, compose_config: dict) -> None:
        """Test that network configuration exists."""
        networks = compose_config.get("networks", {})
        assert networks, "No networks defined in docker-compose.prod.yml"

    def test_volumes_configured(self, compose_config: dict) -> None:
        """Test that named volumes are configured for persistent data."""
        volumes = compose_config.get("volumes", {})

        # Required volumes for data persistence
        expected_volumes = ["postgres_data", "redis_data", "qdrant_data"]

        for vol in expected_volumes:
            assert vol in volumes, f"Required volume '{vol}' not found"


class TestKubernetesManifests:
    """Tests for Kubernetes manifest structure."""

    def test_k8s_directory_exists(self) -> None:
        """Test that k8s directory exists."""
        assert K8S_DIR.exists(), f"K8s directory not found: {K8S_DIR}"

    def test_required_manifests_exist(self) -> None:
        """Test that required K8s manifests exist."""
        if not K8S_DIR.exists():
            pytest.skip("K8s directory not found")

        required_files = [
            "api-deployment.yaml",
            "worker-deployment.yaml",
            "services.yaml",
            "configmaps-secrets.yaml",
        ]

        for filename in required_files:
            filepath = K8S_DIR / filename
            assert filepath.exists(), f"Required K8s manifest not found: {filename}"

    def test_api_deployment_has_probes(self) -> None:
        """Test that API deployment has liveness and readiness probes."""
        api_deployment = K8S_DIR / "api-deployment.yaml"
        if not api_deployment.exists():
            pytest.skip("api-deployment.yaml not found")

        with open(api_deployment) as f:
            # Parse multi-document YAML and find the Deployment
            manifests = list(yaml.safe_load_all(f))

        # Find the Deployment manifest
        manifest = None
        for doc in manifests:
            if doc and doc.get("kind") == "Deployment":
                manifest = doc
                break

        assert manifest is not None, "No Deployment found in api-deployment.yaml"

        # Navigate to container spec
        spec = manifest.get("spec", {})
        template = spec.get("template", {})
        template_spec = template.get("spec", {})
        containers = template_spec.get("containers", [])

        assert containers, "No containers defined in API deployment"

        api_container = containers[0]

        # Check for probes
        assert "livenessProbe" in api_container, "API deployment missing livenessProbe"
        assert (
            "readinessProbe" in api_container
        ), "API deployment missing readinessProbe"

        # Verify probes use correct endpoints
        liveness = api_container.get("livenessProbe", {})
        readiness = api_container.get("readinessProbe", {})

        liveness_path = liveness.get("httpGet", {}).get("path", "")
        readiness_path = readiness.get("httpGet", {}).get("path", "")

        assert (
            "/health" in liveness_path or "health" in liveness_path.lower()
        ), f"Liveness probe should use /health endpoint, got: {liveness_path}"
        assert (
            "/ready" in readiness_path or "ready" in readiness_path.lower()
        ), f"Readiness probe should use /ready endpoint, got: {readiness_path}"

    def test_services_yaml_has_required_services(self) -> None:
        """Test that services.yaml defines required Kubernetes services."""
        services_file = K8S_DIR / "services.yaml"
        if not services_file.exists():
            pytest.skip("services.yaml not found")

        with open(services_file) as f:
            # Parse multi-document YAML
            manifests = list(yaml.safe_load_all(f))

        service_names = []
        for manifest in manifests:
            if manifest and manifest.get("kind") == "Service":
                service_names.append(manifest.get("metadata", {}).get("name", ""))

        # At least API service should be defined
        assert any(
            "api" in name.lower() for name in service_names
        ), f"API service not found. Services: {service_names}"


class TestEnvTemplate:
    """Tests for environment template file."""

    def test_env_template_exists(self) -> None:
        """Test that .env.prod.template exists."""
        assert ENV_TEMPLATE.exists(), f"File not found: {ENV_TEMPLATE}"

    def test_required_variables_documented(self) -> None:
        """Test that all required variables are documented in template."""
        if not ENV_TEMPLATE.exists():
            pytest.skip(".env.prod.template not found")

        with open(ENV_TEMPLATE) as f:
            content = f.read()

        required_vars = [
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "MINIO_ROOT_USER",
            "MINIO_ROOT_PASSWORD",
            "SECRET_KEY",
            "JWT_SECRET",
            "LITELLM_MASTER_KEY",
        ]

        for var in required_vars:
            assert (
                var in content
            ), f"Required variable '{var}' not documented in template"

    def test_template_has_secure_generation_instructions(self) -> None:
        """Test that template includes instructions for secure secret generation."""
        if not ENV_TEMPLATE.exists():
            pytest.skip(".env.prod.template not found")

        with open(ENV_TEMPLATE) as f:
            content = f.read()

        # Should include openssl or similar secure generation instructions
        assert (
            "openssl" in content.lower() or "generate" in content.lower()
        ), "Template should include instructions for generating secure secrets"

    def test_template_warns_about_version_control(self) -> None:
        """Test that template warns against committing secrets to version control."""
        if not ENV_TEMPLATE.exists():
            pytest.skip(".env.prod.template not found")

        with open(ENV_TEMPLATE) as f:
            content = f.read().lower()

        # Should warn about not committing .env.prod
        assert (
            "commit" in content or "version control" in content or "git" in content
        ), "Template should warn about not committing secrets"
