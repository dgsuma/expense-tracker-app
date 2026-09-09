# CI/CD strategy

The pipeline is defined in [Jenkinsfile](../Jenkinsfile) (declarative). It is designed for the target flow:

```
Developer → Git → GitHub → Jenkins CI → GHCR → GitOps repo (dgs-private-cloud) → FluxCD → Kubernetes
```

The pipeline runs on the `jenkins-agent-01` agent and uses `pollSCM` (every ~2 minutes) because Jenkins is privately accessible and GitHub cannot reach it with a webhook. Production deployment happens only from `main`.

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
| **Docker: push** | Push immutable images to GHCR |
| **GitOps: update manifests** | (main only) Update image tags in the GitOps repo → FluxCD reconciles |

## Configuration (no hard-coded values)

All credentials come from **Jenkins credentials**, never committed:

| Value | Source |
|---|---|
| `oci-registry-credentials` | Jenkins credential (GHCR username/PAT) |
| `gitops-repo-credentials` | Jenkins credential (GitHub username/PAT for the GitOps repo) |

The registry (`ghcr.io/dgsuma`) and GitOps repo (`dgs-private-cloud`) are fixed for this deployment and defined in the Jenkinsfile.

## Image tagging

Images are tagged with `<short-commit-sha>-<build-number>` (e.g. `a1b2c3d4-42`). The tag is computed **after checkout** (`git rev-parse --short=8 HEAD`) because `GIT_COMMIT` is not populated before checkout. `latest` is **not** used for deployment. This gives:
- **Traceability** — every image maps to an exact commit and build.
- **Rollback** — redeploy a previous tag.
- **GitOps** — the GitOps repo's `newTag` is updated to the exact immutable tag.

## GitOps handoff

On `main`, the pipeline clones the GitOps repo (`dgs-private-cloud`), updates ONLY the image tags in `clusters/beelink-talos/expense-tracker/kustomization.yaml`, commits (`deploy(expense-tracker): <tag>`), and pushes. **FluxCD** watches that repo and reconciles the cluster — Jenkins never runs `kubectl` against the cluster.

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
