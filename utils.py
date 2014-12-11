# coding: utf8

# stdlib
import re

# 3rd party
from flask import jsonify
import gspread

# own
import settings


re_type = type(re.compile(''))


def get_flows():
    return settings.flows.keys()


def merge_settings(flowname):
    merged_settings = settings.general_settings.copy()
    merged_settings.update(settings.flows.get(flowname, {}))
    return merged_settings


def envelope(response, success=True):
    return jsonify({
        'status': 'success' if success else 'error',
        'data': response
    })


def any_istrue(text, selector):

    if isinstance(selector, basestring):
        return selector in text

    if type(selector) == re_type:
        return selector.search(text)

    return any(any_istrue(text, sel) for sel in selector)


def get_field_value(name, selector, text):

    if type(selector) == re_type:
        if selector.search(text):
            return selector.search(text).group(1)
        return None

    for subsel in selector:

        if type(subsel) == re_type:
            if subsel.search(text):
                return subsel.search(text).group(1)
            continue

        if len(subsel) and isinstance(subsel[0], basestring):
            if any_istrue(text, subsel[1]):
                return subsel[0]
            continue


def format_fields(fields, fields_data):

    values = {}
    for field_name, field_val in fields.items():

        if field_name in fields_data.keys():
            row = fields_data.get(field_name)

            if isinstance(row, basestring):
                values[row.upper()] = field_val
                continue

            data = row
            if data.get('format'):
                field_val = data['format'](field_val)

            values[data['col'].upper()] = field_val

    return values


def get_empty_line(sheet, rows):
    lines_to_fetch = 20
    rows = sorted(rows)
    first_row, last_row = (rows[0], rows[-1])

    for start_line in range(1, sheet.row_count-1, lines_to_fetch):
        end_line = start_line + lines_to_fetch

        data = sheet.range('{}{}:{}{}'.format(
            first_row, start_line, last_row, end_line))

        line_length = ord(last_row) - ord(first_row) + 1
        for start_row in range(0, len(data), line_length):
            line = data[start_row:start_row + line_length]

            if not any(cell.value for cell in line):
                return line


def update_spreadsheet(values, settings):
    gc = gspread.login(settings['google_user']['username'],
                       settings['google_user']['password'])

    # sempre atualiza a primeira folha da planilha
    sheet = gc.open_by_key(settings['spreadsheet_key']).get_worksheet(0)

    # pega as celulas da primeira linha
    # cujos campos a serem gravados estão vazios
    line = get_empty_line(sheet, values.keys())

    # nenhuma linha disponivel (nunca deve acontecer rs)
    if not line:
        raise Exception('Nenhuma linha vazia encontrada')

    # itera sobre uma copia da lista line pq ela sera alterada
    # durante o loop
    for cell in line[:]:
        # obtem a letra da coluna da celula a ser atualizada
        row = chr(cell.col + 64)

        if values.get(row):
            cell.value = values[row]
        else:
            line.remove(cell)

    # faz o request de update
    sheet.update_cells(line)
