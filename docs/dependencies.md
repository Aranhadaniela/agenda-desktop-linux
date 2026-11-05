# Dependências e compatibilidade — v0.1.0

Revisão: 2026-11-05. Não foram instalados nem atualizados pacotes. Consultas externas usaram somente nomes públicos de produtos e avisos; dados de calendário não foram enviados.

## Mínimos e ambiente de referência

Não confundir versão de namespace GI com versão de pacote. O programa não usa GTK, Qt, a API de GNOME Shell ou bibliotecas de interfaces de desktop no Core. `unittest`, `zoneinfo`, `dataclasses`, JSON e demais módulos do Core são da biblioteca padrão; não exigem instalação pip.

| Componente | Exigência identificada | Versão local testada |
| --- | --- | --- |
| Python | Mínimo sintático 3.10 (`str \| None`); `zoneinfo` existe desde 3.9. Usar runtime com suporte de segurança. | 3.12.3; pacote python3 3.12.3-0ubuntu2.1 |
| PyGObject | Bindings GI para os namespaces abaixo; menor versão funcional absoluta não certificada. Baseline da v0.1.0: 3.48.2. | 3.48.2-1 |
| EDS / libecal | EDataServer 1.2 e ECal 2.0 obrigatórios; baseline validada 3.52.3, com patches da distribuição. | 3.52.3-0ubuntu1.2 |
| libical / libical-glib | ICalGLib 3.0 obrigatório; baseline validada 3.0.17, sem certificação de segurança integral. | 3.0.17-1.1build3 |
| GLib/GObject | Dependência transitiva; com PyGObject 3.46–3.48, mínimo documentado GLib 2.64. | 2.80.0-6ubuntu3.10 |
| GIRepository | Dependência transitiva; mínimo documentado com PyGObject 3.46–3.48: gobject-introspection 1.64. | libgirepository-1.0-1 1.80.1-1 |
| libffi | Dependência transitiva de GI; mínimo 3.0 na matriz citada. | Gerenciada pela distribuição, não testada isoladamente |
| tzdata | Base IANA necessária para regras sazonais; nenhuma revisão mínima específica determinada. | 2026e-0ubuntu0.24.04.1 |

A baseline é o conjunto conhecido que passou nos testes, não uma promessa de que todo conjunto de versões superiores funcionará. O menor conjunto suportado só poderá ser reduzido após testes de compatibilidade. Não recomendar releases antigas de EDS apenas porque métodos existem nelas.

A API `connect_sync` existe desde EDS 3.8, mas o parâmetro de espera usado pelo projeto foi acrescentado em 3.16. Isso é apenas um limite histórico parcial, insuficiente para estabelecer o mínimo global com ECal 2.0 e ICalGLib 3.0. A documentação confirma também `generate_instances_sync` desde 3.2. Fontes: [connect_sync](https://gnome.pages.gitlab.gnome.org/evolution-data-server/libecal/type_func.Client.connect_sync.html), [generate_instances_sync](https://gnome.pages.gitlab.gnome.org/evolution-data-server/libecal/method.Client.generate_instances_sync.html).

A [matriz oficial do PyGObject](https://pygobject.gnome.org/guide/sysdeps.html) estabelece dependências nativas que o resolvedor pip não avalia. Portanto, não há `requirements.txt` fingindo instalar EDS, GI ou libical. Instalar os pacotes do sistema descritos no README, com revisões de segurança, é o caminho documentado. GTK e Cairo não são importados pelo Core; dependências adicionais do pacote PyGObject devem ser resolvidas pela distribuição.

Python 3.10 atingiu o fim do suporte upstream em outubro de 2026; compatibilidade sintática não o torna uma escolha segura sem cobertura explícita da distribuição. Ver [status oficial das versões Python](https://devguide.python.org/versions/).

## Avisos verificados e limites

| Aviso / componente | Evidência | Conclusão local |
| --- | --- | --- |
| EDS CVE-2026-2604 | O [aviso Ubuntu](https://ubuntu.com/security/CVE-2026-2604) informa correção no Ubuntu 24.04 em 3.52.3-0ubuntu1.2. Afeta manipulação de contatos pelo backend de agenda de endereços. | A revisão instalada coincide com a corrigida. O Core não chama operações de contatos. Isso não certifica todos os componentes EDS. |
| libical CVE-2026-111269 | O [rastreador Debian](https://security-tracker.debian.org/tracker/CVE-2026-111269) registra leitura fora dos limites ao decodificar texto iCalendar; o estado de libical3 está indeterminado. | Aplicabilidade à libical3 instalada e disponibilidade de patch precisam de confirmação. Não executamos payload nem assumimos ausência de impacto. |
| libical CVE-2026-88383 | O [rastreador Debian](https://security-tracker.debian.org/tracker/CVE-2026-88383) registra problema de callback com possível interrupção do processo; libical3 está marcada vulnerável em versões Debian, com impacto considerado desprezível pelo Debian. | Revisão Ubuntu instalada não foi certificada; a classificação Debian não prova explorabilidade aqui. |
| PyGObject | Matriz de compatibilidade revisada; não foi obtido um inventário conclusivo de avisos de segurança para a revisão local. | Não declarar ausência de CVEs; verificar origem e cobertura do pacote da distribuição antes da release. |
| GLib, GIRepository, rede/TLS | Inventário parcial: libsoup 3.4.4-5ubuntu0.10, GnuTLS 3.8.3-1.1ubuntu3.6, além das bibliotecas acima. | Avisos transitivos não foram integralmente cruzados; manter pendência explícita. |

Há uma diferença importante de nome de pacote: as páginas Ubuntu [CVE-2026-111269](https://ubuntu.com/security/CVE-2026-111269) e [CVE-2026-88383](https://ubuntu.com/security/CVE-2026-88383) consultadas listam `libical` como ausente no Ubuntu 24.04, enquanto há `libical3t64` instalado. Esse estado não demonstra que o pacote instalado esteja corrigido. Confirmar com o mantenedor/rastreador da distribuição para o pacote-fonte correto antes de oferecer garantia de segurança.

Não há exploração demonstrada contra o Core nem certificado de ausência de vulnerabilidades. O EDS e a libical processam dados externos, mesmo quando a aplicação só lê eventos. Atualizações e patches retroportados devem ser avaliados pela revisão completa da distribuição. Não compilar ou aplicar patches manualmente apenas a partir desta tabela. Consulte a [documentação de atualizações Ubuntu](https://documentation.ubuntu.com/security/security-updates/).

## Verificação recomendada para lançamento

- Confirmar suporte e origem dos pacotes da distribuição e aplicar atualizações pelo fluxo normal do sistema, separadamente da preparação dos fontes.
- Resolver a aplicabilidade dos avisos libical3 e revisar avisos atuais de Python, PyGObject, GLib, GIRepository, libsoup e TLS para a distribuição alvo.
- Reexecutar os testes após atualizar dependências; adicionar teste de integração com calendário descartável autorizado antes de declarar compatibilidade ponta a ponta.
- Não usar resultados de `pip-audit` como substituto da auditoria de bibliotecas nativas. Não elevar a versão PyGObject isoladamente sem verificar seus requisitos de GLib/GIRepository.
