# Documentation

This directory contains design documents, specifications, and examples for the Simple Repository Downloader project.

## Contents

### Plans

- **[2025-12-27-repo-downloader-design.md](plans/2025-12-27-repo-downloader-design.md)** - Comprehensive design document covering architecture, components, data flow, and implementation details.

### Examples

- **[config-example.yaml](examples/config-example.yaml)** - Example configuration file with detailed comments
- **[cli-usage.md](examples/cli-usage.md)** - CLI usage examples and recipes

## Quick Links

### For Users

- [CLI Usage Examples](examples/cli-usage.md) - How to use the command-line tool
- [Configuration Example](examples/config-example.yaml) - Template config file

### For Developers

- [Design Document](plans/2025-12-27-repo-downloader-design.md) - Complete architecture and design decisions
  - Technology stack and rationale
  - Component architecture
  - API integration details
  - Dashboard and UI design
  - Error handling strategy
  - Testing approach

## Project Overview

Simple Repository Downloader is a Python-based tool for efficiently downloading all repositories from GitHub or GitLab users/organizations.

### Key Features

- **Parallel Downloads** - Configurable concurrent cloning for speed
- **Real-time Dashboard** - Live progress tracking with Rich TUI
- **Interactive Command Shell** - Control downloads on the fly
- **Smart Error Handling** - Collect and resolve issues interactively
- **Multi-platform** - Support for both GitHub and GitLab
- **Flexible Configuration** - CLI args, config files, or programmatic API
- **Resume Capability** - Pick up where you left off after interruption

### Technology Stack

- Python 3.10+
- asyncio for concurrency
- aiohttp for API calls
- Rich for terminal UI
- Click for CLI
- Pydantic for configuration

## Getting Started

See the [CLI Usage Guide](examples/cli-usage.md) for usage examples.

See the [Design Document](plans/2025-12-27-repo-downloader-design.md) for implementation details.
