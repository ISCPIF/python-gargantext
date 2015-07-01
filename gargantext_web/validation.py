from rest_framework.exceptions import APIException

from datetime import datetime


__all__ = ['validate']


_types_names = {
    bool:       'boolean',
    int:        'integer',
    float:      'float',
    str:        'string',
    dict:       'object',
    list:       'array',
    datetime:   'datetime',
}


class ValidationException(APIException):
    status_code = 400
    default_detail = 'Bad request!'


def validate(value, expected, path='input'):
    # Is the expected type respected?
    if 'type' in expected:
        expected_type = expected['type']
        if not isinstance(value, expected_type):
            if expected_type in (bool, int, float, str, datetime, ):
                try:
                    if expected_type == bool:
                        value = value not in {0, 0.0, '', '0', 'false'}
                    elif expected_type == datetime:
                        value = value + '2000-01-01T00:00:00Z'[len(value):]
                        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
                    else:
                        value = expected_type(value)
                except ValueError:
                    raise ValidationException('%s should be a JSON %s, but could not be parsed as such' % (path, _types_names[expected_type], ))
            else:
                raise ValidationException('%s should be a JSON %s' % (path, _types_names[expected_type], ))
    else:
        expected_type = type(value)

    # Is the value in the expected range?
    if 'range' in expected:
        expected_range = expected['range']
        if isinstance(expected_range, tuple):
            if expected_type in (int, float):
                tested_value = value
                tested_name = 'value'
            elif expected_type in (str, list):
                tested_value = len(value)
                tested_name = 'length'
            if tested_value < expected_range[0]:
                raise ValidationException('%s should have a minimum %s of %d' % (path, tested_name, expected_range[0], ))
            if len(expected_range) > 1 and tested_value > expected_range[1]:
                raise ValidationException('%s should have a maximum %s of %d' % (path, tested_name, expected_range[1], ))
        elif isinstance(expected_range, (list, set, dict, )) and value not in expected_range:
            expected_values = expected_range if isinstance(expected_range, list) else expected_range.keys()
            expected_values = [str(value) for value in expected_values if isinstance(value, expected_type)]
            if len(expected_values) < 16:
                expected_values_str = '", "'.join(expected_values)
                expected_values_str = '"' + expected_values_str + '"'
            else:
                expected_values_str = '", "'.join(expected_values[:16])
                expected_values_str = '"' + expected_values_str + '"...'

            raise ValidationException('%s should take one of the following values: %s' % (path, expected_values_str, ))

    # Do we have to translate through a dictionary?
    if 'translate' in expected:
        translate = expected['translate']
        if callable(translate):
            value = translate(value)
            if value is None and expected.get('required', False):
                raise ValidationException('%s has been given an invalid value' % (path, ))
            return value
        try:
            value = expected['translate'][value]
        except KeyError:
            if expected.get('translate_fallback_keep', False):
                return value
            if expected.get('required', False):
                raise ValidationException('%s has been given an invalid value' % (path, ))
            else:
                return expected.get('default', value)

    # Are we handling an iterable?
    if expected_type in (list, dict):
        if 'items' in expected:
            expected_items = expected['items']
            if expected_type == list:
                for i, element in enumerate(value):
                    value[i] = validate(element, expected_items, '%s[%d]' % (path, i, ))
            elif expected_type == dict:
                if expected_items:
                    for key in value:
                        if key not in expected_items:
                            raise ValidationException('%s should not have a "%s" key.' % (path, key, ))                        
                for expected_key, expected_value in expected_items.items():
                    if expected_key in value:
                        value[expected_key] = validate(value[expected_key], expected_value, '%s["%s"]' % (path, expected_key, ))
                    elif 'required' in expected_value and expected_value['required']:
                        raise ValidationException('%s should have a "%s" key.' % (path, expected_key, ))
                    elif 'default' in expected_value:
                        value[expected_key] = expected_value['default']

    # Let's return the proper value!
    return value
