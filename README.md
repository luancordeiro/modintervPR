# Repositório com dados utilizados pelo ModintervPR

Foram feitas análises em quatro níveis geográficos:

- Municípios do Paraná
- Regionais de saúde do Paraná como definido pela Secretaria de Estado da Saúde do Paraná - SESA (https://www.saude.pr.gov.br/Pagina/Regionais-de-Saude)
- Núcleo Urbano Central de Curitiba (NUC) como definido pela Coordenação da Região Metropolitana de Curitiba - COMEC (http://www.comec.pr.gov.br/FAQ/Municipios-da-Regiao-Metropolitana-de-Curitiba)
- Distritos sanitários de Curitiba

**Com exceção das pirâmides etárias, os dados e mapas para as regionais de saúde e NUC são obtidos através dos dados municipais usando as definições acima.**

## Infecção de Covid-19
Os dados relativos à infecção de Covid nos municípios são os dados "Geral" disponibilizados pela SESA (https://www.saude.pr.gov.br/Pagina/Coronavirus-COVID-19). Para a localidade considera-se o município de residência (*MUN_RESIDENCIA*), para o número de óbitos novos num dado dia é utilizada a soma dos óbitos na data de óbito (*DATA_OBITO*) enquanto que para os casos novos é feita a soma sobre a data de diagnóstico (*DATA_DIAGNOSTICO*).

Os números acumulados são formados a partir da soma dos números novos dos dias anteriores.

## Vacinação
Os dados são obtidos pelo Ministério da Saúde (https://opendatasus.saude.gov.br/dataset/covid-19-vacinacao/resource/ef3bd0b8-b605-474b-9ae5-c97390c197a8). Não há dados de vacinação para os distritos de Curitiba.

## Dados demográficos

### Pirâmides etárias
Para os municípios do Paraná, regionais de saúde e NUC os dados são da projeção de 2021 do Instituto Paranaense de Desenvolvimento Econômico e Social - IPARDES (http://www.ipardes.pr.gov.br/Pagina/Projecao-Populacional-0).

Já para os distritos de Curitiba são referentes ao senso de 2010 do IBGE, disponibilizados também em relatórios regionais  pelo Instituto de Pesquisa e Planejamento Urbano de Curitiba - IPPUC (https://ippuc.org.br/mostrarpagina.php?pagina=496&idioma=1&ampliar=n%E3o).

###



