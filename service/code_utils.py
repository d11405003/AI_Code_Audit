def format_code_html(code: str) -> str:
    lines = code.splitlines()
    html_lines = [
        f"<div><code>{i+1:>3} | {line}</code></div>" for i, line in enumerate(lines)
    ]
    return (
        "<div style='font-family:monospace; white-space:pre;'>"
        + "\n".join(html_lines)
        + "</div>"
    )

def format_code_diff_html(original: str, fixed: str) -> str:
    original_lines = original.splitlines()
    fixed_lines = fixed.splitlines()

    html_lines = []
    max_lines = max(len(original_lines), len(fixed_lines))

    for i in range(max_lines):
        old_line = original_lines[i] if i < len(original_lines) else ""
        new_line = fixed_lines[i] if i < len(fixed_lines) else ""

        # 有變動的行才標綠色
        if old_line.strip() != new_line.strip():
            html_lines.append(
                f"<div style='background-color:#eaffea;border-left:4px solid green;padding-left:4px;'>"
                f"<code>{i+1:>3} | {new_line}</code></div>"
            )
        else:
            html_lines.append(f"<div><code>{i+1:>3} | {new_line}</code></div>")

    return (
        "<div style='font-family:monospace; white-space:pre;'>"
        + "\n".join(html_lines)
        + "</div>"
    )

def highlight_code_multiple(code: str, highlight_lines: list) -> str:
    lines = code.split('\n')
    html_lines = []
    for i, line in enumerate(lines, start=1):
        if i in highlight_lines:
            html_lines.append(
                f"<div style='background-color:#ffeeee;border-left:4px solid red;padding-left:4px;'>"
                f"<code>{i:>3} | {line}</code></div>"
            )
        else:
            html_lines.append(f"<div><code>{i:>3} | {line}</code></div>")
    return (
        "<div style='font-family:monospace; white-space:pre;'>"
        + "\n".join(html_lines)
        + "</div>"
    )

def highlight_fix_diff(old: str, new: str) -> str:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    html_lines = []
    for i, (o, n) in enumerate(zip(old_lines, new_lines), start=1):
        if o.strip() != n.strip():
            html_lines.append(
                f"<div style='background-color:#eaffea;border-left:4px solid green;padding-left:4px;'>"
                f"<code>{i:>3} | {n}</code></div>"
            )
        else:
            html_lines.append(f"<div><code>{i:>3} | {n}</code></div>")
    return "<div style='font-family:monospace;'>" + "\n".join(html_lines) + "</div>"