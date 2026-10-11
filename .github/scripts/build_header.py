#!/usr/bin/env python3
"""Build assets/header.svg from the config block at the top of README.md.

Edit the block in README.md (the part that starts with "header-config"),
commit, and push. The GitHub Action runs this script and updates the image.
"""
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
TEMPLATE = ROOT / ".github" / "header.template.svg"
OUT = ROOT / "assets" / "header.svg"

SECONDS_PER_ROLE = 3

MAX_TAG_LINES = 3

DEFAULTS = {
    "tag_line_1": "ITI · INTAKE 45",
    "tag_line_2": "CAIRO, EGYPT",
    "name": "PATRICK ATEF",
    "roles": ["Embedded Software Developer"],
}


def read_config(text):
    m = re.search(r"<!--\s*header-config(.*?)-->", text, re.S)
    cfg = dict(DEFAULTS)
    if not m:
        return cfg
    roles, in_roles = [], False
    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line:
            continue
        if in_roles and line.startswith("-"):
            roles.append(line[1:].strip())
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key, val = key.strip().lower(), val.strip()
            if key == "roles":
                in_roles = True
                if val:
                    roles.extend(v.strip() for v in val.split("|") if v.strip())
            else:
                in_roles = False
                if val and (key in cfg or re.fullmatch(r"tag_line_\d+", key)):
                    cfg[key] = val
    if roles:
        cfg["roles"] = roles
    return cfg


def fit(size, text, per_char, avail):
    """Shrink font size so the text fits the available width."""
    return int(max(12, min(size, avail / max(1, len(text)) / per_char)))


def tag_lines(cfg):
    keys = sorted(
        (k for k in cfg if re.fullmatch(r"tag_line_\d+", k)),
        key=lambda k: int(k.rsplit("_", 1)[1]),
    )
    return [cfg[k] for k in keys if cfg[k]][:MAX_TAG_LINES]


def tag_layout(count):
    """First baseline and spacing; 3 lines are packed tighter so they clear the name."""
    return (36, 18) if count >= 3 else (52, 20)


def build_tags(lines):
    first, gap = tag_layout(len(lines))
    out = []
    for i, text in enumerate(lines):
        color = "" if i == 0 else ' fill="#4d6a85"'
        out.append(f'<text x="70" y="{first + gap * i}" class="tag"{color}>{escape(text)}</text>')
    return "\n    ".join(out)


def build_roles(roles):
    n = len(roles)
    f = 1.0 / n
    a, b = round(0.2 * f, 4), round(0.85 * f, 4)
    c = round(f, 4)
    dur = n * SECONDS_PER_ROLE
    out = []
    for i, role in enumerate(roles):
        size = fit(26, role, 0.62, 780)
        out.append(
            f'<text x="70" y="188" class="role" style="font-size:{size}px" opacity="0">{escape(role)}\n'
            f'      <animate attributeName="opacity" values="0;1;1;0;0" '
            f'keyTimes="0;{a};{b};{c};1" dur="{dur}s" '
            f'begin="{i * SECONDS_PER_ROLE}s" repeatCount="indefinite"/>\n'
            f'    </text>'
        )
    return "\n    ".join(out)


def main():
    cfg = read_config(README.read_text(encoding="utf-8"))
    svg = TEMPLATE.read_text(encoding="utf-8")
    lines = tag_lines(cfg)
    svg = svg.replace("{{TAGS}}", build_tags(lines))
    svg = svg.replace("{{DOT_Y}}", str(tag_layout(len(lines))[0] - 5))
    svg = svg.replace("{{NAME}}", escape(cfg["name"]))
    svg = svg.replace("{{NAME_SIZE}}", str(fit(70, cfg["name"], 0.74, 760)))
    svg = svg.replace("{{ROLES}}", build_roles(cfg["roles"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(cfg['roles'])} roles)")


if __name__ == "__main__":
    main()
