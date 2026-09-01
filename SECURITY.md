# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| Unreleased (main) | ✅ |

## Reporting a vulnerability

Do **not** open a public GitHub issue for security vulnerabilities.

1. Email the maintainer privately (see repository owner profile) with:
   - description of the issue and potential impact,
   - steps to reproduce or proof of concept,
   - affected versions/components.
2. You will receive an acknowledgement within 3 business days.
3. We will coordinate a fix and disclosure timeline with you. Credit will be given in the release notes unless you prefer anonymity.

## Scope notes

- The API enforces per-user data isolation at the repository layer; reports of cross-user data access are treated as critical.
- Secrets must never be committed. If you find a committed secret, report it immediately as above.
