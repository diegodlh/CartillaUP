from lxml import html
import requests
import pdb
import csv

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


fieldnames = ['c', 'plan', 'cartilla', 'zona', 'categoria', 'especialidad', 'nombre', 'direccion', 'localidad', 'telefono']
with open('out.csv', 'w') as fileout:
    writer = csv.DictWriter(fileout, fieldnames=fieldnames)
    writer.writeheader()
    params = {}
    data = {}
    for c in cs.keys():
        print('.' + cs[c])
        params['c'] = c
        for plan in plans.keys():
            print('..' + plans[plan])
            data['plan'] = plan
            for cartilla in cartillas.keys():
                print('...' + cartillas[cartilla])
                params['control'] = 'zonas'
                data['cartilla'] = cartilla
                zonas = getOptions(params, data)
                for zona in zonas.keys():
                    print('....' + zonas[zona])
                    params['control'] = 'categorias'
                    data['zona'] = zona
                    categorias = getOptions(params, data)
                    for categoria in categorias.keys():
                        print('.....' + categorias[categoria])
                        params['control'] = 'especialidades'
                        data['categoria'] = categoria
                        especialidades = getOptions(params, data)
                        for especialidad in especialidades.keys():
                            print('......' + especialidades[especialidad])
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
                                writer.writerow(row)
                            fileout.flush()
                            # pdb.set_trace()
