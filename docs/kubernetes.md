# Kubernetes deployment

Kubernetes manifests use **Kustomize** with a base + overlays structure, ready for FluxCD GitOps.

## Layout

```
infrastructure/kubernetes/
├── base/                    # Shared manifests
│   ├── namespace.yaml
│   ├── configmap.yaml       # Non-secret config
│   ├── secret.example.yaml  # Documents required secret keys (no real values)
│   ├── db.yaml              # PostgreSQL StatefulSet + headless Service + PVC
│   ├── api.yaml             # API Deployment + Service
│   ├── web.yaml             # Web Deployment + Service
│   ├── ingress.yaml         # Ingress with TLS (cert-manager)
│   └── kustomization.yaml
├── overlays/
│   ├── dev/                 # 1 replica, :dev tags, expenses.dev.local
│   │   └── kustomization.yaml
│   └── prod/                # 3 API replicas, pinned tags, real hostname + CORS
│       └── kustomization.yaml
└── flux/
    └── kustomization.yaml   # FluxCD entry point → overlays/prod
```

## Design decisions

- **StatefulSet for Postgres** — stable network identity and persistent storage via a `volumeClaimTemplate` (5Gi). A headless Service provides the stable DNS name `db`.
- **Deployments for api/web** — stateless, horizontally scalable. The API is stateless (JWT auth, no server-side sessions), so it scales freely.
- **ConfigMap + Secret split** — non-secret config in a ConfigMap; secrets (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`) referenced from a Secret. **No real secret values are committed** — see Secrets below.
- **Probes** — liveness (`/health`) and readiness (`/ready`) on the API; the readiness probe checks DB connectivity so traffic only routes to pods that can serve.
- **Resource requests/limits** — set on all containers for scheduling and QoS.
- **Ingress** — routes `/api` to the API service and `/` to the web service, TLS via cert-manager.

## Secrets strategy

Secrets are **never committed to Git**. The base includes `secret.example.yaml` documenting the required keys. In the target cluster, provide them via one of:

1. **External Secrets Operator** (recommended) — sync from a secrets store (Vault, AWS Secrets Manager, etc.).
2. **Sealed Secrets** — commit encrypted secrets safe for Git.
3. **Manual** — `kubectl create secret generic expense-tracker-secrets --from-literal=...` (bootstrap only).

## Validating locally

```powershell
# Build and inspect an overlay (no cluster needed)
kubectl kustomize infrastructure/kubernetes/overlays/dev
kubectl kustomize infrastructure/kubernetes/overlays/prod
```

## Deploying

```powershell
# Apply an overlay directly
kubectl apply -k infrastructure/kubernetes/overlays/dev

# Or via FluxCD (GitOps): point a Flux Kustomization at infrastructure/kubernetes/flux
```

## GitOps flow (FluxCD)

The intended flow matches the target architecture:

```
Developer → Git → GitHub → Jenkins CI → OCI registry → GitOps repo → FluxCD → cluster
```

- CI builds and pushes `expense-tracker-api:<tag>` and `expense-tracker-web:<tag>`.
- CI updates the image tags in the GitOps repo (or this repo's `overlays/prod/kustomization.yaml`).
- FluxCD watches the repo and reconciles the cluster to match.

## AWS portability

No cloud-specific resources are used. On AWS: EKS (cluster), RDS Postgres (replace the db StatefulSet with an external endpoint in the ConfigMap), ALB Ingress Controller, ECR (registry). Application manifests need no changes beyond the database host and ingress annotations.
