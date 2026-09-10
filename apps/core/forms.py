def style_form_widgets(form):
    for field in form.fields.values():
        widget = field.widget
        input_type = getattr(widget, "input_type", None)
        if input_type in {"checkbox", "radio", "hidden"}:
            continue
        current = widget.attrs.get("class", "")
        extra = "field"
        widget.attrs["class"] = f"{current} {extra}".strip()


def mark_money_field(field, placeholder="0,00"):
    attrs = field.widget.attrs
    attrs["inputmode"] = "decimal"
    attrs["autocomplete"] = "off"
    attrs["placeholder"] = placeholder
    attrs["data-money"] = "1"
    current = attrs.get("class", "")
    if "field-money" not in current:
        attrs["class"] = f"{current} field-money".strip()
