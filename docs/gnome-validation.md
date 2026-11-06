# Etapa 4.2 — preparação da validação GNOME 46

Data: 2026-11-05. Branch: `feat/gnome-extension`. Nenhuma extensão foi instalada ou ativada; nenhuma sessão gráfica nova foi iniciada. Esta etapa prepara os testes e não certifica a interface visual.

## Instalador e pacote

`python3 scripts/install_gnome.py` sem argumentos só cria `dist/gnome/agenda-desktop-linux@extensions.local`. Não acessa calendários, não chama `gnome-extensions` e não escreve no diretório de extensões. `--output` também é preparação; os destinos padrão de instalação são bloqueados nesse modo. Somente `--install`, com confirmação interativa, usa o diretório XDG de extensões. Qualquer destino existente é recusado, inclusive symlinks; não há opção de substituição.

Foi executado o modo sem argumentos: como o pacote já existia, retornou 2 e os hashes dos seus 14 arquivos permaneceram iguais. Um teste em checkout temporário confirmou também o primeiro build sem argumentos e a preservação de uma instalação simulada. Nenhuma escrita no diretório real de extensões foi necessária.

O pacote antigo em `dist/gnome/` foi preservado e está desatualizado em `update_events.py`. Para esta validação foi preparado **outro** pacote em:

```text
dist/gnome-validation-4.2/agenda-desktop-linux@extensions.local/
├── LICENSE
├── extension.js
├── events.js
├── metadata.json
├── stylesheet.css
├── update_events.py
└── python/
    ├── core/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── calendar_service.py
    │   ├── json_writer.py
    │   └── timezones.py
    └── providers/
        ├── __init__.py
        ├── base.py
        └── evolution.py
```

Os 14 arquivos foram comparados byte a byte com os fontes atuais; todos têm modo 0644. Metadados: UUID público `agenda-desktop-linux@extensions.local`, Shell `46`, versão numérica 1 e nome de versão 0.1.0. O pacote não inclui cache, INI, eventos, credenciais ou backup. Arquivos de `dist/` permanecem ignorados pelo Git. Alterações futuras exigem novo build em destino novo, sem sobrescrever este pacote.

Requisitos locais conferidos: GNOME Shell 46.0, GJS 1.80.2 e PyGObject 3.48.2. Para modo EDS são necessários também EDataServer 1.2, ECal 2.0, ICalGLib 3.0, EDS configurado e sessão D-Bus. O modo sintético requer somente Python do sistema, `tzdata` e os componentes normais da interface GNOME; não importa GI nem o provider Evolution no subprocesso Python. Os avisos de dependências em [dependencies.md](dependencies.md) continuam pendentes.

## Isolamento escolhido

Preferir **VM GNOME Shell 46** com snapshot e usuário novo. Ubuntu 24.04 Desktop é um candidato, mas verificar a versão real com `gnome-shell --version`. Não adicionar contas online nem importar o perfil da máquina pessoal. Não compartilhar HOME, diretórios XDG, sockets D-Bus, caches ou sessão do host com o guest. Preparar dependências antes e desconectar a rede para o ensaio sintético, se conveniente. Transferir somente fontes/pacote revisados.

Uma conta separada com login gráfico próprio é alternativa, desde que não compartilhe HOME e dados de contas. Uma Shell aninhada não oferece isolamento suficiente: o [guia GNOME](https://gjs.guide/extensions/development/debugging.html) alerta que ela não é uma sandbox. Alterar somente XDG_CACHE_HOME também não isola contas do EDS. Não usar `gnome-shell --replace` na sessão atual.

## Procedimento visual seguro, a executar manualmente no guest

Os passos abaixo **não foram executados** e não autorizam o agente a instalar ou ativar nada. Se o agente for conduzir essa fase, deve solicitar autorização antes dessas ações. A extensão pessoal permanece intacta no host.

1. Crie snapshot da VM antes do teste. Confirme GNOME Shell 46 e ausência de contas pessoais. Use usuário normal, sem sudo para a extensão.
2. Copie fontes revisados preservando a hierarquia: os cinco arquivos de `desktop/gnome/`, os oito de `core/` e `providers/` listados no instalador, `LICENSE` e `scripts/install_gnome.py`. Não transfira a pasta de trabalho inteira, `.git`, backup, `.env`, INI ou JSONs de eventos. O pacote novo serve para conferir hashes/conteúdo; o instalador atual constrói a partir desses fontes, não instala diretamente um diretório de pacote externo.
3. **Antes de ativar**, configure a fonte sintética no usuário do guest. O trecho abaixo cria arquivo novo de forma exclusiva e recusa substituir uma configuração existente:

```bash
/usr/bin/python3 - <<'PY'
import os
from pathlib import Path
value = os.environ.get('XDG_CONFIG_HOME', '')
base = Path(value) if value and Path(value).is_absolute() else Path.home() / '.config'
directory = base / 'agenda-desktop-linux'
directory.mkdir(parents=True, mode=0o700, exist_ok=True)
path = directory / 'gnome.ini'
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w', encoding='utf-8') as stream:
    stream.write('[calendar]\nsource = synthetic\n')
print('Configuração sintética criada no guest.')
PY
```

4. Após decisão/autorização para instalar **somente no guest**, execute a partir dos fontes:

```bash
/usr/bin/python3 scripts/install_gnome.py --install
```

Digite o UUID solicitado. O instalador recusa destino existente e não ativa nada. Não contorne essa recusa; use snapshot/usuário novo se necessário.

5. Antes de ativar, pode executar o `update_events.py` do pacote preparado no guest. Com o INI sintético ele deve gerar quatro eventos `Exemplo:` no cache privado, sem consultar EDS. Se houver erro, interrompa e confira o INI; não remova a seleção sintética para tentar corrigir. O teste automatizado já bloqueia imports GI/EDS e verifica esse caminho.
6. Após decisão/autorização para ativar **somente no guest**, reabra a sessão do guest se necessário e execute:

```bash
gnome-extensions enable agenda-desktop-linux@extensions.local
```

Confirme que aparecem apenas títulos `Exemplo:`. Não use o UUID antigo. O UUID distinto evita colisão, mas não justifica ativar no host pessoal.

7. Execute o checklist abaixo. Registre versão, resolução, escala, resultado e erro observado; screenshots e logs somente do guest sintético. Não forneça logs da sessão pessoal.
8. Para encerrar o teste no guest:

```bash
gnome-extensions disable agenda-desktop-linux@extensions.local
```

Confira desaparecimento do widget e encerramento do subprocesso. Se a interface travar, encerre a sessão/VM pelo gerenciador da VM e retorne ao snapshot. Não remova arquivos nem reinicie a Shell do host. Não há necessidade de desinstalar ou desativar a extensão pessoal.

## Dados sintéticos

Novo modo opt-in: `[calendar] source = synthetic` no INI privado 0600. Ausência da opção mantém o comportamento EDS anterior; valor desconhecido falha sem fallback. Não existe detecção automática de ambiente de teste.

O provider sintético gera eventos relativos a hoje/amanhã, incluindo dia inteiro com fim exclusivo, vários dias, horário local com offset, ausência de fim e título longo com `<b>` literal. Usa `CalendarService` e `write_events` reais, mantendo o contrato JSON e permissão 0600. Não importa o provider Evolution, não descobre fontes nem precisa de UID. O cache é separado por usuário/VM; não misturar teste sintético e dados reais no mesmo usuário. O modo não pretende testar expansão real de recorrências do EDS.

## Ciclo de vida e erros avaliados

| Cenário | Resultado automatizado / limitação |
| --- | --- |
| Habilitar | Um widget, um processo inicial, timer de 300 s e timeout de 60 s registrados no harness com mocks. |
| Cliques repetidos | Enquanto há processo ativo, nenhum subprocesso adicional é criado. Lock Python também recusa export simultâneo pelo adapter. |
| Atualização concluída | Remove deadline e recarrega cache; arquivo gravado pelo Core mantém contrato. |
| Cache ausente/inválido | Mensagem genérica; sem exceção não tratada nos casos exercitados. Cache inválido após dados anteriores mantém a lista antiga. |
| Falha de criação do processo | Mensagem genérica, processo nulo; timer permite tentar novamente. |
| Processo sem concluir | Timeout chama `force_exit`; callback posterior mantém mensagem de falha. Não promete cancelar trabalho já delegado ao EDS. |
| Desabilitar com I/O ativo | Remove timer/deadline, desconecta sinal, remove ator, cancela leitura e termina processo. |
| Reabilitar antes de callback antigo | Identidade de processo/leitura impede callback anterior de alterar nova sessão. |
| Falha parcial durante construção dos atores | Não simulada; `disable()` pressupõe widget criado. Testar no Shell e considerar cleanup defensivo em alteração posterior. |
| Suspensão ou meia-noite | Reagrupamento depende do próximo tick; pode ficar desatualizado por até cerca de cinco minutos, além de atraso da sessão suspensa. |
| Cache antigo | Não há carimbo de atualização nem idade visível. Uma leitura inicial tardia pode substituir temporariamente o status de falha/atualização. Propor estado explícito e carimbo antes de afirmar que dados estão atuais. |

O harness GJS injeta objetos falsos e executa os métodos do fonte confiável sem importar St/Shell. Isso verifica contratos de ciclo de vida, não renderização, timing real, foco ou integração do compositor.

## Sobreposição: risco e proposta

A [implementação do LayoutManager no GNOME 46](https://raw.githubusercontent.com/GNOME/gnome-shell/46.0/js/ui/layout.js) coloca `window_group` dentro de `uiGroup`; `addChrome()` adiciona o widget nessa UI, abaixo de `top_window_group`. Portanto pode cobrir janelas normais. `affectsStruts: false` não reserva espaço, e `trackFullscreen` trata tela cheia, não janelas maximizadas. Não foi corrigido mudando para `_backgroundGroup`, que é privado.

**Direcionamento corrigido na Etapa 4.3:** o produto permanece um widget de desktop. A proposta anterior de menu no painel não foi aprovada e não deve orientar a implementação. Consulte a [investigação e o protótipo de camada de fundo](gnome-desktop-prototype.md). O adapter original ainda usa overlay; o protótipo separado investiga stacking real, com API privada verificada e validação visual pendente.

## Checklist visual e acessibilidade — todos pendentes no Shell real

- [ ] Roxo, contraste e hierarquia visual legíveis; título e botão sem cortes.
- [ ] HOJE/AMANHÃ corretos; dia inteiro e vários dias aparecem nos grupos esperados; fim exclusivo não cria um dia extra.
- [ ] Horários UTC/offset aparecem no fuso local; títulos com markup permanecem literais.
- [ ] Lista vazia, cache ausente, cache inválido, fonte inválida e erro de processo têm mensagens compreensíveis.
- [ ] Botão e timer atualizam sem duplicação; depois de falha é possível recuperar sem reiniciar Shell.
- [ ] Janela normal, maximizada e fullscreen não têm botões/textos encobertos; documentar falha esperada do overlay atual.
- [ ] Overview, troca de workspace, suspensão/retomada, bloqueio e desbloqueio não deixam ator órfão ou dados visíveis indevidamente.
- [ ] Monitores com origem negativa, troca de principal, desconexão e escala 100/200% posicionam e dimensionam corretamente.
- [ ] Tela pequena e texto grande: nenhum conteúdo essencial fora da área; scroll utilizável. Largura 340 e altura máxima fixa podem exigir adaptação.
- [ ] Somente teclado: alcançar botão, ver foco, usar Tab/Shift+Tab e ativar por Enter/Espaço; sair sem prender foco.
- [ ] Verificar acesso via navegação do Shell: `can_focus` sozinho não garante que esse widget seja alcançável a partir de outra janela.
- [ ] Orca anuncia título, grupos, eventos, horário e ação de atualizar com nomes adequados; erros/atualizações são percebidos sem repetição excessiva. Não há live region configurada; registrar lacunas.
- [ ] Alto contraste, texto ampliado e lupa mantêm legibilidade. Não depender só de cor ou emoji.
- [ ] Disable/enable repetido, inclusive durante atualização, não deixa timer, sinal, widget ou processo extra.
- [ ] Logs e screenshots contêm somente dados sintéticos; não aparecem diagnósticos privados do provider.

Critério de aprovação: preencher todos os itens aplicáveis com evidências sintéticas; registrar falhas e pendências antes de chamar a extensão pronta para distribuição. Hoje não há aprovação visual/acessível, e a sobreposição é risco conhecido.

## Testes disponíveis

```bash
/usr/bin/python3 -m unittest discover -s tests -v
TZ=America/Fortaleza gjs -m tests/test_gnome_events.js
TZ=America/New_York gjs -m tests/test_gnome_dst.js
gjs -m tests/test_gnome_lifecycle.js
gjs -m scripts/check_gnome_js.js desktop/gnome/extension.js desktop/gnome/events.js tests/test_gnome_events.js tests/test_gnome_dst.js tests/test_gnome_lifecycle.js scripts/check_gnome_js.js
```

Resultado desta preparação: 24 testes Python passaram, sem skips; testes GJS de eventos, DST e ciclo de vida com mocks passaram; sintaxe ESM aprovada no SpiderMonkey/GJS. Nenhuma sessão visual foi executada. Não houve instalação, ativação, commit, push ou merge.
