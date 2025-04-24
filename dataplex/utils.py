import datetime

def serialise_data(data: dict) -> dict:
    """
    Serialise the record.

    Args:
        value: The value to serialise.

    Returns:
        The JSON-encoded value. For ints, floats, and strings, this is the value itself.
        For datetime objects, this is a string in the format "YYYY-MM-DD HH:MM:SS.ssssss".
    """
    structure = {}
    for name, record in data.items():
        try:
            #------------------------------------------------------------------------
            # For ECDFNormaliser objects, pass their dictionary of properties.
            #------------------------------------------------------------------------
            structure[name] = {
                "value" : record.value,
                "normalised" : record.normalised,
                "previous_value" : record.previous_value,
                "previous_normalised" : record.previous_normalised,
                "change" : record.change
            }
        except AttributeError:
            #------------------------------------------------------------------------
            # For scalar fields (eg time), simply pass their value.
            #------------------------------------------------------------------------
            if isinstance(record, datetime.datetime):
                structure[name] = record.strftime("%Y-%m-%d %H:%M:%S.%f")
            else:
                structure[name] = record
    return structure