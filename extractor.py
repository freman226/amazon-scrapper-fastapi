def extract_children_text(data):
    children_texts = []
    for idx, item in enumerate(data):
        text = ""
        if "children_text" in item and item["children_text"]:
            text = list(item["children_text"].values())[0]
        children_texts.append({"id": idx + 1, "text": text})
    return children_texts
