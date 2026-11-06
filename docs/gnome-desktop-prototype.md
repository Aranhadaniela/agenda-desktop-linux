# Etapa 4.3 — widget na área de trabalho

Roteiro operacional atualizado: [Etapa 4.4 — teste visual na VM](gnome-visual-test-4.4.md), com ZIP validado, logs e confirmações.

Investigação de 2026-11-06, branch `feat/gnome-extension`. **O produto é um widget fixo na área de trabalho. Menu de painel não é substituto aprovado.** A proposta de painel da Etapa 4.2 foi retirada como recomendação de produto.

## Conclusão e confiança da evidência

Existe uma abordagem tecnicamente fundamentada para um **protótipo GNOME 46**: anexar um ator passivo ao grupo de fundo já existente. O protótipo está isolado em `desktop/gnome/prototype-desktop/`, com UUID próprio. Não muda a extensão anterior, o Core Python, o modo sintético do adapter ou o instalador da Etapa 4.1.

O acesso a `Main.layoutManager._backgroundGroup` é **privado**. Foi confirmado no tag GNOME Shell 46.0, não inventado nem considerado API estável. O experimento recusa versões diferentes de 46 e uma hierarquia inesperada. Não usa `addChrome` como fallback. A recomendação é **validar essa integração limitada ao GNOME 46**, antes de promovê-la a implementação principal. Não existe ainda aprovação visual Wayland/X11 ou garantia de manutenção em versões futuras.

## Alternativas avaliadas

| Alternativa | Viabilidade e limites | Decisão |
| --- | --- | --- |
| `Main.layoutManager.addChrome` atual | Camada de UI pode cobrir janelas normais. Fullscreen e struts não dão semântica de desktop. | Não satisfaz o produto como implementação final. Mantida apenas no adapter anterior, sem alteração nesta etapa. |
| Ator filho do grupo de fundo | Evita janela externa e usa o grafo do compositor em ambos os backends. Ponto de integração privado; requer testes por versão. | Protótipo recomendado. |
| Ator irmão dos atores de janela em `window_group` | Exigiria acompanhar stacking e conviver com o gerenciamento de atores do Mutter e extensões de desktop. Não há contrato público de z-order persistente para esse ator arbitrário. | Não implementado; risco maior de ordenação. |
| Janela externa X11 tipo DESKTOP/BELOW, sticky | EWMH oferece tipo e estados de desktop. Depende do WM e pode conflitar com aplicações de ícones; hints não equivalem a resultado certificado. | Alternativa específica de X11, não uma solução comum para Wayland. |
| Janela Wayland com layer-shell | Requer protocolo suportado pelo compositor. A biblioteca upstream declara GNOME-on-Wayland não suportado. Instalar GTK Layer Shell não acrescenta esse suporte ao Mutter. | Não usar como base GNOME 46. |
| Integrar com aplicação/extensão de ícones de desktop | Pode compartilhar uma superfície de desktop, mas cria dependência de outro produto e de suas APIs/ciclo de vida; nenhuma integração concreta certificada. | Investigar apenas se conflito com ícones inviabilizar o ator de fundo. |
| Pintar eventos no wallpaper | Não oferece controles ou navegação acessível e acopla atualizações a imagens/papel de parede. | Não implementado. |
| Menu de painel | Experiência diferente da solicitada. | Fora do direcionamento, sem migração automática. |

Fonte para hints X11: [EWMH](https://specifications.freedesktop.org/wm/latest/ar01s05.html). Fonte para layer-shell: [projeto GTK Layer Shell](https://github.com/wmww/gtk-layer-shell#supported-desktops). Uma janela XWayland não deve ser confundida com uma API Wayland portátil de desktop. Não foram usados comandos para abaixar/reparentear janelas reais.

## Base técnica verificada no GNOME 46

No [layout.js 46.0](https://raw.githubusercontent.com/GNOME/gnome-shell/46.0/js/ui/layout.js), o Shell cria `_backgroundGroup` dentro de `global.window_group`, abaixo dos demais filhos. `addChrome` pertence a outra camada. O protótipo exige essa relação e grupo de fundo primeiro na lista de filhos, e só eleva seu próprio ator **dentro do fundo**, sem reordenar janelas.

O [MetaBackgroundGroup do Mutter 46](https://raw.githubusercontent.com/GNOME/mutter/46.0/src/compositor/meta-background-group.c) deriva de ClutterActor e participa da otimização de oclusão. Isso fundamenta a escolha do contêiner, mas não constitui teste visual de St dentro dele.

[BackgroundManager 46](https://raw.githubusercontent.com/GNOME/gnome-shell/46.0/js/ui/background.js) cria e troca atores de wallpaper. O protótipo acompanha `child-added` para ficar acima do wallpaper, permanecendo no grupo de fundo. Não altera o wallpaper nem destrói atores de terceiros.

A agenda não representa uma Meta.Window e não pertence a um workspace específico. A expectativa é o mesmo widget no desktop de todas as áreas de trabalho, atrás das janelas da área ativa. As [animações de workspace 46](https://raw.githubusercontent.com/GNOME/gnome-shell/46.0/js/ui/workspaceAnimation.js) montam clones de janelas e fundos; o ator adicionado não ganha automaticamente uma representação em cada clone. Pode desaparecer durante a animação e reaparecer ao final. Não foi feito monkey patch para cloná-lo. Overview e modos diferentes de `user` ocultam o protótipo explicitamente.

Sinais `workareas-changed`, `active-workspace-changed`, `child-added` e `destroy`, métodos de hierarquia/posição/clip e `Meta.Workspace.get_work_area_for_monitor` foram conferidos por introspecção nos typelibs Clutter/Meta 14 do GNOME 46 local. Estados e sinais de overview/sessionMode foram conferidos nos fontes upstream. Não houve criação de atores reais ou ativação de extensão durante essa verificação.

## Escopo do protótipo

- UUID: `agenda-desktop-linux-desktop-prototype@extensions.local`, diferente das duas extensões anteriores.
- Somente dados sintéticos em memória, relativos a hoje/amanhã; reutiliza `events.js` para datas e grupos.
- Não lê cache ou INI, não importa GI no Python, não executa Python/subprocesso, não consulta EDS, não possui rede nem ações de atualização de calendário.
- Um cartão por monitor lógico, mesma agenda; reposiciona ao mudar monitores, work area ou workspace. Usa coordenadas lógicas, sem multiplicar escala manualmente, e limita geometria à work area. Clipping pode cortar conteúdo em telas pequenas: é um limite explícito de protótipo.
- Atualiza a demonstração a cada 60 segundos para acompanhar mudança de dia.
- Todos os descendentes são não reativos; propriedades de foco/hover são desligadas quando existem. Sem botão, scroll interativo, captura de eventos de stage, keybinding, grabs, input region adicional ou reserva de espaço.
- A expectativa é que eventos destinados às janelas permaneçam com elas; não registrar eventos é uma escolha de implementação, **não prova automatizada de entrega real de cliques**. Deve ser validada nos dois backends.
- Encerra timers e sinais e destrói somente sua própria árvore. Disable é idempotente e erros em enable fazem cleanup. Se o grupo de fundo for destruído, deixa de renderizar e não procura outro contêiner de overlay; reabilitação em ambiente compatível será necessária.

O desenho não promete ficar acima de janelas de desktop opacas criadas por outras extensões. Ícones de desktop podem aparecer acima ou interceptar input nessa região. Registrar o resultado com e sem essa integração em VM; não desativar extensões do host. Outras extensões que mudem a hierarquia invalidam as premissas verificadas. Sessões com modos personalizados diferentes de `user` ficam ocultas por segurança.

## Personalização e acessibilidade

O helper `desktopRect` separa geometria da camada, e o CSS continua separado; isso permite evoluir para posição/tamanho/aparência configuráveis sem mover janelas. Ainda não há preferências, arraste, redimensionamento ou persistência dessas opções.

Passividade é intencional para testar stacking e evitar roubo de input. O protótipo não oferece navegação por teclado nem garante que Orca encontre texto fora da UI normal. Isso é uma pendência de produto, não uma justificativa para um menu de painel. Próxima investigação: leitura acessível dos eventos e modo explícito de edição/posicionamento que permita foco apenas quando solicitado, sem transformar o widget em overlay permanente. Alto contraste, escala, lupa e nomes acessíveis precisam de validação real.

## Arquivos e pacote

Novos fontes: `desktop/gnome/prototype-desktop/{extension.js,desktopLayer.js,metadata.json}`, `scripts/build_gnome_desktop_prototype.py`, `tests/test_gnome_desktop_layer.js`, `tests/test_gnome_desktop_package.py` e este documento. O builder usa `events.js`, `stylesheet.css` e `LICENSE` existentes, sem duplicar a lógica de calendário no código-fonte.

O builder só prepara arquivos, **não tem modo de instalação** e bloqueia preparação nos diretórios XDG/padrão de extensões. Destino existente é recusado. Uma exceção exata no `.gitignore` permite apenas o metadado público desse protótipo; JSONs de eventos continuam ignorados.

```bash
/usr/bin/python3 scripts/build_gnome_desktop_prototype.py
```

Pacote preparado e inspecionado nesta etapa: `dist/gnome-desktop-prototype/agenda-desktop-linux-desktop-prototype@extensions.local/`, seis arquivos em modo 0644: `extension.js`, `desktopLayer.js`, `events.js`, `metadata.json`, `stylesheet.css`, `LICENSE`. Não contém provider/Core Python, configurações ou dados pessoais. O builder foi executado apenas para preparar esse pacote ignorado pelo Git.

## Procedimento seguro de validação visual

**Nenhuma instalação ou ativação foi feita.** Os passos de instalação/ativação abaixo são instruções manuais futuras; se o agente conduzir essa parte, deve pedir autorização antes. Não instalar no host pessoal nesta investigação.

1. Criar VM com snapshot, GNOME Shell **46**, usuário novo, sem contas online ou diretórios/sockets compartilhados com o host. Conferir `gnome-shell --version`. Usar a sessão Wayland primeiro; depois repetir em sessão Xorg da VM, se disponível. Registrar backend com `echo "$XDG_SESSION_TYPE"`. Não presumir que testar Wayland certifica X11.
2. Transferir somente os seis arquivos do pacote, preservando a estrutura plana. Não transferir HOME, backups, `.git`, INI ou JSONs de eventos. Não é necessário configurar EDS nem o modo sintético do adapter: este protótipo nunca usa o adapter.
3. No guest, compactar os seis arquivos em ZIP com metadados na raiz. Exemplo, **a partir da pasta do pacote no guest**:

```bash
/usr/bin/python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile
files = ('extension.js', 'desktopLayer.js', 'events.js', 'metadata.json', 'stylesheet.css', 'LICENSE')
with ZipFile(Path.cwd().parent / 'desktop-prototype.zip', 'x') as archive:
    for name in files:
        archive.write(name, arcname=name)
PY
```

4. Após decisão/autorização separada para instalar **somente no guest**, executar:

```bash
gnome-extensions install ../desktop-prototype.zip
```

Não usar `--force`, UUID antigo, `--replace` ou copiar sobre extensão existente. Se houver conflito, parar e usar snapshot/usuário novo. Esse comando não foi executado nesta etapa.

5. Reabrir a sessão do guest se necessário para descobrir o novo UUID. Após decisão/autorização para ativar **somente no guest**:

```bash
gnome-extensions enable agenda-desktop-linux-desktop-prototype@extensions.local
```

Não habilitar simultaneamente o adapter de `addChrome`, que confundiria o resultado. Host e extensão pessoal permanecem intocados.

6. Executar e registrar o checklist abaixo, com títulos sintéticos visíveis. Qualquer cobertura de janela normal ou roubo de clique é falha de aceitação; não contornar com menu de painel.
7. Ao terminar no guest:

```bash
gnome-extensions disable agenda-desktop-linux-desktop-prototype@extensions.local
```

Confirmar ausência de widget/timer/erro em logs. Se a Shell do guest falhar, encerrar a VM e restaurar snapshot. Não reiniciar nem alterar a Shell do host. Não é necessário remover a extensão original para testar este UUID separado.

### Checklist e critérios de aceitação

- [ ] Widget aparece no desktop vazio; nenhuma janela/entrada no Alt+Tab é criada.
- [ ] Abrir janela normal sobre o cartão: janela cobre o widget; cliques, seleção de texto, rolagem e arraste continuam funcionando na janela.
- [ ] Maximizar e usar fullscreen; nenhum trecho do cartão atravessa a janela, mesmo com movimento entre monitores.
- [ ] Minimizar/restaurar: widget reaparece e volta a ficar atrás da janela, sem comando para elevar/abaixar janelas.
- [ ] Trocar para workspace vazio e ocupado: mesmo widget ao final da transição, atrás das janelas. Registrar desaparecimento durante animação e avaliar se aceitável.
- [ ] Overview e lock screen não mostram o protótipo indevidamente; voltar ao desktop restaura visibilidade.
- [ ] Click/scroll no desktop passam para o comportamento de fundo; botão direito de wallpaper funciona. Não esperar interação com o cartão passivo.
- [ ] Dois monitores, origins/arranjos diferentes, escalas 100/200%, troca de principal, hotplug e resolução: cartões dentro de suas work areas.
- [ ] Trocar wallpaper, inclusive animado se disponível: cartão não some sob novo wallpaper nem apaga o fundo.
- [ ] Repetir com integração de ícones de desktop somente no guest: registrar sobreposição/ocultação e conflito de área.
- [ ] Repetir enable/disable, inclusive em overview: nenhum sinal/ator/timer órfão; falha limpa se versão/hierarquia não forem compatíveis.
- [ ] Texto grande, alto contraste, lupa e Orca: registrar cortes e limitações de leitura/foco. Ainda não há aprovação de acessibilidade.
- [ ] Repetir em Wayland e X11 como resultados separados; não registrar testes não executados como aprovados.

## Testes executados e limites

```bash
/usr/bin/python3 -m unittest discover -s tests -v
TZ=America/Fortaleza gjs -m tests/test_gnome_events.js
TZ=America/New_York gjs -m tests/test_gnome_dst.js
gjs -m tests/test_gnome_lifecycle.js
gjs -m tests/test_gnome_desktop_layer.js
gjs -m scripts/check_gnome_js.js desktop/gnome/prototype-desktop/extension.js desktop/gnome/prototype-desktop/desktopLayer.js tests/test_gnome_desktop_layer.js
```

- 26 testes Python passaram, sem skips, incluindo pacote sintético fechado e recusa de escrita em diretório de extensões.
- Testes GJS de eventos, DST, ciclo de vida anterior e protótipo passaram. Mocks verificam hierarquia, reposição acima de wallpaper, passividade, múltiplos monitores, geometria com origem negativa, lock/overview, workspace, destruição do fundo, versão incompatível e cleanup idempotente.
- Sintaxe dos módulos novos aprovada por SpiderMonkey/GJS 1.80.2; métodos/sinais conferidos por GI sem iniciar sessão gráfica.
- Mocks **não demonstram** oclusão, renderização/culling ou entrega de input real. Esses são os objetivos da VM, ainda pendentes. O protótipo é uma hipótese sustentada pelo fonte, não uma solução de produção certificada.

Não houve acesso a calendários reais, modificação da extensão instalada, instalação, ativação, commit, push, merge ou alteração de `main`.
