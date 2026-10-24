import re


def personalize(template: str, lead: dict) -> str:
    def repl(m):
        key = m.group(1).strip()
        # common keys
        if key == "first_name" and lead.get("first_name"):
            return str(lead["first_name"])
        if key == "last_name" and lead.get("last_name"):
            return str(lead["last_name"])
        if key == "email":
            return str(lead.get("email") or "")
        if key == "company" and lead.get("company"):
            return str(lead["company"])
        if key == "title" and lead.get("title"):
            return str(lead["title"])
        if key in lead and lead[key] is not None:
            return str(lead[key])
        if lead.get("custom_fields") and key in lead["custom_fields"] and lead["custom_fields"][key] is not None:
            return str(lead["custom_fields"][key])
        return m.group(0)  # leave as-is if unknown
    return re.sub(r'\{\{\s*([a-zA-Z0-9_]+)\s*\}\}', repl, template)
