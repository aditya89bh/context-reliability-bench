# Security Policy

## Supported Versions

`context-reliability-bench` has not yet made a stable release.
Security fixes will be applied to the `main` branch only.

| Version | Supported |
|---------|-----------|
| main (unreleased) | Yes |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities by email to **aditya89bh@gmail.com** with the subject
line `[SECURITY] context-reliability-bench`.

Include:

- A description of the vulnerability and its potential impact
- Steps to reproduce or a minimal proof-of-concept
- Affected versions or commits

You will receive an acknowledgement within **72 hours**.  If the issue is
confirmed, a fix will be prepared and a patched release (or advisory) will be
published as soon as practical.

## Scope

This library processes local fixture files and executes user-supplied
benchmark configurations.  The primary threat surface is:

- **Fixture loading** — JSON files read from disk; malformed input raises
  a `FixtureError` rather than executing arbitrary code.
- **YAML config loading** — implemented without PyYAML; no deserialisation
  of arbitrary Python objects.
- **Cache storage** — writes JSON files to a caller-specified directory;
  no shell commands are executed.

## Out of Scope

- Denial-of-service issues caused by processing very large fixture files.
- Issues in optional third-party libraries (LangChain, LlamaIndex) used
  via the integration examples.
