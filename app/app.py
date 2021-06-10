import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_table
from flask_caching import Cache

import requests
import simplejson

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from colour import Color

import datetime
import logging
import modelo

logging.basicConfig(level=logging.DEBUG,
                    format=' %(asctime)s - %(levelname)s - %(message)s')

###########################################
################ Funções
###########################################
multi_global = False
multi_global2 = False


# 1: Curitiba
# 2: NUC
# 3: Paraná
# 4: Regionais


def get_options(variavel_local, filtro_value=0):
    opts = 0
    if variavel_local == 1:
        opts = [{'label': dic_locais[distritos[i]], 'value': distritos[i]} for i in range(len(distritos))]
    elif variavel_local == 2:
        opts = [{'label': dic_locais[NUC[i]], 'value': NUC[i]} for i in range(len(NUC))]
    elif variavel_local == 3:
        if filtro_value == 0:
            opts = [{'label': dic_locais[municipios[i]], 'value': municipios[i]} for i in range(len(municipios))]
        else:
            filtro = df_def_reg.groupby("regional").get_group(dic_reg[filtro_value])["codigo"].reset_index(
                drop=True).to_numpy()
            mun = df_PR[df_PR.codigo.isin(filtro)].sort_values("localidade").localidade.drop_duplicates().to_numpy()
            opts = [{'label': dic_locais[mun[i]], 'value': mun[i]} for i in range(len(mun))]
    elif variavel_local == 4:
        opts = [{'label': dic_locais[regionais[i]], 'value': regionais[i]} for i in range(len(regionais))]

    return opts


def eh_none(n):
    if n is None:
        return 0
    else:
        return n


def compare(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4):
    if (nav1 > n0) & (nav1 > n1) & (nav1 > n2) & (nav1 > n3) & (nav1 > n4):
        return False
    elif (nav2 > n0) & (nav2 > n1) & (nav2 > n2) & (nav2 > n3) & (nav2 > n4):
        return False
    elif (nav3 > n0) & (nav3 > n1) & (nav3 > n2) & (nav3 > n3) & (nav3 > n4):
        return False
    elif (nav4 > n0) & (nav4 > n1) & (nav4 > n2) & (nav4 > n3) & (nav4 > n4):
        return False
    else:
        return True


def get_mode(dados_state, n=1):
    if (dados_state is None) | (dados_state == []) | (dados_state == ['relativo']):
        if n == 0:
            return "acumulado"
        else:
            return "markers"
    else:
        if n == 0:
            return "diario"
        else:
            return 'lines+markers'


def get_serie_model(df_modelo, dados, dados_state, local, delta_tempo):
    variavel = get_y(dados, dados_state)
    if dados == 0:
        data = df_modelo["casosAcumulados"].reset_index(drop=True)
    else:
        data = df_modelo["obitosAcumulados"].reset_index(drop=True)

    params = fit(local, data)

    if (variavel == "casosAcumulados") | (variavel == "obitosAcumulados"):
        modelo_fit = modelo.modelo_acumulado(params, delta_tempo, len(data), data[0])
    else:
        modelo_fit = modelo.modelo_diario(params, delta_tempo, len(data), data[0])

    day0 = pd.to_datetime(list(df_modelo['date'])[0])
    t = modelo_fit[0]
    t = list(map(lambda ti: day0 + datetime.timedelta(ti), t))
    y_model = modelo_fit[1]

    fig_max = go.Figure()
    fig_max.add_trace(
        go.Scatter(
            x=df_modelo["date"],
            y=df_modelo[variavel],
            mode=get_mode(dados_state),
            line={'color': px.colors.qualitative.Light24[0]},
            name='Dados'
        )
    )

    fig_max.add_trace(
        go.Scatter(
            x=t,
            y=y_model,
            mode='lines',
            line={'color': 'black'},
            name='Modelo'
        )
    )

    fig_max.update_layout(
        title=dic_locais[local] + " - " + label[variavel].lower(),
        showlegend=True
    )

    fig_max.update_layout(
        title=dict(
            font_family="myriad",
            font_size=22
        )
    )
    fig_max.update_yaxes(title_text='', showgrid=True, gridwidth=1)

    fig_min = go.Figure(fig_max)

    fig_max.update_layout(legend=dict(yanchor="top",
                                      y=0.99,
                                      xanchor="left",
                                      x=0.01)
                          )

    return fig_min, fig_max


def get_serie(df_filtrado, dados, dados_state, visual, local, media, range_media=7):
    if (type(local) == list) & (media == [1]) & ("diario" in dados_state):

        fig_max = go.Figure()
        i = 0
        for localidade in local:
            fig_max.add_trace(
                go.Scatter(
                    x=df_filtrado[df_filtrado.localidade == localidade]["date"],
                    y=df_filtrado[df_filtrado.localidade == localidade][get_y(dados, dados_state)].rolling(
                        window=7).mean(),
                    mode='lines',
                    line={'color': px.colors.qualitative.Light24[i]},
                    name=dic_locais[localidade],
                )
            )
            i += 1

        fig_max.update_layout(
            title=dict(
                text=get_title(local[0]) + " - " + label[get_y(dados, dados_state)].lower(),
                font_family="myriad",
                font_size=22
            ),
            legend_title_text="Localidade"
        )

        fig_max.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01)
        )
        fig_min = go.Figure(fig_max)

        return fig_min, fig_max
    else:
        if visual == 0:
            fig_max = px.bar(
                df_filtrado,
                x="date",
                y=get_y(dados, dados_state),
                opacity=0.8,
                color=df_filtrado["localidade"].map(lambda local_: dic_locais[local_]),
                color_discrete_sequence=px.colors.qualitative.Light24,
                labels=label
            )

        else:
            fig_max = px.line(
                df_filtrado,
                x="date",
                y=get_y(dados, dados_state),
                color=df_filtrado["localidade"].map(lambda local_: dic_locais[local_]),
                color_discrete_sequence=px.colors.qualitative.Light24,
                labels=label
            )

        if type(local) == str:
            fig_max.update_layout(
                title=dic_locais[local] + " - " + label[get_y(dados, dados_state)].lower(),
                showlegend=False
            )
        else:
            fig_max.update_layout(
                title=get_title(local[0]) + " - " + label[get_y(dados, dados_state)].lower()
            )
        fig_max.update_layout(
            title=dict(
                font_family="myriad",
                font_size=22
            )
        )
        fig_max.update_yaxes(title_text='', showgrid=True, gridwidth=1)

        if (media == [1]) & ("diario" in dados_state):
            fig_max.add_trace(
                go.Scatter(
                    x=df_filtrado["date"],
                    y=df_filtrado[get_y(dados, dados_state)].rolling(window=range_media).mean(),
                    mode='lines',
                    line={'color': 'black'},
                    name=f'Média móvel ({range_media} dias)'
                )
            )
            fig_max.update_layout(showlegend=True, legend_title_text="Legenda")

        fig_max.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ))

        fig_min = go.Figure(fig_max)

        return fig_min, fig_max


def get_title(local, filtro_reg=0):
    print(f"local: {local}")
    if local in distritos:
        return "Curitiba"
    elif local in NUC:
        print("entrou")
        return "Núcleo Urbano Central"
    else:
        if filtro_reg == 0:
            return "Paraná"
        else:
            return f"Regional {dic_reg[filtro_reg]}"


def get_max(local, filtro_value=0):
    if local in distritos:
        return "Curitiba"
    elif local in NUC:
        return "NUC"
    else:
        if filtro_value == 0:
            return "Paraná"
        else:
            return dic_reg[filtro_value]


def get_y(dados, dados_state):
    if (dados == 0) | (dados == 1):
        if (dados_state is None) | (dados_state == []):
            if dados == 0:
                return "casosAcumulados"
            else:
                return "obitosAcumulados"
        elif dados_state == ['diario']:
            if dados == 0:
                return "casosNovos"
            else:
                return "obitosNovos"
        elif dados_state == ['relativo']:
            if dados == 0:
                return "casos_100k"
            else:
                return "obitos_100k"
        else:
            if dados == 0:
                return "casosNovos_100k"
            else:
                return "obitosNovos_100k"
    elif dados == 2:
        return "CFR"
    else:
        if (dados_state is None) | (dados_state == []):
            if dados == 3:
                return "vacinas_parcialAcumulados"
            else:
                return "vacinas_completasAcumulados"
        elif dados_state == ['diario']:
            if dados == 3:
                return "vacinas_parcialNovas"
            else:
                return "vacinas_completasNovas"
        elif dados_state == ['relativo']:
            if dados == 3:
                return "vacinas_parcialAcumulados_100k"
            else:
                return "vacinas_completasAcumulados_100k"
        else:
            if dados == 3:
                return "vacinas_parcialNovas_100k"
            else:
                return "vacinas_completasNovas_100k"


def get_labels(df_filtrado):
    return df_filtrado['localidade'].map(lambda local_: dic_locais[local_])


filtro_var = 0  # Gambiarra


def filtro_act(filtro_value):
    global filtro_var
    if filtro_value == 0:
        return True
    if filtro_var != filtro_value:
        filtro_var = filtro_value
        return False
    else:
        return True


def get_values(variavel_local, multi_state, value_act, filtro_value=0):
    global multi_global
    changed = False
    if variavel_local == 2:
        if ((value_act in NUC) & (value_act != "Curitiba")) | (value_act[0] in NUC):
            changed = False
        else:
            changed = True
    elif variavel_local == 3:
        if (((value_act in municipios) & (value_act != "Curitiba")) | (value_act[0] in municipios)) & filtro_act(
                filtro_value):
            changed = False
        else:
            changed = True
    elif variavel_local == 4:
        if (value_act in regionais) | (value_act[0] in regionais):
            changed = False
        else:
            changed = True

    if (multi_state != multi_global) | changed:
        values = 0
        if multi_state:
            if variavel_local == 1:
                values = distritos[1:]
            elif variavel_local == 2:
                values = NUC[1:]
            elif variavel_local == 3:
                if filtro_value == 0:
                    values = municipios[0]
                else:
                    filtro = df_def_reg.groupby("regional").get_group(dic_reg[filtro_value])["codigo"].reset_index(
                        drop=True).to_numpy()
                    mun = df_PR[df_PR.codigo.isin(filtro)].sort_values(
                        "localidade").localidade.drop_duplicates().to_numpy()
                    values = mun[0]
            elif variavel_local == 4:
                values = regionais[0]
        else:
            if variavel_local == 1:
                values = distritos[0]
            elif variavel_local == 2:
                values = NUC[0]
            elif variavel_local == 3:
                if filtro_value == 0:
                    values = municipios[0]
                else:
                    filtro = df_def_reg.groupby("regional").get_group(dic_reg[filtro_value])["codigo"].reset_index(
                        drop=True).to_numpy()
                    mun = df_PR[df_PR.codigo.isin(filtro)].sort_values(
                        "localidade").localidade.drop_duplicates().to_numpy()
                    values = mun[0]
            elif variavel_local == 4:
                values = regionais[0]
        multi_global = multi_state
    else:
        values = value_act

    return values


###########################################
######## end funcs
###########################################
######## Layout funcs
###########################################


def button_tooltip(id_):
    return dbc.Button(
        children=[html.I(className="far fa-question-circle")],
        id=f"tooltip-target-{id_}",
        outline=True,
        color="dark",
        style={'border': '0px',
               # "border-radius": "50%",
               "float": "right"}
    )


def make_tooltip(id_, msg="qualquer msg"):
    return dbc.Tooltip(
        msg,
        target=f"tooltip-target-{id_}",
        placement=id_,
    )


def get_exception(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4):
    if ((n1 == n2) & (n1 == n3) & (n1 == n4) & (n1 == 0)) | ((n0 > n1) & (n0 > n2) & (n0 > n3) & (n0 > n4)) | \
            (not compare(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)):
        # Caso o programa seja iniciado ou o btn 'voltar' for clicado
        raise dash.exceptions.PreventUpdate


###########################################
######## end Layout funcs
###########################################

external_stylesheets = [
                        dbc.themes.COSMO,
                        {
                            'href': 'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
                            'rel': 'stylesheet',
                            'integrity': 'sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf',
                            'crossorigin': 'anonymous'
                        }
]

app = dash.Dash(__name__,
                external_stylesheets=external_stylesheets,
                meta_tags=[{'name': "viewpoint",
                            "content": "width=device-width, initial-scale=2., maximum-scale=2., minimum-scale=1,"}]
                )
server = app.server
cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})
app.config.suppress_callback_exceptions = True
TIMEOUT = 3600*12

@cache.memoize(timeout=TIMEOUT)
def fit(local, dados):
    print(local)
    return modelo.fit(dados)


logging.info("O app iniciou...")

logging.info("Reunindo os dados...")
url_covid_cwb = 'https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_distritos_cwb.csv'
url_pop_cwb = 'https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/cwb_variaveis.csv'
url_geo_cwb = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/geojson/distritos_cwb.geojson"
url_cwb_co_idades = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_cwb_idades.csv"
url_cwb_idades = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/idades_distritos_cwb.csv"

url_covid_PR = 'https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_parana.csv'
url_pop_PR = 'https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/PR_variaveis.csv'
url_geo_PR = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/geojson/" \
             "municipios_parana_simplificado.geojson"
url_PR_idades = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/idades_parana.csv"
url_PR_co_idades = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_parana_idades.csv"

url_covid_regionais = 'https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_regionais.csv'
url_regionais = 'https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/definicao_regionais.csv'
url_geo_reg = "https://raw.githubusercontent.com/brunomc3/fits_RMC/main/mapas/regionais/dataRegionais.geojson"
url_def_reg = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/definicao_regionais.csv"
url_reg_idades = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/idades_regionais.csv"
url_reg_co_idades = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_reg_idades.csv"

url_vacinas = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_vacinacao_PR.csv"
url_vacinas_reg = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_vacinacao_regionais.csv"

url_ev_idades = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/dados/df_ev_idades.csv"

df_distritos = pd.read_csv(url_covid_cwb)
df_PR = pd.read_csv(url_covid_PR)
df_reg = pd.read_csv(url_covid_regionais)

df_def_reg = pd.read_csv(url_def_reg)

df_vacina = pd.read_csv(url_vacinas)
df_vacina_reg = pd.read_csv(url_vacinas_reg)

df_idades_co_cwb = pd.read_csv(url_cwb_co_idades)
df_idades_cwb = pd.read_csv(url_cwb_idades)
df_idades_PR = pd.read_csv(url_PR_idades)
df_idades_co_PR = pd.read_csv(url_PR_co_idades)
df_idades_reg = pd.read_csv(url_reg_idades)
df_idades_co_reg = pd.read_csv(url_reg_co_idades)


def dummy_func(x):
    if x != '80+':
        return x
    return 80


def dummy_sort(dff):
    dff['dummy_sort'] = dff.idade.map(lambda idade_: int(dummy_func(idade_.split('-')[0])))
    dff = dff.sort_values(by=["localidade", "sexo", "dummy_sort"]).drop(columns="dummy_sort")
    return dff


df_idades_co_cwb = dummy_sort(df_idades_co_cwb)
df_idades_co_PR = dummy_sort(df_idades_co_PR)
df_idades_co_reg = dummy_sort(df_idades_co_reg)

df_ev_idades = pd.read_csv(url_ev_idades)

logging.info("Reuniu todos os dados.")

logging.info("Reunindo os arquivos .geoJson.")

df_geo_dist = pd.read_csv(url_pop_cwb)
r = requests.get(url_geo_cwb)
c = r.content
json_data_cwb = simplejson.loads(c)

bairro_id_map = {}
for feature in json_data_cwb['features']:
    feature['id'] = feature['properties']['codigo_regional']
    bairro_id_map[feature['properties']['nome_regional']] = feature['properties']['codigo_regional']

r = requests.get(url_geo_PR)
c = r.content
json_data_PR = simplejson.loads(c)

municipio_id_map = {}
for feature in json_data_PR['features']:
    feature['id'] = feature['properties']['CD_MUN']
    municipio_id_map[feature['properties']['NM_MUN']] = feature['properties']['CD_MUN']

NUC_codigo = [
    4100400,
    4101804,
    4104006,
    4104204,
    4104253,
    4105805,
    4106902,
    4107652,
    4111258,
    4119152,
    4119509,
    4120804,
    4122206,
    4125506
]

r = requests.get(url_geo_reg)
c = r.content
json_data_reg = simplejson.loads(c)

reg_id_map = {}
for feature in json_data_reg['features']:
    reg_id_map[feature['id']] = feature['id']
logging.info("Pronto!")

distritos = [
    'Curitiba',
    'DSBN',
    'DSBV',
    'DSBQ',
    'DSCJ',
    'DSCIC',
    'DSMZ',
    'DSPN',
    'DSPR',
    'DSSF',
    'DSTQ'
]

NUC = ["NUC"] + sorted(list(set(df_PR[df_PR["codigo"].isin(NUC_codigo)]["localidade"])))

municipios = list(set(df_PR.localidade))
# municipios.remove('Nuc')
municipios.remove('Paraná')
municipios.sort()
municipios.insert(0, 'Paraná')

regionais = list(set(df_reg.localidade))
regionais.sort()

dic_locais = {
    'Curitiba': 'Curitiba',
    'DSBV': 'Boa vista',
    'DSBQ': 'Boqueirão',
    'DSBN': 'Bairro Novo',
    'DSCIC': 'Cidade Industrial',
    'DSCJ': 'Cajuru',
    'DSMZ': 'Matriz',
    'DSPR': 'Portão',
    'DSPN': 'Pinheirinho',
    'DSSF': 'Santa Felicidade',
    'DSTQ': 'Tatuquara',
    'NUC': 'NUC'
}

for municipio in municipios:
    dic_locais[municipio] = municipio.title()

for regional in regionais:
    dic_locais[regional] = regional

label = {
    "color": "Localidade",
    "date": "Data",
    "casosNovos": "Casos diários",
    "casosAcumulados": "Casos acumulados",
    "localidade": "Localidade",
    "obitosNovos": "Óbitos diários",
    "obitosAcumulados": "Óbitos acumulados",
    "codigo": "Código",
    "casos_100k": "Casos por 100 mil habitantes",
    "casosNovos_100k": "Casos diários por 100 mil habitantes",
    "obitos_100k": "Óbitos por 100 mil habitantes",
    "obitosNovos_100k": "Óbitos diários por 100 mil habitantes",
    "CFR": "Letalidade",
    "vacina_dataaplicacao": "Data",
    "estabelecimento_municipio_codigo": "Código",
    "vacinas_completasNovas": "Vacinações diárias",
    "vacinas_parcialNovas": "Vacinações diárias",
    "vacinas_parcialAcumulados": "Vacinações",
    "vacinas_completasAcumulados": "Vacinações",
    "vacinas_parcialNovas_100k": "Vacinações diárias por 100 mil habitantes",
    "vacinas_completasNovas_100k": "Vacinações diárias por 100 mil habitantes",
    "vacinas_parcialAcumulados_100k": "Vacinações por 100 mil habitantes",
    "vacinas_completasAcumulados_100k": "Vacinações por 100 mil habitantes",
    "idade": "Faixa etária",
    "casosNovos_media": "Casos diários médio (7 dias)",
    "obitosNovos_media": "Óbitos diários médio (7 dias)",
    "casosNovos_100k_media": "Casos diários por 100k hab. médio (7 dias)",
    "obitosNovos_100k_media": "Óbitos diários por 100k hab. médio (7 dias)",
    "vacinas_parcialNovas_media": "Média das primeiras doses aplicadas diárias (7 dias)",
    "vacinas_completasNovas_media": "Média das segundas doses aplicadas diárias (7 dias)",
    "vacinas_parcialNovas_100k_media": "Média das primeiras doses aplicadas diárias por 100k hab. (7 dias)",
    "vacinas_completasNovas_100k_media": "Média das segundas doses aplicadas diárias por 100k hab. (7 dias)",

}

regionais_df = df_def_reg[["regional", "codigo_reg"]].drop_duplicates("regional").reset_index(drop=True)
regionais_df = regionais_df.sort_values(by="codigo_reg")

dic_reg = {}
for reg in regionais_df.to_records():
    dic_reg[reg[2]] = reg[1]

filtro_opt = [{"label": "Todas", "value": 0}]

for key, value, in dic_reg.items():
    filtro_opt.append({"label":value, "value": key})

df_tabela_dist = df_distritos.drop_duplicates("localidade", keep="last")
df_tabela_NUC = df_PR[df_PR.localidade.isin(NUC)].drop_duplicates("localidade", keep="last")
df_tabela_vac_NUC = df_vacina[df_vacina.localidade.isin(NUC)].drop_duplicates("localidade", keep="last")
df_tabela_PR = df_PR[df_PR.localidade != "NUC"].drop_duplicates("localidade", keep="last")
df_tabela_vac_PR = df_vacina[df_vacina.localidade != "NUC"].drop_duplicates("localidade", keep="last")
df_tabela_reg = df_reg.drop_duplicates("localidade", keep="last")
df_tabela_vac_reg = df_vacina_reg.drop_duplicates("localidade", keep="last")

pio.templates.default = "plotly_white"

logging.info("Terminou de processar as tabelas.")

opt_dados1 = [{"label": "Casos", "value": 0},
              {"label": "Óbitos", "value": 1},
              {"label": "Letalidade", "value": 2},
              {"label": "Vacinas 1 dose", "value": 3},
              {"label": "Vacinas 2 dose", "value": 4}]

opt_dados2 = opt_dados1[:3]

logging.info("Começou a rodar o layout.")
# Navbar
modinterv_logo = "https://raw.githubusercontent.com/luancordeiro/modintervPR/main/MODINTERVPR.png"


def get_btn(children, id_, outline=False, color="light", color_font="white", tamanho=1):
    return dbc.Col(
        dbc.Button(
            children,
            id=id_,
            outline=outline,
            size="lg",
            color=color,
            style={"font-family": "Helvetica",
                   "color": color_font}
        ),
        style={"margin-top": "40px", "margin-right": "25px"},
        xs=tamanho, sm=tamanho, md=tamanho, lg=tamanho, xl=tamanho
    )


botoes = dbc.Row(
    [
        dbc.Col(
            dbc.Button(
                "Início",
                id="btn_inicio_",
                color="light",
                style={"font-family": "Helvetica",
                       'background-color': 'white',
                       "color": "black"}
            ),
            width=1),
        dbc.Col(
            dbc.Button("Portal Paraná", id="btn_app", outline=True, color="danger"),
            width=10
        ),
    ],
    align="center",
    style={"width": "100%"}
)
navbar = dbc.Navbar(
    [
        html.A(
            html.Img(src=modinterv_logo, height="45px"),
            href="http://fisica.ufpr.br/redecovid19/index.html",
            style={"margin-right": "50px"}
        ),
        botoes,
    ],
    fixed="top",
    color="white",
    dark=False,
    style={"height": "80px"}
)


def get_garbage(n):
    return html.Div(id=f"garbage-output-{n}")


def style_inicio():
    return {"margin-left": "40px",
            "margin-right": "5%",
            }


def get_column(conteudo, figura, imag, ordem):
    if (imag is None) & (figura is None):
        tamanho = 12
    else:
        tamanho = 5
    col = [
        dbc.Col(
            html.P(
                conteudo,
                style={"font-size": "130%"},
            ),
            xs=12, sm=12, md=12, lg=tamanho, xl=tamanho
        )
    ]

    if not (figura is None):
        col.append(dbc.Col(dcc.Graph(figure=figura), xs=12, sm=12, md=12, lg=7, xl=7))

    if not (imag is None):
        col.append(dbc.Col(imag, xs=12, sm=12, lg=7, xl=7))

    if ordem != 1:
        col.reverse()

    return col


def get_div(titulo="titulo", conteudo="conteudo", figura=None, imag=None, ordem=1, cor="white", bool_hr=True):

    def get_hr(bool):
        if bool:
            return html.Hr()
        return html.Div("")
    div = html.Div(
        [
            get_hr(bool_hr),
            html.H1(
                children=titulo,
                style={"font-size": "250%", "color": "black"}
            ),
            dbc.Row(get_column(conteudo, figura, imag, ordem),
                    justify="between",
                    align="center",
                    # style=style_inicio(),
            )
        ],
        style={"background-color": cor, "margin-left": "40px", "margin-right": "10%"}
    )

    return div


fig1 = px.line(
    df_distritos[df_distritos["localidade"] == "Curitiba"],
    x="date",
    y="obitosNovos",
    labels=label,
    title="Curitiba"
)

t_1 = "Bem-vindo ao Portal Modinterv Paraná Covid-19! A presente plataforma reúne, de forma consolidada, dados sobre " \
      "a pandemia de Covid-19 no estado do Paraná. Ao acessar o Portal Modinterv Paraná (link acima), o usuário " \
      "poderá acompanhar o número de casos confirmados de Covid-19 , o número de óbitos decorrentes da doença e a " \
      "quantidade de pessoas vacinadas por regionais e municípios paranaenses. Também estão disponíveis os números " \
      "de casos e óbitos nos distritos sanitários da cidade de Curitiba."

t_12 = "A plataforma apresenta ainda outras análises complementares, como a distribuição etárias de casos e óbitos, " \
       "além de ajustes matemáticos para as curvas epidêmicas dos municípios paranaenses e distritos sanitários da " \
       "capital, os quais permitem entender melhor o atual estágio da pandemia na localidade escolhida, bem como " \
       "fazer previsões de curto prazo sobre a evolução da mesma. Outras funcionalidades serão implementadas à medida " \
       "que forem sendo desenvolvidas."

t_2 = "Os dados de casos e óbitos mostrados neste Portal são obtidos de forma automática dos bancos de dados da " \
      "Secretaria de Saúde do Parana e da Prefeitura Municipal de Curitiba. Os dados de vacinação são obtidos do " \
      "portal DataSUS do Ministério da Saúde. Os links para as respectivas fontes dos dados podem ser encontradas " \
      "na página GitHub: https://github.com/luancordeiro/modintervPR."

t_3 = "O Portal Modinterv Paraná também implementa um modelo matemático que permite entender a evolução temporal de " \
      "uma dada curva epidêmica, seja de casos ou óbitos, e seus sucessivos estágios de crescimento. Em particular, " \
      "o modelo descreve o comportamento de dados com múltiplas ondas epidêmicas, como observados em muitos  estados " \
      "e cidades do Brasil, incluindo o Paraná e seus maiores municípios. A partir do modelo, pode-se fazer " \
      "projeções de curto prazo sobre a evolução da epidemia em uma determinada localidade. \n" \
      "A matemática do modelo está descrita em um artigo científico do nosso grupo; vide referência 3 na seção de " \
      "Publicações (abaixo)."

t_41 = '''1. G. L. Vasconcelos, A. M. S. Macêdo, R. Ospina, F. A. G. Almeida, G. C. Duarte-Filho, A. A. Brum, I. C. L. Souza, “Modelling fatality curves of COVID-19 and the effectiveness of intervention strategies”, PeerJ 8:e9421 (2020), https://doi.org/10.7717/peerj.9421 '''

t_42 = '''2. G. L. Vasconcelos, A. M. S. Macêdo, G. C. Duarte-Filho, A. A. Brum, R. Ospina, F. A. G. Almeida, “Power law behaviour in the saturation regime of fatality curves of the COVID-19 pandemic”, Scientific Reports 11, 4619 (2021). https://www.nature.com/articles/s41598-021-84165-1'''

t_43 = '''3. G. L. Vasconcelos, A. A. Brum, F. A. G. Almeida, A. M. S. Macêdo, G. C. Duarte-Filho, R. Ospina,“Standard and anomalous waves of COVID-19: A multiple-wave growth model for epidemics, ” submitted to Brazilian Journal of Physics. Uma versão em forma de pré-publicação está disponível aqui https://www.medrxiv.org/content/10.1101/2021.01.31.21250867v4. '''

t_44 = '''Para maiores informações sobre as atividades de pesquisa do nosso grupo, vide seção abaixo.'''

t_5 = "O Portal Modinterv Paraná Covid-19 foi desenvolvido por pesquisadores da Rede Cooperativa de Pesquisa em " \
      "Modelagem da Epidemia de Covid-19 e Intervenções não Farmacológicas (Modinterv), que reúne pesquisadores " \
      "das universidades federais do Paraná (UFPR), Pernambuco (UFPE) e Sergipe (UFS). Maiores informações sobre " \
      "os artigos, notas técnicas e atividades de divulgação científica da Rede Modinterv podem ser encontradas na " \
      "nossa página http://fisica.ufpr.br/redecovid19. " \
      "A presente versão do Portal Modinterv Paraná foi desenvolvida pelos bolsistas de iniciação científica " \
      "Luan de Paula Cordeiro e Bruno Mantovani Czajkowski, sob supervisão do Prof. Giovani Lopes Vasconcelos, " \
      "todos do Departamento de Física da UFPR."

imag_apresentacao = "https://user-images.githubusercontent.com/66036012/85095333-72272e00-b1c7-11ea-8c85-8f251fea910a.jpg"
fig = html.Img(src=imag_apresentacao, style={"width": "90%"})

div_inicio = html.Div(
    [
        get_garbage(0),
        html.Div("", style={"height": "65px"}),
        get_div(titulo="Apresentação", conteudo=t_1, imag=fig, ordem=1),
    ],
    id="inicio_div"
)

div_dados = html.Div(
    [
        get_garbage(1),
        html.Div("", style={"height": "65px"}),
        get_div(titulo="Dados", conteudo=t_2)
    ],
    id="dados_div"
)

div_modelo = html.Div(
    [
        get_garbage(2),
        html.Div("", style={"height": "65px"}),
        get_div(titulo="Modelo", conteudo=t_3)
    ],
    id="modelo_div"
)

div_publi = html.Div(
    [
        get_garbage(3),
        html.Div("", style={"height": "65px"}),
        get_div(titulo="Publicações", conteudo=t_41)
    ],
    id="publi_div"
)

div_equipe = html.Div(
    [
        get_garbage(4),
        html.Div("", style={"height": "65px"}),
        get_div(titulo="Equipe", conteudo=t_5)
    ],
    id="equipe_div"
)

# App
card_botoes = dbc.CardBody(
    dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    "Curitiba",
                    id="cwb_button",
                    outline=True,
                    size="lg",
                    color="danger",
                    style={'border': '0px'}
                ),
                width='auto'
            ),
            dbc.Col(
                dbc.Button(
                    "Núcleo Urbano Central",
                    id="nuc_button",
                    outline=True,
                    size="lg",
                    color="danger",
                    style={'border': '0px'}
                ),
                width='auto'
            ),
            dbc.Col(
                dbc.Button(
                    "Regionais PR",
                    id="reg_button",
                    outline=True,
                    size="lg",
                    color="danger",
                    style={'border': '0px'}
                ),
                width='auto'
            ),
            dbc.Col(
                dbc.Button(
                    "Municípios PR",
                    id="pr_button",
                    outline=True,
                    size="lg",
                    color="danger",
                    style={'border': '0px'}
                ),
                width='auto'
            )
        ]
    )
)

row_capa = html.Div(
    [
        html.Hr(),
        html.Div(
            [
                html.H1(
                    "Escolha uma Região",
                    style={"font-size": "250%", "color": "black"}
                ),
                card_botoes
            ],
            style={"margin-left": "250px", "margin-right": "250px", "margin-top": "100px"}
        )
    ],
    id="capa",
)


def get_section_title(titulo, id_, dica_texto):
    return dbc.Row([dbc.Col(html.P(titulo)), dbc.Col(button_tooltip(id_)), make_tooltip(id_, dica_texto)],
                   justify="between")


painel_controle = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Button(children=[html.I(className="fas fa-arrow-left")],
                           id='voltar_localidade',
                           outline=True,
                           color="danger",
                           style={'border': '0px', "border-radius": "50%"}),
                html.Hr(),
                dbc.Button(children=[html.I(className="fas fa-bars")],
                           id="hidden_painel",
                           outline=True,
                           color="dark",
                           style={"justify": "right", "border-radius": "50%",'border': '0px'}),
                html.Div(
                    [
                        get_section_title(titulo="Localidade", id_="locais", dica_texto="Altere ou adicione localidades"),

                        html.Div(
                            id="div_filtro",
                            children=dbc.Row(
                                [
                                    dbc.Col(html.P("Filtro por regional:"),
                                            md=4,
                                            align="center",
                                            style={"font-size": "13px"}),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="filtro",
                                            value=0,
                                            clearable=False,
                                            options=filtro_opt
                                        ),
                                        md=8
                                    )
                                ],
                                no_gutters=True,
                            )
                        ),
                        dcc.Dropdown(
                            id="drop_local",
                            value="Curitiba",
                            clearable=False,
                            multi=False,
                            options=get_options(1)
                        ),
                        dbc.Checklist(
                            id="multi_state",
                            options=[{"label": "Multi", "value": 1}],
                        ),

                        html.Hr(),
                        get_section_title(titulo="Dados", id_="dados_id", dica_texto="Escolha uma variável"),
                        dcc.Dropdown(
                            id="drop_dados",
                            value=1,
                            clearable=False,
                            options=opt_dados1
                        ),
                        dbc.Checklist(
                            id="dados_state",
                            value=[],
                            options=[
                                {"label": "Dados diários", "value": "diario"},
                                {"label": "Por 100 mil habitantes", "value": "relativo"}
                            ]
                        ),
                        dbc.Checklist(
                            id="media",
                            options=[{"label": "Média móvel", "value": 1}]
                        ),
                        dcc.Slider(
                            id='media_slider',
                            min=7,
                            max=30,
                            step=1,
                            value=7,
                            marks={
                                7: {'label': "7"},
                                15: {'label': "15"},
                                30: {'label': "30"}
                            }
                        ),
                        html.Hr(),

                        get_section_title(titulo="Modelo", id_="modelo_id", dica_texto="Algo sobre o modelo"),
                        dbc.Checklist(
                            id="fit_state",
                            options=[{"label": "Fit", "value": 1}]
                        ),
                        dcc.Slider(
                            id='fit_slider',
                            min=-30,
                            max=30,
                            step=1,
                            value=0,
                            marks={
                                -30: {'label': '-30'},
                                0: {'label': "0"},
                                30: {'label': "30"}
                            }
                        ),
                        html.Hr(),

                        get_section_title(titulo="Visualização",
                                          id_="visual_id",
                                          dica_texto="Altere a visualização das séries temporais."),
                        dcc.Dropdown(
                            id="visualizacao_state",
                            value=1,
                            clearable=False,
                            options=[
                                {"label": "Barra", "value": 0},
                                {"label": "Linha", "value": 1}
                            ]
                        ),
                        html.Div(children=[""], style={"height": "100px", "background-color": "white"})
                    ],
                    id="div_controles"
                )
            ],
        )
    ],
    style={"height": "100vh", "maxHeight": "90vh", "overflow": "scroll"}
)


def card_geral_graph(id_):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(dcc.Loading(
                    type="default",
                    children=dcc.Graph(id=id_),
                )
            ),
            style={"margin-top": "10px", "margin-left": "10px", "padding": "10px"},
        ),
        xs=12, sm=12, md=12, lg=6, xl=6,
    )

graficos_card = dbc.Card(
    dbc.Row(
        [
            dbc.Col(
                dbc.Row(
                    [
                        card_geral_graph("grafico_serie1"),
                        card_geral_graph("grafico_demo1"),
                        card_geral_graph("grafico_geo1"),
                        card_geral_graph("ev_demo"),
                    ],
                    no_gutters=True,
                ),
                xs=12, sm=12, md=12, lg=12, xl=12,
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dash_table.DataTable(
                            id='table_min',
                            style_data={"font-family": "Helvetica"},
                            style_header={"font-family": "Helvetica"},
                            style_cell={'textAlign': 'left'},
                        ),
                        style={"maxHeight": "100vh", "margin-left": "10px", "overflow": "scroll"}
                    ),
                ],
                xs=12, sm=12, md=12, lg=12, xl=12,
                style={"margin-top": "10px"})
        ],
        no_gutters=True,
    ),
)

# serie_card = dbc.Card(dcc.Graph(id="grafico_serie2"))

style_series = {"width": "1100px", "margin-top": "10px", "margin-left": "10px"}

serie_card = dbc.Card(
    dbc.Row(
        [
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico_serie2")), style=style_series)),
            dbc.Col(html.Div(dbc.Card(
                dbc.CardBody(
                    dcc.Graph(id="grafico_serie_idades")
                ),
                style=style_series),
                id="div_serie_idade")
            )
        ],
        justify="center",
        no_gutters=True
    )
)

geo_card = dbc.Card(dbc.CardBody(dcc.Graph(id="grafico_geo2")), style=style_series)

style_demo = {"width": "550px", "margin-top": "10px", "margin-left": "10px"}
demo_card = dbc.Card(
    dbc.Row(
        [
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico_demo2")), style=style_demo),
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico_pop")), style=style_demo),
                    xs=12,
                    sm=12,
                    md=12,
                    lg=6,
                    xl=6,)
        ],
        no_gutters=True,
    )
)
tabela_card = dbc.Card(
    dash_table.DataTable(
        id='table_tot',
        style_data={"font-family": "Helvetica"},
        style_header={"font-family": "Helvetica"},
        sort_action='custom',
        sort_mode='single',
        sort_by=[]
    ),
    style={"max-width": "100%", "maxHeight": "87vh", "overflow": "scroll"}
)


def get_tab(children, label_, id_):
    return dbc.Tab(children, label=label_, tab_id=id_, label_style={"color": "#00000f"})


tabs_graficos = html.Div(
    dbc.Tabs(
        [
            get_tab(graficos_card, "Geral", "tab-geral"),
            get_tab(serie_card, "Série temporal", "tab-serie"),
            get_tab(geo_card, "Geográfico", "tab-geo"),
            get_tab(demo_card, "Dados demográficos", "tab-demo"),
            get_tab(tabela_card, "Tabela", "tab-tabela")
        ],
        id="tabs",
        style={"margin-left": "2%", "background-color": "#f8f8f8"}
    )
)


row_localidades = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    painel_controle,
                    id="test1",
                    style={"position": "fixed", "top": "80px", "z-index": "999"},
                    xs=5, sm=5, md=5, lg=2, xl=2
                ),
                dbc.Col(
                    tabs_graficos,
                    id="test2",
                    style={"background-color": "#f8f8f8", "margin-left": "16.5%"},
                    xs=7, sm=7, md=7, lg=10, xl=10
                )
            ],
            no_gutters=True,
            # justify="left",
            style={"background-color": "#f8f8f8"}
        )
    ],
    id="localidades",
    hidden=True,
    style={"width": "100%", "margin-top": "80px"}
)

div_app = html.Div(
    [
        row_capa,
        row_localidades
    ],
    id="app_div",
    hidden=True
)


div_side_bar = html.Div(
    children=[
        get_btn("Apresentação", color="dark", id_="btn_inicio"),
        get_btn("Dados", color="dark", id_="btn_dados"),
        get_btn("Modelo", color="dark", id_="btn_modelo"),
        get_btn("Publicações", color="dark", id_="btn_publi"),
        get_btn("Equipe", color="dark", id_="btn_equipe")
    ],
    style={"background-color": "#343c3c", "margin-top": "60px", "position": "fixed", "height": "100%"}
)


def divisoria():
    return html.Div(style={"height": "15vh"})

div_apresentacao = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(div_side_bar, xs=4, sm=4, md=4, lg=2, xl=2),
                dbc.Col(
                    [
                        div_inicio,
                        html.Div(get_div(titulo="", conteudo=t_12, bool_hr=False), style={"margin-right": "57%"}),
                        divisoria(),
                        div_dados,
                        divisoria(),
                        div_modelo,
                        divisoria(),
                        div_publi,
                        get_div(titulo="", conteudo=t_42, bool_hr=False),
                        get_div(titulo="", conteudo=t_43, bool_hr=False),
                        get_div(titulo="", conteudo=t_44, bool_hr=False),
                        divisoria(),
                        div_equipe
                    ],
                    xs=8, sm=8, md=8, lg=10, xl=10,
                )
            ],
            no_gutters=True,
        )
    ],
    id="apresentacao_div",
)


app.layout = html.Div(
    [
        navbar,
        div_apresentacao,
        div_app,
    ],
)


@app.callback(
    Output("capa", "hidden"),
    Output("localidades", "hidden"),
    Output("drop_local", "options"),
    Output("drop_local", "value"),
    Output("drop_local", "multi"),
    Output("multi_state", "value"),
    Output("drop_dados", "value"),
    Output("drop_dados", "options"),
    Output("dados_state", "value"),
    Output("fit_state", "value"),
    Output("visualizacao_state", "value"),
    Output("tabs", "active_tab"),
    Output("fit_slider", "value"),
    Output("media", "value"),
    Output("div_filtro", "hidden"),
    Output("filtro", "value"),
    Input("voltar_localidade", "n_clicks_timestamp"),
    Input("cwb_button", "n_clicks_timestamp"),
    Input("nuc_button", "n_clicks_timestamp"),
    Input("pr_button", "n_clicks_timestamp"),
    Input("reg_button", "n_clicks_timestamp"),
    Input("btn_inicio", "n_clicks_timestamp"),
    Input("btn_app", "n_clicks_timestamp"),
    Input("btn_dados", "n_clicks_timestamp"),
    Input("btn_publi", "n_clicks_timestamp"),
    Input("multi_state", "value"),
    Input("filtro", "value"),
    State("drop_local", "value"),
    State("drop_dados", "value"),
    State("dados_state", "value"),
    State("visualizacao_state", "value"),
    State("fit_state", "value"),
    State("tabs", "active_tab"),
    State("fit_slider", "value"),
    State("media", "value"))
def on_button_click(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4, multi_state, filtro_value, drop_local, drop_dados,
                    dados_state, visualizacao_state, fit_state, active_tab, delta_tempo, media):
    logging.info("Atualizou a página.")

    multi = multi_state
    multi_state = (multi_state == [0, 1])
    n0, n1, n2, n3, n4 = [eh_none(n0), eh_none(n1), eh_none(n2), eh_none(n3), eh_none(n4)]
    nav1, nav2, nav3, nav4 = [eh_none(nav1), eh_none(nav2), eh_none(nav3), eh_none(nav4)]

    if (((n1 > n0) | (n2 > n0) | (n3 > n0) | (n4 > n0)) & (sum([n1, n2, n3, n4]) != 0)) & (
            compare(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)):
        # se uma localidade for escolhida, se o programa não acabou de ser iniciado, se nenhum btn da navbar for clicado
        if (n1 > n2) & (n1 > n3) & (n1 > n4):
            if (((drop_local == "Curitiba") & (multi_state == multi_global)) | ((drop_local == distritos[1:]) & (multi_state != multi_global))) & (active_tab != "tab-demo"):
                opt_dados = opt_dados1
            else:
                opt_dados = opt_dados2

            return True, False, get_options(1), get_values(1, multi_state,
                                                           drop_local), multi_state, multi, drop_dados, opt_dados, \
                   dados_state, fit_state, visualizacao_state, active_tab, delta_tempo, media, True, 0
        elif (n2 > n1) & (n2 > n3) & (n2 > n4):
            return True, False, get_options(2), get_values(2, multi_state,
                                                           drop_local), multi_state, multi, drop_dados, opt_dados1, \
                   dados_state, fit_state, visualizacao_state, active_tab, delta_tempo, media, True, 0
        elif (n3 > n1) & (n3 > n2) & (n3 > n4):
            return True, False, get_options(3, filtro_value), get_values(3,
                                                                         multi_state,
                                                                         drop_local,
                                                                         filtro_value), multi_state, multi, \
                   drop_dados, opt_dados1, dados_state, fit_state, visualizacao_state, active_tab, delta_tempo, media, \
                   False, filtro_value
        else:
            return True, False, get_options(4), get_values(4, multi_state,
                                                           drop_local), multi_state, multi, drop_dados, opt_dados1, \
                   dados_state, fit_state, visualizacao_state, active_tab, delta_tempo, media, True, 0
    else:
        # se o botão voltar for apertado ou algum botão da barra de navegação
        return False, True, get_options(1), "Curitiba", False, [0], 1, opt_dados2, [], [], 1, "tab-geral", 0, [], True, 0


@app.callback(
    Output("apresentacao_div", "hidden"),
    Output("app_div", "hidden"),
    [Input("btn_inicio_", "n_clicks_timestamp"),
     Input("btn_app", "n_clicks_timestamp")]
)
def get_div_(n1, n4):
    logging.info("Mudou a div.")
    n1, n4 = [eh_none(n1), eh_none(n4)]

    if n1 >= n4:
        return False, True
    elif n4 > n1:
        return True, False


@app.callback(
    Output("grafico_serie1", "figure"),
    Output("grafico_serie2", "figure"),
    [Input("voltar_localidade", "n_clicks_timestamp"),
     Input("cwb_button", "n_clicks_timestamp"),
     Input("nuc_button", "n_clicks_timestamp"),
     Input("pr_button", "n_clicks_timestamp"),
     Input("reg_button", "n_clicks_timestamp"),
     Input("drop_local", "value"),
     Input("drop_dados", "value"),
     Input("dados_state", "value"),
     Input("fit_state", "value"),
     Input("visualizacao_state", "value"),
     Input("btn_inicio", "n_clicks_timestamp"),
     Input("btn_app", "n_clicks_timestamp"),
     Input("btn_dados", "n_clicks_timestamp"),
     Input("btn_publi", "n_clicks_timestamp"),
     Input("media", "value"),
     Input("fit_slider", "value"),
     Input("media_slider", "value")]
)
def update_graph(n0, n1, n2, n3, n4, local, dados, dados_state, fit_state, visual, nav1, nav2, nav3, nav4, media,
                 delta_tempo, range_media):
    n0, n1, n2, n3, n4 = [eh_none(n0), eh_none(n1), eh_none(n2), eh_none(n3), eh_none(n4)]
    nav1, nav2, nav3, nav4 = [eh_none(nav1), eh_none(nav2), eh_none(nav3), eh_none(nav4)]

    print(f"n0: {n0}")
    print(f"n1: {n1}")
    print(f"n2: {n2}")
    print(f"n3: {n3}")
    print(f"n4: {n4}")

    if ((n1 == n2) & (n1 == n3) & (n1 == n4) & (n1 == 0)) | (not compare(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)):
        raise dash.exceptions.PreventUpdate

    logging.info(
        f"A série temporal começou a ser atualizado. "
        f"Local escolhido: {local}. Dados: {dados}. Estado dos dados: {dados_state}")

    # A func 'compare' retorna False caso nenhum botão da div tenha sido clicado
    # Dados
    if ((n2 > n0) | (n3 > n0)) & ((n2 > n1) | (n3 > n1)) & ((n2 > n4) | (n3 > n4)):
        # Caso o PR ou a NUC seja escolhida
        if (dados == 3) | (dados == 4):
            df_filtrado = df_vacina.query('localidade in @local').reset_index(drop=True)
        else:
            df_filtrado = df_PR.query('localidade in @local').reset_index(drop=True)
    elif (n4 > n0) & (n4 > n1) & (n4 > n2) & (n4 > n3):
        # regionais PR
        if (dados == 3) | (dados == 4):
            df_filtrado = df_vacina_reg.query('localidade in @local').reset_index(drop=True)
        else:
            df_filtrado = df_reg.query('localidade in @local').reset_index(drop=True)
    elif (n1 > n0) & (n1 > n2) & (n1 > n3) & (n1 > n4):
        # distritos
        if (dados == 3) | (dados == 4):
            local = "Curitiba"
            df_filtrado = df_vacina.query('localidade in @local').reset_index(drop=True)
        else:
            df_filtrado = df_distritos.query('localidade in @local').reset_index(drop=True)
    else:
        raise dash.exceptions.PreventUpdate

    if (dados == 1) | (dados == 2):
        df_filtrado = df_filtrado[df_filtrado.obitosAcumulados >= 1]
    elif dados == 3:
        df_filtrado = df_filtrado[df_filtrado['vacinas_parcialAcumulados'] >= 1]
    elif dados == 4:
        df_filtrado = df_filtrado[df_filtrado['vacinas_completasAcumulados'] >= 1]

    # series
    if fit_state == [1]:
        fig_min, fig_max = get_serie_model(df_filtrado, dados, dados_state, local, delta_tempo)
    else:
        fig_min, fig_max = get_serie(df_filtrado, dados, dados_state, visual, local, media, range_media)

    logging.info("Terminou de processar a série temporal")

    return fig_min, fig_max


def get_media(dff_, variavel):
    dff_ = dff_[pd.to_datetime(dff_.date) >= pd.to_datetime(dff_.date.max()) - datetime.timedelta(14)]
    dff_[variavel + '_media'] = dff_.sort_values(by=["localidade", "date"])[variavel].rolling(window=7).mean()

    return dff_.drop_duplicates("localidade", keep="last")[["localidade", "date", variavel + '_media']]




@app.callback(
    Output("grafico_geo1", "figure"),
    Output("grafico_geo2", "figure"),
    Input("voltar_localidade", "n_clicks_timestamp"),
    Input("cwb_button", "n_clicks_timestamp"),
    Input("nuc_button", "n_clicks_timestamp"),
    Input("pr_button", "n_clicks_timestamp"),
    Input("reg_button", "n_clicks_timestamp"),
    Input("drop_dados", "value"),
    Input("dados_state", "value"),
    Input("btn_inicio", "n_clicks_timestamp"),
    Input("btn_app", "n_clicks_timestamp"),
    Input("btn_dados", "n_clicks_timestamp"),
    Input("btn_publi", "n_clicks_timestamp"),
    Input("multi_state", "value"),
    Input("filtro", "value"),
    State("tabs", "active_tab"),
    State("drop_local", "value"),
)
def update_geo_graph(n0, n1, n2, n3, n4, dados, dados_state, nav1, nav2, nav3, nav4, multi, filtro_reg, act_tab, local):
    n0, n1, n2, n3, n4 = [eh_none(n0), eh_none(n1), eh_none(n2), eh_none(n3), eh_none(n4)]
    nav1, nav2, nav3, nav4 = [eh_none(nav1), eh_none(nav2), eh_none(nav3), eh_none(nav4)]
    global multi_global2

    get_exception(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)

    if not (act_tab in ["tab-geral", "tab-geo"]):
        raise dash.exceptions.PreventUpdate

    # Gambiarra \/

    multi = (multi == [0, 1])
    if multi != multi_global2:
        multi_global2 = multi
        raise dash.exceptions.PreventUpdate

    logging.info("O gráfico geográfico começou a ser atualizado")

    variavel = get_y(dados, dados_state)
    lista_get_media = ["casosNovos",
                       "obitosNovos",
                       "casosNovos_100k",
                       "obitosNovos_100k",
                       "vacinas_parcialNovas",
                       "vacinas_completasNovas",
                       "vacinas_parcialNovas_100k",
                       "vacinas_completasNovas_100k"]

    get = False
    if variavel in lista_get_media:
        get = True

    if (n1 >= n2) & (n1 >= n3) & (n1 >= n4):
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_PR.copy()
        else:
            dff_ = df_tabela_dist.copy()
            dff_ = dff_[dff_["localidade"] != "Curitiba"]
        if get:
            if variavel in lista_get_media[4:]:
                raise dash.exceptions.PreventUpdate

            df = df_distritos.copy()
            dff_ = pd.merge(dff_, get_media(df, variavel), how="left", on=["localidade", "date"])
            variavel = variavel + '_media'

        dff_["id"] = dff_['localidade'].map(lambda local_: bairro_id_map[local_])
        dff_["localidade"] = dff_["localidade"].map(lambda local_: dic_locais[local_])
        json_data = json_data_cwb
        location = 'id'
        hover = ["localidade"]
    elif (n2 > n1) & (n2 > n3) & (n2 > n4):
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_NUC.copy()
        else:
            dff_ = df_tabela_NUC.copy()
        if get:
            df = df_PR[df_PR.localidade.isin(NUC)]
            dff_ = pd.merge(dff_, get_media(df, variavel), how="left", on=["localidade", "date"])
            variavel = variavel + '_media'

        dff_ = dff_.rename(columns={"codigo": "CD_MUN"})
        dff_ = dff_[dff_["CD_MUN"] != 0]
        dff_['CD_MUN'] = dff_['CD_MUN'].astype(str)
        json_data = json_data_PR
        location = 'CD_MUN'
        hover = ["localidade"]
    elif (n3 > n1) & (n3 > n2) & (n3 > n4):
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_PR.copy()
        else:
            dff_ = df_tabela_PR.copy()
        if get:
            df = df_PR[df_PR.localidade != "NUC"]
            dff_ = pd.merge(dff_, get_media(df, variavel), how="left", on=["localidade", "date"])
            variavel = variavel + '_media'

        dff_ = dff_[dff_.localidade != "Paraná"]
        if filtro_reg != 0:
            filtro = df_def_reg.groupby("regional"). \
                get_group(dic_reg[filtro_reg])["codigo"].reset_index(drop=True).to_numpy()
            dff_ = dff_[dff_.codigo.isin(filtro)]

        dff_ = dff_.rename(columns={"codigo": "CD_MUN"})
        dff_['CD_MUN'] = dff_['CD_MUN'].astype(str)

        json_data = json_data_PR
        location = 'CD_MUN'
        hover = ["localidade"]
    else:
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_reg.copy()
        else:
            dff_ = df_tabela_reg.copy()
        if get:
            df = df_reg.copy()
            dff_ = pd.merge(dff_, get_media(df, variavel), how="left", on=["localidade", "date"])
            variavel = variavel + '_media'

        dff_ = dff_.rename(columns={'localidade': 'id'})
        json_data = json_data_reg
        location = 'id'
        hover = ["id"]

    data_ = str(dff_.date.max())

    graph_max = px.choropleth(
        dff_,
        locations=location,
        geojson=json_data,
        color=variavel,
        color_continuous_scale=px.colors.sequential.RdBu[::-1],
        hover_data=hover,
        labels=label,
    )
    graph_max.update_layout(title_text=f"{get_title(local, filtro_reg)} - {label[variavel]}<br>Data de referência: {data_}",
                            title_font_size=20,
                            title_font_family="myriad",
                            coloraxis_colorbar=dict(title=""),
                            geo=dict(
                                fitbounds="locations",
                                visible=False),
                            dragmode=False
                            )

    graph_min = go.Figure(graph_max)

    graph_min.update_layout(coloraxis_showscale=False)

    logging.info("O gráfico geográfico terminou de ser atualizado.")
    return graph_min, graph_max


@app.callback(
    Output("grafico_demo1", "figure"),
    Output("grafico_demo2", "figure"),
    [Input("voltar_localidade", "n_clicks_timestamp"),
     Input("cwb_button", "n_clicks_timestamp"),
     Input("nuc_button", "n_clicks_timestamp"),
     Input("pr_button", "n_clicks_timestamp"),
     Input("reg_button", "n_clicks_timestamp"),
     Input("drop_local", "value"),
     Input("drop_dados", "value"),
     Input("btn_inicio", "n_clicks_timestamp"),
     Input("btn_app", "n_clicks_timestamp"),
     Input("btn_dados", "n_clicks_timestamp"),
     Input("btn_publi", "n_clicks_timestamp"),],
    State("filtro", "value")
)
def update_demo1(n0, n1, n2, n3, n4, local, dados, nav1, nav2, nav3, nav4, filtro_value):
    n0, n1, n2, n3, n4 = [eh_none(n0), eh_none(n1), eh_none(n2), eh_none(n3), eh_none(n4)]
    nav1, nav2, nav3, nav4 = [eh_none(nav1), eh_none(nav2), eh_none(nav3), eh_none(nav4)]

    get_exception(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)

    pr_filtro_bool = True
    if type(local) == list:
        print(local)
        local = get_max(local[1], filtro_value)
        pr_filtro_bool = False

    reg_bool = False
    if (n1 >= n2) & (n1 >= n3) & (n1 >= n4): # Curitiba
        dff_ = df_idades_co_cwb.copy()
    elif (n2 > n1) & (n2 > n3) & (n2 > n4): # NUC
        dff_ = df_idades_co_PR.copy()
    elif ((n3 > n1) & (n3 > n2) & (n3 > n4)) & pr_filtro_bool: # PR
        dff_ = df_idades_co_PR.copy()
    else: # REGIONAIS
        reg_bool = True
        dff_ = df_idades_co_reg.copy()

    dic_dados = {
        0: "casosAcumulados",
        1: "obitosAcumulados",
        2: "obitosAcumulados",
        3: "obitosAcumulados",
        4: "obitosAcumulados",
    }

    fig = get_piramide_covid(dff_, local, dic_dados[dados], not pr_filtro_bool, filtro_value, reg_bool)

    return fig, fig


def get_piramide_covid(dff_, local, variavel, filtro_bool=False, filtro_value=0, reg_bool=False):
    var_m = dff_[(dff_.localidade == local) & (dff_.sexo == "m")][variavel]
    var_f = dff_[(dff_.localidade == local) & (dff_.sexo == "f")][variavel]

    idades = dff_[(dff_.localidade == local) & (dff_.sexo == "m")].idade

    fig = go.Figure()

    fig.add_trace(go.Bar(y=idades,
                         x=-var_m,
                         name='Homens',
                         orientation='h',
                         showlegend=True)
                  )

    fig.add_trace(go.Bar(y=idades,
                         x=var_f,
                         name='Mulheres',
                         orientation='h')
                  )

    # xmax = int(np.ceil(max(var_m.max(), var_f.max())))
    # xmax = int(xmax // 20) * 20
    # tickvals = np.ceil(np.linspace(-xmax, xmax, 11))
    # ticktext = abs(tickvals)

    xmax = int(np.ceil(max(var_m.max(), var_f.max()) + 1))
    tickvals = np.array(range(-xmax, xmax + 1, 2))
    ticktext = abs(tickvals)

    if filtro_bool & (local != "Curitiba"):
        if type(local) == list:
            title = get_title(local[0], filtro_value)
        else:
            title = get_title(local, filtro_value)
    else:
        title = dic_locais[local]

    if reg_bool & (not filtro_bool):
        title = "Regional " + title

    fig.update_layout(title=title,
                      autosize=True,
                      # width=500,
                      title_font_size=22,
                      title_font_family="myriad",
                      barmode='relative',
                      bargap=0.0,
                      bargroupgap=0,
                      xaxis=dict(title=label[variavel],
                                 title_font_size=14,
                                 tickvals=tickvals,
                                 ticktext=ticktext
                                 ),
                      yaxis=dict(title='Faixa etária', title_font_size=14))

    return fig


def mediana_(soma):
    cumsum = soma.cumsum()
    for i in range(len(cumsum)):
        if cumsum[i] < 50 and cumsum[i + 1] > 50:
            if abs(cumsum[i] - 50) > abs(cumsum[i + 1] - 50):
                return (cumsum[i + 1], cumsum.index[i + 1], i + 1)
            else:
                return (cumsum[i], cumsum.index[i], i)


def plotPiramide(df, localidade, reg_bool=False):
    df = df.set_index("idade")
    name = localidade

    lista = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39',
             '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79',
             '80+']

    homens = df.query("sexo=='m'")['perc'].reindex(lista)
    mulheres = df.query("sexo=='f'")['perc'].reindex(lista)
    idades = homens.index

    fig = go.Figure()

    fig.add_trace(go.Bar(y=idades,
                         x=-homens,
                         name='Homens',
                         orientation='h',
                         showlegend=True))

    fig.add_trace(go.Bar(y=idades,
                         x=mulheres,
                         name='Mulheres',
                         orientation='h'))

    soma = homens + mulheres
    mediana = mediana_(soma)

    xtexto = max(mulheres)
    texto = format(mediana[0], '.2f') + '%'

    fig.add_annotation(x=xtexto,
                       y=mediana[2] + 0.5,
                       text=texto,
                       showarrow=False,
                       align="center",
                       yshift=10,
                       xanchor='left', )

    fig.add_shape(type='line',
                  x0=0,
                  x1=1,
                  y0=mediana[2] + 0.5,
                  y1=mediana[2] + 0.5,
                  xref="paper",
                  line=dict(color='black', dash='dash'),
                  name='mediana')

    xmax = int(np.ceil(max(homens.max(), mulheres.max()) + 1))
    tickvals = np.array(range(-xmax, xmax + 1, 1))
    ticktext = abs(tickvals)

    title = dic_locais[name]

    if reg_bool:
        title = "Regional " + title

    fig.update_layout(title=title,
                      title_font_size=22,
                      title_font_family="myriad",
                      autosize=True,
                      # width=500,
                      barmode='relative',
                      bargap=0.0,
                      bargroupgap=0,
                      xaxis=dict(title='Porcentagem da população',
                                 title_font_size=14,
                                 tickvals=tickvals,
                                 ticktext=ticktext),
                      yaxis=dict(title='Faixa etária', title_font_size=14))
    return fig


@app.callback(
    Output("grafico_pop", "figure"),
    [Input("voltar_localidade", "n_clicks_timestamp"),
     Input("cwb_button", "n_clicks_timestamp"),
     Input("nuc_button", "n_clicks_timestamp"),
     Input("pr_button", "n_clicks_timestamp"),
     Input("reg_button", "n_clicks_timestamp"),
     Input("drop_local", "value"),
     Input("btn_inicio", "n_clicks_timestamp"),
     Input("btn_app", "n_clicks_timestamp"),
     Input("btn_dados", "n_clicks_timestamp"),
     Input("btn_publi", "n_clicks_timestamp")],
    State("filtro", "value")
)
def update_demo2(n0, n1, n2, n3, n4, local, nav1, nav2, nav3, nav4, filtro_value):
    n0, n1, n2, n3, n4 = [eh_none(n0), eh_none(n1), eh_none(n2), eh_none(n3), eh_none(n4)]
    nav1, nav2, nav3, nav4 = [eh_none(nav1), eh_none(nav2), eh_none(nav3), eh_none(nav4)]

    get_exception(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)
    pr_filtro_bool = True
    if type(local) == list:
        local = get_max(local[0], filtro_value)
        pr_filtro_bool = False

    reg_bool = False
    if (n1 >= n2) & (n1 >= n3) & (n1 >= n4):  # Curitiba
        dff_ = df_idades_cwb.copy()
    elif (n2 > n1) & (n2 > n3) & (n2 > n4):  # NUC
        dff_ = df_idades_PR.copy()
    elif ((n3 > n1) & (n3 > n2) & (n3 > n4)) & pr_filtro_bool:  # PR
        dff_ = df_idades_PR.copy()
    else:  # REGIONAIS
        reg_bool = True
        dff_ = df_idades_reg.copy()

    dff_ = dff_[dff_.localidade == local]

    return plotPiramide(dff_, local, reg_bool)


@app.callback(
    Output("ev_demo", "figure"),
    Output("grafico_serie_idades", "figure"),
    [Input("voltar_localidade", "n_clicks_timestamp"),
     Input("cwb_button", "n_clicks_timestamp"),
     Input("nuc_button", "n_clicks_timestamp"),
     Input("pr_button", "n_clicks_timestamp"),
     Input("reg_button", "n_clicks_timestamp"),
     Input("drop_dados", "value"),
     Input("dados_state", "value"),
     Input("visualizacao_state", "value"),
     Input("btn_inicio", "n_clicks_timestamp"),
     Input("btn_app", "n_clicks_timestamp"),
     Input("btn_dados", "n_clicks_timestamp"),
     Input("btn_publi", "n_clicks_timestamp")]
)
def update_demo2(n0, n1, n2, n3, n4, dados, dados_state, visual, nav1, nav2, nav3, nav4):
    n0, n1, n2, n3, n4 = [eh_none(n0), eh_none(n1), eh_none(n2), eh_none(n3), eh_none(n4)]
    nav1, nav2, nav3, nav4 = [eh_none(nav1), eh_none(nav2), eh_none(nav3), eh_none(nav4)]

    get_exception(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)

    if (n1 >= n2) & (n1 >= n3) & (n1 >= n4):  # Curitiba
        dff_ = df_ev_idades[df_ev_idades.localidade == "Curitiba"]
        title = "Curitiba"
    elif (n2 > n1) & (n2 > n3) & (n2 > n4):  # NUC
        dff_ = df_ev_idades[df_ev_idades.localidade == "Paraná"]
        title = "Paraná"
    elif (n3 > n1) & (n3 > n2) & (n3 > n4):  # PR
        dff_ = df_ev_idades[df_ev_idades.localidade == "Paraná"]
        title = "Paraná"
    else:  # REGIONAIS
        dff_ = df_ev_idades[df_ev_idades.localidade == "Paraná"]
        title = "Paraná"

    if "diario" in dados_state:
        dados_state = 1
    else:
        dados_state = 0

    dic_dados = {
        0: {0: "casosAcumulados", 1: "casosNovos"},
        1: {0: "obitosAcumulados", 1: "obitosNovos"},
        2: {0: "CFR", 1: "CFR"},
        3: {0: "obitosAcumulados", 1: "obitosNovos"},
        4: {0: "obitosAcumulados", 1: "obitosNovos"}
    }
    if visual == 0:
        red = Color("blue")
        colors = list(red.range_to(Color("red"), 17))
        colors = list(map(lambda cor: cor.hex, colors))

        fig_max = px.bar(
            dff_,
            x="date",
            y=dic_dados[dados][dados_state],
            color="idade",
            title=title + " - " + label[dic_dados[dados][dados_state]].lower() + " por faixa etária",
            color_discrete_sequence=colors,
            labels=label

        )
    else:
        fig_max = px.line(
            dff_,
            x="date",
            y=dic_dados[dados][dados_state],
            color="idade",
            title=title + " - " + label[dic_dados[dados][dados_state]].lower() + " por faixa etária",
            color_discrete_sequence=px.colors.qualitative.Light24,
            labels=label
        )

    fig_max.update_layout(
        title=dict(
            font_family="myriad",
            font_size=22
        )
    )
    fig_max.update_yaxes(title_text='')

    fig_min = go.Figure(fig_max)

    return fig_min, fig_max


@app.callback(
    Output("table_min", "columns"),
    Output("table_min", "data"),
    Output("table_tot", "columns"),
    Output("table_tot", "data"),
    [Input("voltar_localidade", "n_clicks_timestamp"),
     Input("cwb_button", "n_clicks_timestamp"),
     Input("nuc_button", "n_clicks_timestamp"),
     Input("pr_button", "n_clicks_timestamp"),
     Input("reg_button", "n_clicks_timestamp"),
     Input("drop_local", "value"),
     Input("drop_dados", "value"),
     Input("dados_state", "value"),
     Input("table_tot", "sort_by"),
     Input("btn_inicio", "n_clicks_timestamp"),
     Input("btn_app", "n_clicks_timestamp"),
     Input("btn_dados", "n_clicks_timestamp"),
     Input("btn_publi", "n_clicks_timestamp"),
     Input("filtro", "value")]
)
def update_table(n0, n1, n2, n3, n4, local, dados, dados_state, sort_by, nav1, nav2, nav3, nav4, filtro_reg):
    n0, n1, n2, n3, n4 = [eh_none(n0), eh_none(n1), eh_none(n2), eh_none(n3), eh_none(n4)]
    nav1, nav2, nav3, nav4 = [eh_none(nav1), eh_none(nav2), eh_none(nav3), eh_none(nav4)]

    get_exception(n0, n1, n2, n3, n4, nav1, nav2, nav3, nav4)

    logging.info("A tabela começou a ser atualizada.")

    if (n1 >= n2) & (n1 >= n3) & (n1 >= n4):
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_PR[df_tabela_vac_PR == "Curitiba"]
        else:
            dff_ = df_tabela_dist.copy()
    elif (n2 > n1) & (n2 > n3) & (n2 > n4):
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_NUC.copy()
        else:
            dff_ = df_tabela_NUC.copy()
    elif (n3 > n1) & (n3 > n2) & (n3 > n4):
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_PR.copy()
        else:
            dff_ = df_tabela_PR.copy()
    else:
        if (dados == 3) | (dados == 4):
            dff_ = df_tabela_vac_reg.copy()
        else:
            dff_ = df_tabela_reg.copy()

    if filtro_reg != 0:
        filtro = df_def_reg.groupby("regional"). \
            get_group(dic_reg[filtro_reg])["codigo"].reset_index(drop=True).to_numpy()
        dff_ = dff_[dff_.codigo.isin(filtro)]

    if type(local) != str:
        dff_ = dff_.query('localidade in @local').reset_index(drop=True)

    dff_["localidade"] = dff_["localidade"].map(lambda local_: dic_locais[local_])

    # tabela 1
    colunas = list(dff_.columns)
    variavel = get_y(dados, dados_state)
    colunas.remove('localidade')
    colunas.remove(variavel)

    table1 = dff_.copy()

    table1 = table1.drop(colunas, axis=1)
    table1 = table1.sort_values(by=variavel, ascending=False)

    # tabela 2
    if len(sort_by):
        dff_ = dff_.sort_values(
            sort_by[0]["column_id"],
            ascending=sort_by[0]["direction"] == 'asc',
            inplace=False
        )

    logging.info("A tabela terminou de ser atualizada.")

    table1 = table1.rename(columns={"obitosAcumulados": "Óbitos",
                                    "casosAcumulados": "Casos",
                                    "localidade": "Localidade",
                                    "CFR": "Letalidade"})

    return [{"name": k, "id": k} for k in table1.columns], table1.to_dict('records'), \
           [{"name": k, "id": k} for k in dff_.columns], dff_.to_dict('records')


@app.callback(
    Output("div_serie_idade", "hidden"),
    [Input("drop_local", "value"),
     Input("drop_dados", "value")]
)
def serie_idades_hidden(local, dados):
    if not (dados in [0, 1, 2]):
        return True

    if local in ["Curitiba", "Paraná"]:
        return False
    else:
        return True


# xs=5, sm=5, md=5, lg=2, xl=2
@app.callback(
    Output("div_controles", "hidden"),
    Output("test1", "xs"),
    Output("test1", "sm"),
    Output("test1", "md"),
    Output("test1", "lg"),
    Output("test1", "xl"),
    Output("test2", "xs"),
    Output("test2", "sm"),
    Output("test2", "md"),
    Output("test2", "lg"),
    Output("test2", "xl"),
    Output("test2", "style"),
    Input("hidden_painel", "n_clicks"), prevent_initial_call=True
)
def hide(n_clicks):
    if n_clicks % 2 == 0:
        style = {"background-color": "#f8f8f8", "margin-left": "16.5%"}
        return False, 5, 5, 5, 2, 2, 11, 11, 11, 10, 10, style
    else:
        style = {"background-color": "#f8f8f8", "margin-left": "8%"}
        return True, 1, 1, 1, 1, 1, 11, 11, 11, 11, 11, style



app.clientside_callback(
    """
    function(clicks, elemid) {
        document.getElementById(elemid).scrollIntoView({
          behavior: 'smooth'
        });
    }
    """,
    Output('garbage-output-0', 'children'),
    [Input('btn_inicio', 'n_clicks')],
    [State('garbage-output-0', 'id')], prevent_initial_call=True
)

app.clientside_callback(
    """
    function(clicks, elemid) {
        document.getElementById(elemid).scrollIntoView({
          behavior: 'smooth'
        });
    }
    """,
    Output('garbage-output-1', 'children'),
    [Input('btn_dados', 'n_clicks')],
    [State('garbage-output-1', 'id')], prevent_initial_call=True
)

app.clientside_callback(
    """
    function(clicks, elemid) {
        document.getElementById(elemid).scrollIntoView({
          behavior: 'smooth'
        });
    }
    """,
    Output('garbage-output-2', 'children'),
    [Input('btn_modelo', 'n_clicks')],
    [State('garbage-output-2', 'id')], prevent_initial_call=True
)

app.clientside_callback(
    """
    function(clicks, elemid) {
        document.getElementById(elemid).scrollIntoView({
          behavior: 'smooth'
        });
    }
    """,
    Output('garbage-output-3', 'children'),
    [Input('btn_publi', 'n_clicks')],
    [State('garbage-output-3', 'id')], prevent_initial_call=True
)

app.clientside_callback(
    """
    function(clicks, elemid) {
        document.getElementById(elemid).scrollIntoView({
          behavior: 'smooth'
        });
    }
    """,
    Output('garbage-output-4', 'children'),
    [Input('btn_equipe', 'n_clicks')],
    [State('garbage-output-4', 'id')], prevent_initial_call=True
)


if __name__ == '__main__':
    app.run_server(debug=True)