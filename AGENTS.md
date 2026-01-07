# Substance Automation Toolkit Development Environment

## Available AI Skills

This project is configured with the following AI assistant capabilities:

### Codex OpenSkills (v0.77.0)
- **Status**: ✅ Installed and Configured
- **Configuration**: `~/.codex/config.toml`
- **Model Provider**: OpenAI
- **Model**: GPT-4
- **Features**: Advanced code generation, refactoring, and debugging

### Claude OpenSkills (v1.2.1)
- **Status**: ✅ Installed and Initialized
- **Skills Location**: `.claude/skills/`
- **Total Skills**: 16 project skills

#### Available Skills:
1. **algorithmic-art** - Creating algorithmic art using p5.js
2. **brand-guidelines** - Anthropic official brand styling
3. **canvas-design** - Beautiful visual art in PNG/PDF
4. **doc-coauthoring** - Structured documentation workflow
5. **docx** - Comprehensive Word document creation and editing
6. **frontend-design** - Production-grade frontend interfaces
7. **internal-comms** - Internal communications writing
8. **mcp-builder** - MCP (Model Context Protocol) server creation
9. **pdf** - PDF manipulation and generation
10. **pptx** - PowerPoint presentation creation and editing
11. **skill-creator** - Guide for creating new skills
12. **slack-gif-creator** - Animated GIFs for Slack
13. **theme-factory** - Artifact styling themes
14. **web-artifacts-builder** - Complex React/Tailwind artifacts
15. **webapp-testing** - Playwright-based web testing
16. **xlsx** - Spreadsheet creation and analysis

### OpenSpec (v0.17.2)
- **Status**: ✅ Installed and Configured
- **Configuration**: `.openspec/config.json`
- **Integration**: Enabled with Claude Skills
- **Features**: Standardized AI skill interfaces

## Project Configuration

### Environment Setup
- Python 3.x with pysbs API installed
- Substance Automation Toolkit Pro 15.0.3
- Node.js for AI tooling
- Git for version control

### Key Directories
- `.claude/` - Claude configuration and skills
- `.openspec/` - OpenSpec configuration
- `Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/` - SAT installation

### Usage
All AI assistants are now configured and ready to use. Skills are automatically available when working with Claude Code.

---
Last Updated: 2026-01-05