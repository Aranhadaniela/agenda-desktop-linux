# Agenda Desktop Linux

Versão em preparação: **v0.1.0**. Core Python para consultar calendários do Evolution Data Server (EDS) e exportar eventos em JSON. Nenhuma release foi publicada.

## Estado do projeto

| Componente | Estado na v0.1.0 |
| --- | --- |
| Core e CLI Python | Implementados, com testes automatizados |
| Evolution Data Server | Descoberta, seleção e consulta implementadas; testes de conexão usam mocks |
| GNOME Shell | Adaptador não incluído nesta versão; eventual extensão local não faz parte da distribuição |
| KDE Plasma | Planejado, não implementado |
| Cinnamon | Planejado, não implementado |

O Core não depende de GNOME Shell, GTK ou Qt. Em qualquer desktop, precisa do EDS e de uma sessão D-Bus do usuário com calendários configurados. A compatibilidade ponta a ponta com cada desktop ainda não foi certificada.

## Requisitos

- Linux e Python com suporte de segurança. O código usa recursos de Python **3.10+**, mas essa é uma exigência sintática, não uma recomendação para instalar uma versão sem suporte.
- Ambiente de referência validado pelos testes: Python 3.12.3, PyGObject 3.48.2, EDS 3.52.3 e libical 3.0.17, com revisões de distribuição descritas em [dependências](docs/dependencies.md).
- Namespaces GI obrigatórios: `EDataServer 1.2`, `ECal 2.0` e `ICalGLib 3.0`. Esses números são versões de API, não versões dos pacotes.
- `tzdata`, EDS configurado e sessão D-Bus do usuário ativa.

Versões anteriores ao ambiente de referência não foram testadas como conjunto. Não há instalação PyPI nem empacotamento pronto nesta versão.

## Instalação das dependências

Exemplo para Ubuntu 24.04 e distribuições Debian/Ubuntu com esses nomes de pacotes. Os comandos abaixo são instruções para o usuário; não são executados automaticamente pelo projeto:

```bash
sudo apt update
sudo apt install python3 python3-gi evolution-data-server tzdata gir1.2-edataserver-1.2 gir1.2-ecal-2.0 gir1.2-ical-3.0
```

Use os repositórios oficiais da distribuição, com atualizações de segurança. Bibliotecas nativas GLib/GObject, GIRepository, libecal e libical são resolvidas pelos pacotes. Outras distribuições podem usar nomes diferentes; não há matriz de instalação validada para elas.

Execute a partir da pasta do projeto com `/usr/bin/python3`, que precisa enxergar os bindings GI do sistema. Um ambiente virtual comum pode ocultá-los. Não instale `gi` com pip para substituir `python3-gi`; um upgrade isolado de PyGObject pode exigir bibliotecas de sistema mais novas.

## Comandos

```bash
/usr/bin/python3 main.py --help
/usr/bin/python3 main.py --list-calendars
/usr/bin/python3 main.py --calendar 'UID_OBTIDO_LOCALMENTE' --days 2 --output eventos.json
```

| Opção | Função e padrão |
| --- | --- |
| `--help` | Exibe a ajuda sem consultar calendários |
| `--list-calendars` | Lista UIDs e nomes de fontes habilitadas; não exporta eventos |
| `--calendar UID` | Seleciona exatamente uma fonte habilitada |
| `--days N` | Dias civis a consultar, inteiro positivo; padrão: 2 |
| `--output CAMINHO` | JSON de saída; padrão: `eventos.json` no diretório atual |

`--calendar` tem precedência sobre `CALENDAR_UID`. Sem ambos, o programa seleciona automaticamente se houver apenas um calendário habilitado; com zero ou vários, retorna erro. Não existem UIDs fixos no código. A listagem e os identificadores são privados: não os publique em issues ou commits. Argumentos podem aparecer no histórico do shell e na lista de processos.

A janela começa à meia-noite local de hoje e termina à meia-noite após N dias; inclui eventos anteriores ao horário atual de hoje. O EDS expande recorrências. O JSON mantém `eventos`, `titulo`, `inicio`, `fim` e `dia_inteiro`; veja o [contrato](docs/json-format.md).

A saída substitui um arquivo existente de forma atômica e recebe permissão 0600. Escolha um diretório privado controlado pelo usuário. Não execute como root. Todos os JSONs são ignorados pelo Git por padrão, mas isso não impede upload manual nem inclusão forçada. O projeto não tem telemetria ou upload próprio; o EDS pode sincronizar fontes remotas já configuradas ao ser consultado.

## Testes e documentação

```bash
/usr/bin/python3 -m unittest discover -s tests -v
```

Os 15 testes usam eventos sintéticos, temporários e mocks de conexão EDS. Os testes de conversão usam bindings reais; testes específicos do provider são ignorados quando eles não estão disponíveis. Não há validação automática ponta a ponta dos desktops ou do servidor.

- [Arquitetura](docs/architecture.md) e [contribuições](CONTRIBUTING.md)
- [Dependências e avisos de segurança](docs/dependencies.md)
- [Segurança e privacidade](SECURITY.md) e [auditoria inicial](docs/security-audit.md)
- [Notas da v0.1.0](CHANGELOG.md) e [prontidão para publicação](docs/release-v0.1.0.md)
- [Lista explícita para o primeiro commit](docs/first-commit-files.txt)

## Licença

[MIT](LICENSE). Copyright (c) 2026 agenda-desktop-linux. As dependências mantêm suas próprias licenças; não são redistribuídas neste conjunto de fontes.
