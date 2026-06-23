dirs = {
    "/": {"count": 1, "type": "root"},
    "/src/Controllers": {"count": 5, "type": "controller"},
    "/src/Models": {"count": 2, "type": "model"},
    "/public/assets": {"count": 10, "type": "asset"},
}

ascii_tree_lines = ["."]
seen_dirs = set()
for path, info in sorted(dirs.items()):
    if path == "/":
        continue
    parts = [p for p in path.split('/') if p]
    for i in range(1, len(parts) + 1):
        subpath = "/".join(parts[:i])
        if subpath not in seen_dirs:
            seen_dirs.add(subpath)
            indent = "│   " * (i - 1)
            # Find if this exact subpath is in dirs
            if "/" + subpath in dirs:
                sub_info = dirs["/" + subpath]
                ascii_tree_lines.append(f"{indent}├── {parts[i-1]}/ ({sub_info.get('count', 0)} files, {sub_info.get('type')})")
            else:
                ascii_tree_lines.append(f"{indent}├── {parts[i-1]}/")

print("\n".join(ascii_tree_lines))
