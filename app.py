#! /usr/bin/env python
# coding: utf8

from flask import Flask, g, jsonify, request

from utils import (envelope,
                   get_field_value,
                   format_fields,
                   update_spreadsheet,
                   merge_settings,
                   get_flows)


application = app = Flask('txt2gspread')


@app.route('/<flow>', methods=['POST', 'GET'])
def execute_flow(flow):

    if flow not in get_flows():
        return envelope('unknown flow {}'.format(flow))

    settings = merge_settings(flow)

    if request.method not in settings.get('http_methods'):
        return envelope('invalid http method', success=False)

    # read the args from request type data
    params = request.form if request.method == 'POST' else request.args

    if params.get('token') != settings.get('token'):
        return envelope('incorrect token', success=False)

    text = params.get('text')

    if not text:
        return envelope('empty text', success=False)

    if not settings.get('activate_flow_re').search(text):
        return envelope('no activation phrase found - ignored')

    fields = dict(
        (field, get_field_value(field, settings['selectors'][field], text))
        for field in settings['selectors'].keys()
    )

    values = format_fields(fields, settings['fields'])

    try:
        update_spreadsheet(values, settings)
    except Exception as e:
        return envelope('error updating spreadsheet - '
                        '{} {}'.format(type(e).__name__, str(e)),
                        success=False)

    return envelope('data successfully saved')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
