# Arquitetura

`main.py → CalendarService → CalendarProvider → EvolutionProvider`

O modelo imutável `CalendarEvent` mantém datas como strings para preservar o contrato atual. O serviço calcula dias civis locais e ordena por instante, aceitando fuso e relógio injetáveis para testes. O writer não depende do EDS.

O provider descobre fontes habilitadas com `SourceRegistry.list_sources` e `check_enabled`; consulta instâncias com `ECal.Client.generate_instances_sync`, incluindo recorrências expandidas pelo servidor. Os horários com timezone próprio são resolvidos pela libical, incluindo identificadores que não correspondem diretamente a nomes IANA.

Referência oficial: [Evolution Data Server](https://gnome.pages.gitlab.gnome.org/evolution-data-server/libedataserver/).

## Próximas validações

- Integração manual com sessão EDS e calendários de teste, incluindo recorrências, exceções e horários flutuantes em consultas que cruzam meia-noite.
- Adaptadores para GNOME, KDE Plasma e Cinnamon, sem duplicar o Core.
- Empacotamento e instalação; licença MIT definida para os fontes da v0.1.0.

Os testes com bindings reais validam conversões de datas, mas a conexão e os callbacks são simulados. Não certificam comportamento ponta a ponta do servidor nem dos desktops.
