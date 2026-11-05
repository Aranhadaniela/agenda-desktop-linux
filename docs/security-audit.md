# Auditoria de segurança e privacidade

Data: 2026-11-05. Escopo: estado local do projeto nesta data. Auditoria estática, inventário de arquivos, varredura local de padrões e testes sintéticos. Não é certificação de ausência de vulnerabilidades.

## Parecer

**O conjunto de fontes e documentos revisados está apto a ser preparado para publicação, com as exclusões atuais e revisão final do conteúdo selecionado. Não publicar uma cópia integral da pasta.** Há arquivos locais com eventos que precisam continuar fora de qualquer distribuição. A segurança operacional das dependências ainda não está certificada. A licença deve ser escolhida antes de apresentar a distribuição como open source.

Nenhuma extensão instalada, calendário ou evento foi alterado. Nenhum arquivo privado foi removido. Não foram executados inicialização de Git, staging, commit ou publicação. Conteúdo do projeto e dados privados não foram enviados a serviços externos; somente consultas genéricas a fontes públicas de segurança foram feitas.

## Inspeção de informações sensíveis

Foram lidos os fontes Python, testes e documentos candidatos à publicação. A busca local automatizada cobriu e-mails, atribuições de credenciais, chaves privadas, caminhos de usuário, referências institucionais e identificadores UUID. Foram inspecionadas localmente as estruturas dos JSONs e varridos os arquivos de backup sem imprimir seu conteúdo. Nenhum valor de evento foi reproduzido aqui.

- Dois JSONs locais contêm listas não vazias de eventos. Tratados como privados, independentemente do conteúdo dos títulos; já eram excluídos antes da auditoria.
- Não foram identificados e-mails, credenciais, caminhos pessoais, nomes institucionais ou UIDs reais nos candidatos à publicação.
- Os identificadores nos testes são sintéticos. Os exemplos JSON públicos estão em Markdown e são sintéticos.
- Os quatro arquivos de backup foram varridos localmente e permanecem integralmente excluídos. A ausência de correspondências de padrões não os torna publicáveis.
- Os diretórios de configuração e adaptadores não contêm implementações a revisar neste estado. Não foram encontrados links simbólicos no projeto.
- Caches Python existem e estão excluídos; podem incorporar caminhos locais no bytecode e não devem ser distribuídos.

Uma busca por padrões não detecta todo segredo possível, especialmente dados codificados, nomes próprios ou credenciais sem rótulo. A revisão humana foi aplicada ao código e à documentação publicável; dados locais não receberam autorização para publicação.

## Achados e tratamento

| ID | Risco | Achado | Tratamento |
| --- | --- | --- | --- |
| P1 | Alto se publicados | JSONs locais contêm eventos. Nomes alternativos de exportação não estavam todos protegidos. | Corrigido: todos os `*.json` e `*.json.*` excluídos, em qualquer diretório. Exemplos públicos ficam em Markdown. Arquivos privados preservados. |
| P2 | Médio | Regras duplicadas e cobertura incompleta de temporários e configurações. | Corrigido: `.gitignore` consolidado, sem duplicatas; protege backup, ambientes, credenciais comuns, ferramentas locais, configurações, caches, logs e temporários. |
| C1 | Médio, condicionado ao caminho escolhido | `--output` aceita qualquer destino gravável e substitui um arquivo existente; diretórios pais podem ser links simbólicos. | Proposta pendente: modo de recusa de sobrescrita e política de diretório privado. Não implementada porque altera comportamento. Usar diretório controlado pelo usuário, fora de pastas sincronizadas/publicadas. Não executar com privilégios elevados. |
| C2 | Baixo a médio | `--days` não tem teto; valores enormes causam overflow ou expansão custosa de recorrências. Consulta síncrona sem cancelamento pode bloquear. | Proposta pendente: limitar dias e volume de eventos, adicionar cancelamento e erros controlados. Depende de decisão funcional. |
| C3 | Baixo a médio | Listagem imprime UIDs e nomes; argumento CLI pode ficar no histórico/processos. Tracebacks do EDS/SO podem revelar metadados e caminhos. Nomes podem conter controles de terminal. | Listagem é explícita, sem impressão de títulos de eventos pelo Core. Proposta: sanitizar controles e mensagens de erro e separar diagnóstico privado. Não implementada para preservar saída atual. |
| D1 | Médio, não confirmado | Bibliotecas nativas processam calendários não confiáveis; inventário não comprova correções de CVEs. | Pendente: conferir avisos da distribuição para versões e revisões instaladas, incluindo dependências transitivas. Não há declaração de ausência de CVEs. |
| F1 | Médio, futuro | Interfaces podem interpretar títulos como markup/HTML, ampliar permissões ou expor JSON em rede. | Requisitos de projeto documentados abaixo; interfaces ainda não implementadas, sem certificação possível. |
| G1 | Informativo | Diretório `.git` existe, mas está vazio e não constitui repositório válido. | Nenhum índice, objeto ou histórico acessível a auditar. Nenhum repositório foi inicializado. Não permite afirmar algo sobre cópias ou históricos externos. |

## Código e limites de confiança

Não há uso de shell, subprocessos, `eval`, `exec`, desserialização pickle ou montagem de consultas SQL no código da aplicação. A seleção de UID é comparação exata com fontes habilitadas descobertas no EDS; não há identificador de calendário fixo. Strings de eventos são serializadas por `json.dump`, sem execução. JSON válido não é sanitização para HTML: consumidores devem tratar títulos como texto.

O CLI usa `argparse` e exige inteiro para dias; o serviço rejeita valores não positivos. UID inválido resulta em erro de seleção. O valor de `TZ` é controlado pelo ambiente local e pode apontar para arquivo TZif; configuração inválida pode gerar exceção. Não deve ser tratado como entrada remota confiável nem usado em serviço privilegiado.

O código acessa o EDS via GI e sessão local. Não chama métodos de criação, alteração ou remoção de eventos. Isso não impõe uma permissão de leitura no processo: ele executa com os privilégios do usuário, e as bibliotecas/sessão fazem parte da confiança necessária.

Não há cliente de rede próprio, upload ou telemetria. **Não se pode prometer execução offline:** conectar a uma fonte EDS pode acionar comunicação/sincronização com o serviço já configurado pelo usuário, sem confirmação adicional no CLI. A consulta iniciada pelo usuário não autoriza um destino novo criado pelo projeto. Não há nenhum destino novo no código revisado. A auditoria não conectou à sessão EDS nem capturou tráfego real.

## Escrita JSON

O temporário é criado de forma exclusiva no diretório de destino por `NamedTemporaryFile`, com permissão 0600. O conteúdo é escrito e sincronizado antes de `os.replace`, evitando leitura de JSON parcial em condições normais. O arquivo final mantém 0600, inclusive ao substituir um arquivo 0644. Substituir um link simbólico final troca o link, sem escrever no destino do link; teste sintético confirma esse comportamento em Linux.

Falhas de serialização, `fsync` e substituição preservam o arquivo anterior e limpam o temporário nos caminhos testados. Falhas de criação/escrita são propagadas. A limpeza também pode falhar por permissões ou falha de disco, e interrupção abrupta pode deixar temporário privado contendo eventos. Não há criptografia em repouso nem proteção contra processos do mesmo usuário, root, backups ou sincronização do diretório. Diretórios novos seguem a umask do processo. O diretório não recebe `fsync`, portanto não há garantia de durabilidade após queda de energia. Escritas concorrentes têm política de última substituição bem-sucedida; não há locking.

## Dependências

Inventário local: Python 3.12.3, PyGObject 3.48.2-1, EDS/libecal/libedataserver 3.52.3-0ubuntu1.2, libical 3.0.17-1.1build3, tzdata 2026e-0ubuntu0.24.04.1. Não há requirements, lockfile ou dependências PyPI declaradas. O projeto depende de pacotes do sistema; `pip-audit` isoladamente não certificaria bibliotecas nativas.

Correções podem ser retroportadas pela distribuição: não deduzir vulnerabilidade somente pela versão upstream. Conferir a revisão completa, origem dos pacotes, suporte da distribuição e dependências transitivas (incluindo componentes de rede/TLS do EDS). Nenhum pacote foi instalado ou atualizado nesta auditoria.

A documentação anterior cita compatibilidade sintática com Python 3.10; isso não equivale a suporte de segurança. Em novembro de 2026, deve-se usar versão com suporte upstream ou suporte de segurança explícito da distribuição. Referências públicas: [ciclo de versões Python](https://devguide.python.org/versions/), [política de segurança Python](https://devguide.python.org/security/policy/), [rastreador do pacote EDS no Debian](https://security-tracker.debian.org/tracker/source-package/evolution-data-server). O rastreador Debian é referência do pacote, não um parecer sobre patches Ubuntu instalados.

## Git e inventário de publicação

`git rev-parse --is-inside-work-tree` falhou: não há repositório válido disponível. Não foi possível usar índice ou histórico para confirmar rastreamento; nenhum arquivo pode ser chamado de rastreado neste estado. Um `.gitignore` não protege arquivos já rastreados, inclusões forçadas, anexos de releases nem uploads manuais.

Candidatos identificados, após exclusões locais:

- `.gitignore`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `main.py`.
- `core/__init__.py`, `core/models.py`, `core/calendar_service.py`, `core/timezones.py`, `core/json_writer.py`.
- `providers/__init__.py`, `providers/base.py`, `providers/evolution.py`.
- `tests/test_core.py`, `tests/test_dates_and_evolution.py`.
- `docs/architecture.md`, `docs/json-format.md`, `docs/security-audit.md`.

Esta é uma previsão estática para os arquivos presentes, sem regras globais de Git, não uma simulação real de staging. Diretórios vazios não seriam versionados. Caso um repositório seja criado ou restaurado posteriormente, revisar arquivos selecionados e todo histórico antes de publicar. Não publicar arquivo ZIP da pasta inteira.

## Verificação realizada

- 15 testes passaram, sem skips, com `/usr/bin/python3 -m unittest discover -s tests -v`.
- Três testes adicionais de segurança: falha de `fsync`, permissões na substituição e link simbólico final.
- 11 casos de exclusão passaram por checagem estática dos padrões simples usados no `.gitignore`, sem inicializar Git; nenhuma regra duplicada.
- Conexões EDS são simuladas. Conversões de datas usam os bindings instalados. Não houve leitura via API de calendários reais, integração de desktop ou teste de penetração da sessão D-Bus.

## Pendências e propostas antes de ampliar o uso

1. Conferir atualizações de segurança dos pacotes do sistema antes de recomendar esta instalação como ambiente seguro; esta auditoria não certifica dependências.
2. Escolher licença e revisar somente o conjunto de publicação; manter dados locais excluídos. Quando existir Git, repetir auditoria do índice/histórico, sem presumir que `.gitignore` remove conteúdo anterior.
3. Aprovar ou ajustar limites de consulta, política de sobrescrita e mensagens de erro antes de implementar mudanças funcionais.
4. Futuras interfaces devem renderizar títulos como texto, evitar `innerHTML` e interpolação em comandos, manter arquivo 0600, usar leitura com tratamento de falhas, reduzir permissões e evitar servidor HTTP/telemetria sem decisão explícita. Nunca incluir eventos em logs ou relatórios automáticos.
5. Testar integração somente com calendário descartável autorizado e distribuir pacotes usando fontes oficiais. Revisar novamente permissões, rede e dependências quando interfaces ou instaladores forem adicionados.
