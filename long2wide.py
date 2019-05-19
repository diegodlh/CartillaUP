import pandas as pd
import pdb

df = pd.read_csv(
  'out.csv',
  keep_default_na=False,
  parse_dates=['accedido']
)
df.especialidad = df[['cartilla', 'categoria', 'especialidad']].apply(' > '.join, axis=1)


def cat2code(df, fieldname):
  df[fieldname] = df[fieldname].astype('category')
  df[fieldname].cat.categories.name = df[fieldname].name
  df[fieldname].cat.categories.to_frame(index=False).to_csv(fieldname + 'es.csv', index_label='code') 
  df[fieldname] = df[fieldname].cat.codes


# cat2code(df, 'especialidad')
# cat2code(df, 'localidad')

df.telefono = df.telefono.str.replace('^Tel: ', '')

# id no identifica prestador unívocamente, sino que hay un id por cada línea en out.csv

# # muestra prestadores que coinciden en nombre y dirección, pero difieren en localidad o coordenadas
# prestadores = df.groupby(['nombre','direccion','localidad','coordenadas']).agg({'especialidad': set}).reset_index()
# grouped = prestadores.groupby(['nombre', 'direccion']) 
# filtered = grouped.filter(lambda x: len(x) > 1)
# filtered[['nombre','direccion','localidad','coordenadas']]
# # al 04may19 las discrepancias son errores de localidad: se indican dos distritos diferentes por error

# # muestra prestadores que coinciden en nombre y dirección, pero difieren en teléfono
# prestadores = df.groupby(['nombre','direccion','telefono']).agg({'especialidad': set}).reset_index()
# grouped = prestadores.groupby(['nombre', 'direccion']) 
# filtered = grouped.filter(lambda x: len(x) > 1)
# filtered[['nombre','direccion','telefono']]
# # algunas diferencias son errores de tipeo, pero no se puede descartar que haya distintos teléfonos
# # para distintas especialidades o planes atendidos por un mismo prestador

# # muestra prestadores que coinciden en nombre y dirección, pero difieren en observaciones
# prestadores = df.groupby(['nombre','direccion','observaciones']).agg({'especialidad': set}).reset_index()
# grouped = prestadores.groupby(['nombre', 'direccion']) 
# filtered = grouped.filter(lambda x: len(x) > 1)
# filtered[['nombre','direccion','observaciones']]
# # algunas diferencias son errores de tipeo, pero no se puede descartar que haya distintas observaciones
# # para distintas especialidades o planes atendidos por un mismo prestador

# antes de agrupar, sobreescribir fecha de acceso con la más vieja disponible para cada prestador
df.accedido = df.groupby(['nombre', 'direccion', 'localidad', 'telefono', 'observaciones', 'coordenadas']
  ).accedido.transform(min)

prestadores = df.groupby(['nombre', 'direccion', 'localidad', 'telefono', 'observaciones', 'coordenadas', 'plan', 'accedido']
  ).agg({'especialidad': set})
prestadores = prestadores.unstack(level='plan')
prestadores.columns = prestadores.columns.droplevel()
# pdb.set_trace()
prestadores = prestadores.reset_index()

properties = [column for column in prestadores.columns if column != 'coordenadas']
geojson = prestadores[
  prestadores['coordenadas'].str.contains(r'^-?\d+.\d+,-?\d+.\d+$', regex=True)
].reset_index(drop=True)
geojson['properties'] = geojson[properties].apply(lambda x: x.to_dict(), axis=1)
geojson['geometry'] = geojson['coordenadas'].apply(
  lambda x: {'type': 'Point', 'coordinates': [float(i) for i in x.split(',')][::-1]}  # geojson usa longitud, latitud
)
geojson['type'] = 'Feature'
geojson = geojson.drop(properties + ['coordenadas'], axis=1)

prestadores.to_csv('prestadores.csv', index=None)
prestadores.to_json('prestadores.json', orient='records')
geojson.to_json('prestadores.geojson', orient='records')