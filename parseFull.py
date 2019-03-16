from lxml import html
import requests
import pdb
import csv
import os

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
    tree = html.fromstring(response.content)
    options = tree.xpath('//option')
    return {option.attrib['value']: option.text for option in options if option.attrib['value']}


def getPrestadores(params, data):
    response = requests.post(urlswitch, params=params, data=data)
    tree = html.fromstring(response.content)
    cells = tree.xpath('//tr/td[2]')
    prestadores = []
    for cell in cells:
        span_elements = [span_element.text for span_element in cell.getchildren()]
        prestador = {
            'nombre': span_elements[0],
            'especialidad': span_elements[1],
            'direccion': span_elements[2],
            'localidad': span_elements[3],
            'telefono': span_elements[4]
        }
        prestadores.append(prestador)
    return prestadores


def omitir(value, done):
    if value in done:
        print(' > OMITIR...')
        return True
    else:
        print()
        return False


log_fieldnames = ['c', 'plan', 'cartilla', 'zona', 'categoria', 'especialidad']
done = {fieldname: [] for fieldname in log_fieldnames}
if os.path.exists('log.csv'):
    with open('log.csv') as log_file:
        log_reader = csv.DictReader(log_file)
        for row in log_reader:
            for fieldname, value in reversed(row.items()):
                if value != '*':
                    if value not in done[fieldname]:
                        done[fieldname].append(value)
                    break


out_fieldnames = log_fieldnames + ['nombre', 'direccion', 'localidad', 'telefono']
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
        print('.' + cs[c], end='')
        if omitir(c, done['c']):
            continue
        params['c'] = c
        for plan in plans.keys():
            print('..' + plans[plan], end='')
            if omitir(plan, done['plan']):
                continue
            data['plan'] = plan
            for cartilla in cartillas.keys():
                print('...' + cartillas[cartilla], end='')
                if omitir(cartilla, done['cartilla']):
                    continue
                params['control'] = 'zonas'
                data['cartilla'] = cartilla
                zonas = getOptions(params, data)
                for zona in zonas.keys():
                    print('....' + zonas[zona], end='')
                    if omitir(zona, done['zona']):
                        continue
                    params['control'] = 'categorias'
                    data['zona'] = zona
                    categorias = getOptions(params, data)
                    for categoria in categorias.keys():
                        print('.....' + categorias[categoria], end='')
                        if omitir(categoria, done['categoria']):
                            continue
                        params['control'] = 'especialidades'
                        data['categoria'] = categoria
                        especialidades = getOptions(params, data)
                        for especialidad in especialidades.keys():
                            print('......' + especialidades[especialidad], end='')
                            if omitir(especialidad, done['especialidad']):
                                continue
                            params['control'] = 'consulta'
                            data['especialidad'] = especialidad
                            data['localidad'] = 'todas'
                            prestadores = getPrestadores(params, data)
                            for prestador in prestadores:
                                row = {
                                    'c': cs[c],
                                    'plan': plans[plan],
                                    'cartilla': cartillas[cartilla],
                                    'zona': zonas[zona],
                                    'categoria': categorias[categoria],
                                    'especialidad': especialidades[especialidad],
                                    'nombre': prestador['nombre'],
                                    'direccion': prestador['direccion'],
                                    'localidad': prestador['localidad'],
                                    'telefono': prestador['telefono']
                                }
                                out_writer.writerow(row)
                            out_file.flush()
                            del params['control']
                            del data['localidad']
                            log_writer.writerow({**params, **data})
                        data['especialidad'] = '*'
                        log_writer.writerow({**params, **data})
                    data['categoria'] = '*'
                    log_writer.writerow({**params, **data})
                data['zona'] = '*'
                log_writer.writerow({**params, **data})
            data['cartilla'] = '*'
            log_writer.writerow({**params, **data})
        data['plan'] = '*'
        log_writer.writerow({**params, **data})
os.remove('log.csv')
