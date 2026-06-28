# Skill Template

Copy this directory to `skills/<category>/<your-skill-name>/` and edit SKILL.md.

Required frontmatter:
- `name`: lowercase, hyphens, ≤64 chars
- `description`: ≤1024 chars, must be a single line OR a YAML block scalar
- `version`, `author`, `license`: peer convention (not enforced)
- `metadata.hermes.tags`, `metadata.hermes.related_skills`: peer convention

Body must follow this structure:
1. `# Title`
2. `## Overview`
3. `## When to Use` (with bullet triggers + "don't use for" counter-triggers)
4. Topic sections (numbered steps, each with completion criteria)
5. `## Common Pitfalls`
6. `## Verification Checklist`

See `hermes-agent-skill-authoring` skill for full authoring guide.
