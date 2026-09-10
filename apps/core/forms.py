def style_form_widgets(form):
    for field in form.fields.values():
        widget = field.widget
        input_type = getattr(widget, "input_type", None)
        if input_type in {"checkbox", "radio", "hidden"}:
            continue
        current = widget.attrs.get("class", "")
        extra = "field"
        widget.attrs["class"] = f"{current} {extra}".strip()
