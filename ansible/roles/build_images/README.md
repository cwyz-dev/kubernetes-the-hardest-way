# build_images role

## FEATURES
- DAG-based builds
- Async execution
- Smart rebuild detection
- Registry caching
- Test gating
- SBOM generation (Syft)
- Vulnerability scanning (Grype)
- Image signing (Cosign)
- Provenance (SLSA-style)
- Policy enforcement (OPA-ready)
- Structured logs
- Timing metrics
- Checkpoint/Resume support

## FEATURE FLAGS
See defaults/main.yaml

## USAGE
```yaml
- hosts: all
  roles:
    - build_images
