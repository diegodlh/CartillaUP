from lxml import html
import requests
import re
import csv


with open('/tmp/cartilla.html') as filein:
    cartilla = ''.join(filein.readlines())

tree = html.fromstring(cartilla)
direcciones = tree.xpath('//*[@id="matriz"]/tbody/tr/td[2]/span[3]')

direcciones = [d.text.split('-')[0].strip() for d in direcciones]
direcciones = [re.sub(r'\s+', ' ', d) for d in direcciones]

with open('/tmp/cartilla.csv', 'w') as fileout:
    writer = csv.writer(fileout)
    writer.writerow(['address', 'city'])
    for direccion in direcciones:
        writer.writerow([direccion, 'Ciudad de Buenos Aires'])
