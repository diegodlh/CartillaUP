from lxml import html
import requests
import pdb
import csv
import os
import datetime
import re

urlswitch = "https://www.unionpersonal.com.ar/modulos/afiliados/cartillas/switch.php"

cs = {
    "metropolitana": "Ciudad Autonóma de Buenos Aires y Gran Buenos Aires",
    "costa_atlantica": "Costa Atlántica",
    "interior": "Interior del país"
}

plans = {
    '2': 'Plan Classic',
    '8': 'Plan Familiar',
    'UP10': 'Plan UP10',
    '1': 'Plan PMO',
    '9': 'Plan Monotributista'
}

cartillas = {
    "M": "Médica",
    "F": "Farmaceútica",
    "O": "Odontológica",
    "P": "Optica",
    "R": "Ortopedia",
    "V": "Vacunas"
}


def getOptions(params, data):
    response = requests.post(urlswitch, params=params, data=data)
    tree = html.fromstring(response.text)
    options = tree.xpath('//option')
    return {option.attrib['value']: option.text for option in options if option.attrib['value']}


def getPrestadores(params, data):
    response = requests.post(urlswitch, params=params, data=data)
    tree = html.fromstring(response.text)
    rows = tree.xpath('//tr')
    prestadores = []
    for row in rows:
        cell = row.xpath('./td[2]')[0]
        span_elements = [span_element.text for span_element in cell.getchildren()]
        href = row.xpath('./td[4]/a/@href')[0]
        if re.match(r'^javascript:verMapa\((,?".*?")+\)$', href):
            coordenadas = re.findall(r'"(.*?)"', href)[-1]
        else:
            coordenadas = ''
        prestador = {
            'id': row.attrib['id'],
            'nombre': span_elements[0],
            'especialidad': span_elements[1],
            'direccion': span_elements[2],
            'localidad': span_elements[3],
            'telefono': span_elements[4],
            'observaciones': span_elements[5] if len(span_elements) > 5 else '',
            'coordenadas': coordenadas
        }
        prestadores.append(prestador)
    return prestadores


def omitir(params, data, debug=False):
    if debug:
        pdb.set_trace()
    data = {'c': params['c'], **data}
    i = root
    for log_fieldname in log_fieldnames:
        if log_fieldname in data:
            value = data[log_fieldname]
            if value in i[log_fieldname]:
                i = i[log_fieldname][value]
            else:
                break
        else:
            break
    done = i['done']
    if done:
        print(' > OMITIR...')
    else:
        print()
    return done


global root
root = {'done': False, 'c': {}}
if os.path.exists('log.csv'):
    with open('log.csv') as log_file:
        log_reader = csv.DictReader(log_file)
        for row in log_reader:
            i = root
            for fieldname, value in row.items():
                if fieldname not in i:
                    i[fieldname] = {}
                if value:
                    if value not in i[fieldname]:
                        i[fieldname][value] = {'done': False}
                    i = i[fieldname][value]
            i['done'] = True

log_fieldnames = ['c', 'plan', 'cartilla', 'zona', 'categoria', 'especialidad']
out_fieldnames = log_fieldnames + ['id', 'nombre', 'direccion', 'localidad', 'telefono', 'observaciones', 'coordenadas', 'accedido']
with open('out.csv', 'a') as out_file, open('log.csv', 'a') as log_file:
    out_writer = csv.DictWriter(out_file, fieldnames=out_fieldnames)
    if out_file.tell() == 0:
        out_writer.writeheader()
    log_writer = csv.DictWriter(log_file, fieldnames=log_fieldnames)
    if log_file.tell() == 0:
        log_writer.writeheader()
    params = {}
    data = {}
    for c in cs.keys():
        params['c'] = c
        print('.' + cs[c], end='')
        if omitir(params, data):
            continue
        for plan in plans.keys():
            data['plan'] = plan
            print('..' + plans[plan], end='')
            if omitir(params, data):
                continue
            for cartilla in cartillas.keys():
                params['control'] = 'zonas'
                data['cartilla'] = cartilla
                print('...' + cartillas[cartilla], end='')
                if omitir(params, data):
                    continue
                zonas = getOptions(params, data)
                for zona in zonas.keys():
                    print('....' + zonas[zona], end='')
                    if omitir(params, data):
                        continue
                    params['control'] = 'categorias'
                    data['zona'] = zona
                    categorias = getOptions(params, data)
                    for categoria in categorias.keys():
                        params['control'] = 'especialidades'
                        data['categoria'] = categoria
                        print('.....' + categorias[categoria], end='')
                        if omitir(params, data):
                            continue
                        especialidades = getOptions(params, data)
                        for especialidad in especialidades.keys():
                            params['control'] = 'consulta'
                            data['especialidad'] = especialidad
                            data['localidad'] = 'todas'
                            print('......' + especialidades[especialidad], end='')
                            if omitir(params, data):
                                continue
                            prestadores = getPrestadores(params, data)
                            del data['localidad']
                            for prestador in prestadores:
                                row = {
                                    'c': cs[c],
                                    'plan': plans[plan],
                                    'cartilla': cartillas[cartilla],
                                    'zona': zonas[zona],
                                    'categoria': categorias[categoria],
                                    'especialidad': especialidades[especialidad],
                                    'id': prestador['id'],
                                    'nombre': prestador['nombre'],
                                    'direccion': prestador['direccion'],
                                    'localidad': prestador['localidad'],
                                    'telefono': prestador['telefono'],
                                    'observaciones': prestador['observaciones'],
                                    'coordenadas': prestador['coordenadas'],
                                    'accedido': datetime.date.today()
                                }
                                out_writer.writerow(row)
                            out_file.flush()
                            log_writer.writerow({'c': c, **data})
                            log_file.flush()
                            del data['especialidad']
                        log_writer.writerow({'c': c, **data})
                        log_file.flush()
                        del data['categoria']
                    log_writer.writerow({'c': c, **data})
                    log_file.flush()
                    del data['zona']
                log_writer.writerow({'c': c, **data})
                log_file.flush()
                del data['cartilla']
            log_writer.writerow({'c': c, **data})
            log_file.flush()
            del data['plan']
        log_writer.writerow({'c': c, **data})
        log_file.flush()
os.remove('log.csv')
