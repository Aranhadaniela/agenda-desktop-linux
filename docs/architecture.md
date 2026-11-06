# Arquitetura

`main.py → CalendarService → CalendarProvider → EvolutionProvider`

O modelo imutável `CalendarEvent` mantém datas como strings para preservar o contrato atual. O serviço calcula dias civis locais e ordena por instante, aceitando fuso e relógio injetáveis para testes. O writer não depende do EDS.

O provider descobre fontes habilitadas com `SourceRegistry.list_sources` e `check_enabled`; consulta instâncias com `ECal.Client.generate_instances_sync`, incluindo recorrências expandidas pelo servidor. Os horários com timezone próprio são resolvidos pela libical, incluindo identificadores que não correspondem diretamente a nomes IANA.

Referência oficial: [Evolution Data Server](https://gnome.pages.gitlab.gnome.org/evolution-data-server/libedataserver/).

## Próximas validações

- Integração manual com sessão EDS e calendários de teste, incluindo recorrências, exceções e horários flutuantes em consultas que cruzam meia-noite.
- Validar o [adaptador GNOME 46 experimental](gnome-integration.md). KDE Plasma e Cinnamon continuam planejados.
- Empacotamento e instalação; licença MIT definida para os fontes da v0.1.0.

Os testes com bindings reais validam conversões de datas, mas a conexão e os callbacks são simulados. Não certificam comportamento ponta a ponta do servidor nem dos desktops.

## Adapter GNOME

A extensão ESM usa o Core copiado por uma lista fechada no empacotamento, sem alterar sua implementação. O adapter Python adiciona seleção privada, cache XDG e lock; o JSON conserva o mesmo contrato. Veja `gnome-integration.md` para instalação opt-in e limites.

## Direcionamento desktop (Etapa 4.3)

O produto é um widget atrás das janelas, não um menu de painel. Um protótipo sintético isolado investiga o grupo de fundo privado do GNOME 46; não altera o Core ou o adapter existente. Veja [decisões, limites e validação visual](gnome-desktop-prototype.md).
