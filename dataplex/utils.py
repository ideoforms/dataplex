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

def segment_contiguous(array, min_length:int = 0):
    """
    Given a list of scalar values, segments the list into separate contiguous sequences and returns
    a list of tuples, each containingthe value and the number of contiguous occurrences

    e.g.: segment_contiguous([1, 1, 1, 2, 2, 3, 3, 3, 3, 1, 1]) returns [(1, 3), (2, 2), (3, 4), (1, 2)]

    Args:
        array: A list of scalar values to be segmented.
        min_length (int, optional): If specified, only segments with a length greater than or equal
                                    to this value will be returned. Defaults to 0.

    Returns:
        tuple: The segmented values, each represented as a tuple of (value, count).
    """
    segmented_values = []
    if len(array) > 0:
        current_value = array[0]
        count = 1
        for value in array[1:]:
            if value == current_value:
                count += 1
            else:
                if count >= min_length:
                    segmented_values.append((current_value, count))
                current_value = value
                count = 1
        if count >= min_length:
            segmented_values.append((current_value, count))
    # print(segmented_values)
    return segmented_values