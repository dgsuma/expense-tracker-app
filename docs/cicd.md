# CI/CD strategy

The pipeline is defined in [Jenkinsfile](../Jenkinsfile) (declarative). It is designed for the target flow:

```
Developer → Git → GitHub → Jenkins CI → OCI registry → GitOps repo → FluxCD → Kubernetes
```

## Pipeline stages

| Stage | What it does |
|---|---|
| **Checkout** | Clone the repo |
| **Backend: dependencies** | Create venv, install `requirements-dev.txt` |
| **Backend: lint** | `ruff check` + `ruff format --check` |
| **Backend: unit tests + coverage** | `pytest` (no DB) with coverage XML |
| **Backend: integration tests** | Ephemeral Postgres container → `alembic upgrade head` → `pytest tests/test_auth.py` |
| **Security: dependency scan** | `pip-audit` for known vulnerabilities |
| **Frontend: analyze + test** | `flutter pub get`, `flutter analyze`, `flutter test` |
| **Docker: build** | Build API + web images, tagged with commit SHA + build number |
| **Docker: scan** | Trivy image scan (HIGH/CRITICAL) |
| **Docker: push** | Push to the OCI registry |
| **GitOps: update manifests** | (main only) Update image tags in the GitOps repo → FluxCD reconciles |

## Configuration (no hard-coded values)

All infrastructure-specific values come from **Jenkins credentials** and **environment variables**, never committed:

| Value | Source |
|---|---|
| `oci-registry-credentials` | Jenkins credential (username/password) |
| `gitops-repo-credentials` | Jenkins credential (username/token) |
| `OCI_REGISTRY_URL` | Jenkins global env var |
| `GITOPS_REPO_URL` | Jenkins global env var |
| `WEB_API_BASE_URL` | Jenkins global env var (the public API URL for the web build) |

## Image tagging

Images are tagged with `<short-commit-sha>-<build-number>` (e.g. `a1b2c3d4-42`) plus `latest`. This gives:
- **Traceability** — every image maps to an exact commit and build.
- **Rollback** — redeploy a previous tag.
- **GitOps** — the prod overlay's `newTag` is updated to the exact tag.

## GitOps handoff

On `main`, the pipeline clones the GitOps repo, updates the image tags in `infrastructure/kubernetes/overlays/prod/kustomization.yaml`, commits, and pushes. **FluxCD** watches that repo and reconciles the cluster — no direct cluster access from CI.

## Quality gates

- Lint must pass (ruff, flutter analyze).
- Unit tests must pass; coverage reported (gate ≥80% combined with integration).
- Integration tests run against a real ephemeral Postgres.
- Dependency and image scans report findings (set `--exit-code 1` to fail on HIGH/CRITICAL once the baseline is clean).

## Running a Jenkins agent

The pipeline expects an agent with: Docker, Python 3.12, Flutter SDK, Trivy, and kubectl. A Docker-in-Docker or host-Docker-socket setup is typical. These are agent prerequisites, not pipeline config.

## Future enhancements

- Parallelize backend/frontend stages.
- Cache pip/pub dependencies between builds.
- Sign images (cosign) and verify in the cluster.
- Add a staging environment gate before prod.
