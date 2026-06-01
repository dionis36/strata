import os
import re

d = "frontend/views"
for f in os.listdir(d):
    if not f.endswith(".py"): continue
    p = os.path.join(d, f)
    with open(p, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Replace st.success("✅ ...") -> st.success("...", icon=":material/check_circle:")
    content = re.sub(r'st\.success\(\s*f?["\']✅\s*(.*?)(["\'])\s*\)', r'st.success("\1", icon=":material/check_circle:")', content)
    # Replace st.warning("🚨 ...") -> st.warning("...", icon=":material/warning:")
    content = re.sub(r'st\.warning\(\s*f?["\'][🚨⚠️]\s*(.*?)(["\'])\s*\)', r'st.warning("\1", icon=":material/warning:")', content)
    content = re.sub(r'st\.error\(\s*f?["\'][🚨☠️]\s*(.*?)(["\'])\s*\)', r'st.error("\1", icon=":material/error:")', content)
    content = re.sub(r'st\.info\(\s*f?["\'][💡🌐]\s*(.*?)(["\'])\s*\)', r'st.info("\1", icon=":material/info:")', content)
    
    # Define a list of common emojis used in the project
    emojis = ["🚨", "⚠️", "📊", "✅", "🛡️", "📈", "🟢", "🟡", "🟠", "🔴", "⚪", "🔍", "🧠", "🏗️", "🚪", "🎮", "🖼️", "⚙️", "⚡", "📦", "🧩", "🌎", "💡", "🌐", "☠️", "🔐", "🔑", "🖥️", "🛑", "🔌", "🕸️", "📋", "🎯", "🧐", "🤖", "📖", "⬇️", "👁️", "🗺️", "🔗", "💾", "🏛️", "🔄", "🏷️", "📁"]
    
    for e in emojis:
        content = content.replace(e + " ", "")
        content = content.replace(e, "")
    
    with open(p, "w", encoding="utf-8") as file:
        file.write(content)
print("Done cleaning emojis!")
