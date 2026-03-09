# Branch Protection Evidence: GATEFLOW-V1-004

Updated: 2026-03-09

## Command
```bash
gh api repos/0202alcc/gateflow/branches/main/protection
```

## Result
`main` branch protection is enabled with strict required checks.

Required check contexts:
- `planning-standardization-gates / planning-gates`
- `backend-local-external-smoke / backend-local-external-smoke`
- `release-reproducibility / reproducible-artifacts`

Additional controls:
- `required_conversation_resolution=true`
- `allow_force_pushes=false`
- `allow_deletions=false`

## Raw Evidence Excerpt
```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "planning-standardization-gates / planning-gates",
      "backend-local-external-smoke / backend-local-external-smoke",
      "release-reproducibility / reproducible-artifacts"
    ]
  }
}
```
