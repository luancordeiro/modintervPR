# Repositório com dados utilizados pelo ModintervPR

Foram feitas análises em quatro níveis geográficos:

- Regionais de saúde do Paraná como definido pela Secretaria de Estado da Saúde do Paraná - SESA (https://www.saude.pr.gov.br/Pagina/Regionais-de-Saude).
- Municípios do Paraná.
- Núcleo Urbano Central de Curitiba (NUC) como definido pela Coordenação da Região Metropolitana de Curitiba - COMEC (http://www.comec.pr.gov.br/FAQ/Municipios-da-Regiao-Metropolitana-de-Curitiba).
- Distritos sanitários de Curitiba como definido pela Prefeitura Municipal de Curitiba (https://www.curitiba.pr.gov.br/servicos/enderecos-da-vigilancia-sanitaria-municipal/729).

Em geral, todos os arquivos de dados seguem a divisão distritos_cwb,municipios_PR,regionais_PR. Com exceção das pirâmides etárias, os dados e mapas para as regionais de saúde e NUC são obtidos através dos dados municipais usando as definições acima.

## Infecção de Covid-19
Os dados relativos à infecção de Covid nos municípios são os dados "Geral" disponibilizados pela SESA (https://www.saude.pr.gov.br/Pagina/Coronavirus-COVID-19). Para a localidade considera-se o município de residência (*MUN_RESIDENCIA*), para o número de óbitos novos num dado dia é utilizada a soma dos óbitos na data de óbito (*DATA_OBITO*), enquanto que para os casos novos é feita a soma sobre a data de diagnóstico (*DATA_DIAGNOSTICO*).

Já para os distritos de Curitiba são obtidos pela Prefeitura Municipal de Curitiba (https://www.curitiba.pr.gov.br/dadosabertos/busca/?grupo=16). Para os óbitos é considerado a data de óbito (*DATA ÓBITO*) e para os casos a data de inclusão (*DATA INCLUSÃO/ NOTIFICAÇÃO*).

Os dados estão em arquivos csv na forma (*df_...*)

## Vacinação
Os dados são obtidos pelo Ministério da Saúde (https://opendatasus.saude.gov.br/dataset/covid-19-vacinacao/resource/ef3bd0b8-b605-474b-9ae5-c97390c197a8). Para a localidade considera-se o município do estabelecimento (*estabelecimento_municipio_nome*). Pacientes que tomaram a primeira dose entram no grupo de vacinados parcial e os que tomaram as duas doses ou dose única em vacinados completos

- São desconsiderados dados de pacientes que tomaram segunda dose sem terem tomado a primeira.
- Quando algum paciente tomou mais de uma vez a primeira dose é considerada somente a data mais antiga (a que ocorreu antes). O mesmo ocorre para casos de pacientes que tomaram mais de uma vez a segunda dose.

Não há dados de vacinação para os distritos de Curitiba.

Os dados estão em arquivos csv na forma (*df_vacinacao_...*)

## Dados demográficos

### Dados de população absoluta
Utiliza-se os dados da projeção de 2020 do IBGE para os municípios (https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html?=&t=downloads).

### Pirâmides etárias
Para os municípios do Paraná, regionais de saúde e NUC os dados são da projeção de 2020 do Instituto Paranaense de Desenvolvimento Econômico e Social - IPARDES (http://www.ipardes.pr.gov.br/Pagina/Projecao-Populacional-0).

Já para os distritos de Curitiba são referentes ao senso de 2010 do IBGE, disponibilizados também em relatórios regionais  pelo Instituto de Pesquisa e Planejamento Urbano de Curitiba - IPPUC (https://ippuc.org.br/mostrarpagina.php?pagina=496&idioma=1&ampliar=n%E3o).

Os dados estão em arquivos csv na forma (*idades_...*)

###



