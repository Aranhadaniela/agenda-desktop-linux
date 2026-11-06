# Etapa 4.4 — execução manual em VM GNOME 46

Preparação: 2026-11-06. Branch `feat/gnome-extension`. **Estado visual: não executado** em Wayland ou X11. Esta etapa prepara pacote, comandos e critérios; não instala nem ativa nada no host.

## Artefato aprovado para transferência

Foram revisados `docs/gnome-desktop-prototype.md` e o builder. O builder não tem modo de instalação e recusa diretórios de extensões e destinos existentes. A opção nova `--archive` gera ZIP fora do diretório de seis arquivos, validando lista, conteúdo byte a byte, permissões e metadados. ZIP usa ordenação e metadados fixos, sem carregar caminhos/nomes do usuário. Conteúdo extra, divergente ou symlink é recusado.

Comando executado localmente, **somente preparação**:

```bash
/usr/bin/python3 scripts/build_gnome_desktop_prototype.py \
  --output dist/gnome-visual-4.4/agenda-desktop-linux-desktop-prototype@extensions.local \
  --archive dist/gnome-visual-4.4/desktop-prototype.zip
```

Os destinos agora existem: repetir o comando os recusará. Para nova preparação, escolher destinos novos, não apagar/sobrescrever o artefato revisado.

ZIP: `dist/gnome-visual-4.4/desktop-prototype.zip`. Checksum externo: `desktop-prototype.zip.sha256`, no mesmo diretório. SHA-256 desta preparação:

```text
8bde8ec0d78925942f77d9a9d746025746b0d9d10612260c1a4b8eee1547202e
```

O hash verifica integridade em relação a esta preparação; não é assinatura nem prova independente de autenticidade. Qualquer mudança futura nos seis fontes muda o hash e exige nova revisão.

**Exatamente seis entradas na raiz do ZIP, sem subdiretórios**, todas com permissões 0644:

```text
LICENSE
desktopLayer.js
events.js
extension.js
metadata.json
stylesheet.css
```

Metadados conferidos: UUID `agenda-desktop-linux-desktop-prototype@extensions.local`, `shell-version: ["46"]`, `version: 1`. Nenhum Core/provider Python, INI, JSON de eventos, cache ou backup integra o pacote. Os eventos são sintéticos em memória; este protótipo não chama Python/EDS, nem precisa de configuração `source = synthetic`. Não executar o adapter das etapas anteriores.

## Confirmações e limites

| Ação | Confirmação necessária se o agente for executar |
| --- | --- |
| Ler fontes, verificar ZIP/hash e executar testes locais | Já autorizados nesta etapa. |
| Criar/provisionar VM ou instalar dependências no guest | Pedir aprovação específica; não realizado aqui. |
| **C1 — instalar o ZIP no guest** | Confirmar nome da VM, usuário de teste, UUID e hash antes de executar. |
| **C2 — ativar no guest** | Pedir confirmação separada de ativação, com a sessão/backend informados. Instalar não equivale a autorizar ativação. |
| Encerrar/reabrir sessão do guest | Confirmar antes, se o agente conduzir, para não perder trabalho aberto. |
| Desativar ao final do teste | Parte da limpeza prevista no ensaio autorizado; somente o UUID do protótipo no guest. |
| Restaurar snapshot | Confirmar antes: descarta mudanças do guest posteriores ao snapshot. |
| Instalar/ativar, reiniciar Shell ou alterar extensão no host | **Proibido nesta etapa**, mesmo que o guest tenha sido autorizado. |

Os comandos abaixo são para execução manual futura **dentro da VM**. Ao executá-los pessoalmente, confira que está no guest. Se delegar ao agente, C1/C2 precisam de autorização explícita; a existência deste roteiro não a concede.

## 1. Preparar a VM

1. Usar hipervisor já disponível que ofereça snapshots. Sugestão de recursos para o ensaio: 2 vCPU, 4 GiB RAM e disco virtual de 30 GiB, ajustando conforme o ambiente. Não foi criada VM nesta etapa.
2. Instalar uma imagem oficial de desktop que forneça GNOME 46, por exemplo Ubuntu 24.04 Desktop. Obter imagem e verificar checksum pelo [site oficial de imagens Ubuntu](https://releases.ubuntu.com/24.04/); **a versão efetiva da Shell será a condição de entrada**, independentemente do nome da ISO. Registrar versão/atualizações; não atualizar para outra versão principal da Shell durante o ensaio.
3. Criar usuário descartável `agenda-test`, sem login em contas online, serviços de sincronização ou navegador pessoal. Não importar HOME, chaveiros, perfis, calendários ou configurações do host.
4. Desabilitar compartilhamento de HOME, clipboard e pastas com o host; não encaminhar sockets D-Bus do host. Não usar sessão aninhada como substituto: o [guia GNOME](https://gjs.guide/extensions/development/debugging.html) informa que ela não é totalmente isolada.
5. Confirmar no guest que existem `gnome-shell`, `gnome-extensions`, `python3`, `sha256sum` e `journalctl`. Não é necessário instalar EDS para este protótipo. Ferramentas de acessibilidade são opcionais para testes específicos; provisioná-las somente após aprovação.
6. Desligar a VM pelo guest, criar snapshot **S0 — GNOME46 limpo**, e ligá-la novamente. Não há comando universal de snapshot entre hipervisores; usar a interface do hipervisor e registrar o identificador sem dados pessoais.
7. Transferir somente `desktop-prototype.zip` e `desktop-prototype.zip.sha256` para o guest, por mídia temporária ou canal de transferência escolhido. Se usar pasta compartilhada temporária, expor apenas esses dois arquivos como somente leitura e desmontar/desconectar após copiar. Não expor a pasta do projeto inteira. A rede pode ser desligada após provisionamento/transferência.

## 2. Selecionar sessão e verificar pré-condições

Na tela de login do guest, selecionar o usuário de teste e, antes de entrar, usar o seletor de sessão:

- Wayland: sessão padrão GNOME/Ubuntu, conforme a distribuição.
- X11: sessão GNOME/Ubuntu **on Xorg**.

Nomes variam. Se a opção não existir ou a virtualização gráfica impedir Wayland, registrar **bloqueado/não executado** para esse backend. Não editar GDM ou forçar um backend sem decisão separada. Não inferir backend pelo menu; verificar no terminal do guest:

```bash
gnome-shell --version
printf 'Backend: %s\n' "$XDG_SESSION_TYPE"
printf 'Desktop: %s\n' "$XDG_CURRENT_DESKTOP"
```

Parar se Shell não for **46.x** ou se o backend não for o pretendido (`wayland` ou `x11`). Registrar resolução, escala, monitores e GPU virtual pela interface Configurações → Monitores. Não coletar número de série, nome real ou informações do host.

Neste roteiro os dois arquivos transferidos devem estar em `~/agenda-visual-4.4/` no usuário do guest. Criar essa pasta pelo gerenciador de arquivos e copiar somente os dois artefatos para ela. No terminal:

```bash
cd "$HOME/agenda-visual-4.4"
sha256sum -c desktop-prototype.zip.sha256
```

Exigir `desktop-prototype.zip: OK` e comparar o checksum com o valor deste documento, recebido por canal confiável. Em seguida, validar estrutura/metadados sem extrair ou executar código:

```bash
/usr/bin/python3 - <<'PY'
import json
from zipfile import ZipFile
expected = {'LICENSE', 'desktopLayer.js', 'events.js', 'extension.js', 'metadata.json', 'stylesheet.css'}
with ZipFile('desktop-prototype.zip') as bundle:
    names = bundle.namelist()
    assert len(names) == 6 and set(names) == expected, 'Lista de arquivos inesperada'
    assert all((entry.external_attr >> 16) & 0o777 == 0o644 for entry in bundle.infolist()), 'Permissões inesperadas'
    assert bundle.testzip() is None, 'ZIP corrompido'
    metadata = json.loads(bundle.read('metadata.json'))
    assert metadata['uuid'] == 'agenda-desktop-linux-desktop-prototype@extensions.local'
    assert metadata['shell-version'] == ['46'] and metadata['version'] == 1
print('Pacote conferido: seis arquivos e GNOME 46.')
PY
```

Não prosseguir se qualquer verificação falhar.

## 3. C1 — instalar somente na VM

**Parar para confirmação C1 antes deste comando**, se o agente conduzir. Instalar como usuário normal do guest, sem sudo:

```bash
cd "$HOME/agenda-visual-4.4"
gnome-extensions install ./desktop-prototype.zip
```

Não usar `--force`. Se existir uma instalação com esse UUID, parar: não substituir, não remover e não modificar a extensão original. Usar snapshot limpo ou usuário novo após confirmação.

O comando instala o pacote, mas não o ativa. Encerrar e reabrir a sessão do **guest** para descoberta limpa. Reescolher o backend pretendido no login e verificar novamente:

```bash
gnome-shell --version
printf 'Backend: %s\n' "$XDG_SESSION_TYPE"
gnome-extensions info agenda-desktop-linux-desktop-prototype@extensions.local
```

Não alterar a lista de extensões habilitadas com `gsettings`. Não habilitar simultaneamente o adapter antigo de `addChrome`. Se houver extensões de ícones de desktop preinstaladas no guest, registrar essa condição; qualquer desativação delas para comparação deve ser limitada ao guest e decidida separadamente.

## 4. Preparar observação e C2 — ativar somente na VM

No terminal do guest, guardar início do ensaio e proteger eventuais arquivos de diagnóstico:

```bash
umask 077
agenda_test_start="$(date --iso-8601=seconds)"
printf 'Início do teste: %s\n' "$agenda_test_start"
```

Manter esse terminal aberto. **Parar para confirmação C2 antes da ativação**, informando VM e backend:

```bash
gnome-extensions enable agenda-desktop-linux-desktop-prototype@extensions.local
gnome-extensions info agenda-desktop-linux-desktop-prototype@extensions.local
```

`info` deve indicar extensão carregada/ativa, sem estado de erro; a palavra exata varia com a versão/idioma. Se o widget não aparecer, fechar o overview antes de concluir que falhou: o protótipo fica oculto nele. Ele também fica oculto fora do modo de sessão `user`.

Não há botão de atualizar nem subprocesso neste experimento. Observar por pelo menos 65 segundos para atravessar um tick de atualização sintética, sem considerar isso prova de ausência de vazamentos.

## 5. Diagnóstico restrito ao guest

Comandos de leitura, **somente no usuário de teste da VM**, no mesmo terminal do marcador de início:

```bash
gnome-extensions info agenda-desktop-linux-desktop-prototype@extensions.local
journalctl --user -b _COMM=gnome-shell --since "$agenda_test_start" --no-pager -n 200 -o cat
```

Se o journal de usuário não contiver a Shell, tentar o journal com filtro pelo UID atual do guest (não exige nem autoriza elevar permissões):

```bash
journalctl -b "_UID=$(id -u)" _COMM=gnome-shell --since "$agenda_test_start" --no-pager -n 200 -o cat
```

Para acompanhar ao vivo em outro terminal, pode usar `journalctl --user -b _COMM=gnome-shell --since '5 minutes ago' -f -o cat`; encerrar com Ctrl+C. Para focar erros, adicionar:

```text
--grep='agenda-desktop-linux-desktop-prototype|JS ERROR|Gjs|TypeError|Error|CRITICAL'
```

Filtros podem ocultar contexto; primeiro revisar localmente as 200 linhas limitadas. Logs não são uma fronteira de privacidade: até uma VM de teste pode registrar caminhos do usuário descartável. Não publicar logs brutos, screenshots do host ou diagnósticos de outras sessões. Se precisar guardar evidência local no guest:

```bash
journalctl --user -b _COMM=gnome-shell --since "$agenda_test_start" --no-pager -n 200 -o cat > shell-test.log
```

Antes de compartilhar, selecionar somente a exceção relevante e remover nomes de usuário, caminhos, hostname e outros metadados. Se não houver permissão para logs, registrar a limitação; não usar sudo nem mudar grupos automaticamente. Não coletar chaveiros, dconf completo, variáveis de ambiente completas ou dados EDS.

No GNOME 46, outra opção no guest é Alt+F2 → `lg`, aba Extensions: inspecionar o estado do UUID e erros. Não executar código na aba Evaluator. O [guia GNOME de debugging](https://gjs.guide/extensions/development/debugging.html) explica que extensões executam dentro da Shell e que uma sessão nova é necessária para garantir recarga de código alterado. Este roteiro usa logout/login do guest em ambos os backends; não usa `gnome-shell --replace` nem reinicia a Shell do host.

### Interpretação de falhas

| Observação | Próxima verificação |
| --- | --- |
| UUID não encontrado | Confirmar instalação no usuário do guest e abrir nova sessão, sem reinstalar com force. |
| Erro de versão | Confirmar 46.x; não editar shell-version para burlar o teste. |
| `desktop layer unavailable` / `hierarchy unavailable` | Guardar exceção sintética e versões; o protótipo falhou sem fallback. Não trocar por overlay. |
| Ativa, mas invisível | Sair do overview, conferir monitores e desktop windows/ícones. Testar minimize/restauração; registrar ambiente. |
| Widget aparece acima de janela | Falha de aceitação de stacking, mesmo se os demais testes passarem. |
| Cliques/rolagem desviados | Falha de aceitação de input; desativar o protótipo no guest. |
| Erro de arquivo ou sintaxe | Revalidar hash e seis entradas. Não corrigir arquivos diretamente na instalação para esconder divergência. |
| Shell congelada ou caiu | Encerrar VM pelo hipervisor; restaurar snapshot somente após confirmação. Não tocar no host. |

## 6. Checklist manual por backend

Copiar o [modelo de resultados](gnome-visual-results-template.md). Marcar **passou, falhou, bloqueado ou não executado**, com evidência sintética para Wayland e X11 separadamente.

| ID | Ação | Resultado esperado |
| --- | --- | --- |
| V01 | Desktop vazio e Alt+Tab | Cartão roxo HOJE/AMANHÃ com títulos `Exemplo:`; nenhuma janela própria no Alt+Tab. |
| V02 | Abrir editor/terminal do guest sobre o cartão | Janela cobre todo o trecho correspondente do widget. |
| V03 | Mover, redimensionar e maximizar janela | Nenhum fragmento do cartão sobe acima da janela. |
| V04 | Fullscreen no guest | Widget permanece atrás; saída de fullscreen restaura comportamento normal. |
| V05 | Minimizar e restaurar a janela | Agenda reaparece ao minimizar e fica atrás ao restaurar. Repetir cinco vezes. |
| V06 | Clicar/arrastar/selecionar texto e rolar na janela sobre o cartão | Interações atingem a janela; nenhum roubo de foco/input. Usar texto fictício. |
| V07 | Clique direito e scroll no desktop, dentro/fora da região do cartão | Mesmo comportamento de fundo; cartão passivo não recebe ações. |
| V08 | Alternar workspace vazio/ocupado | Mesmo widget ao final, atrás das janelas; registrar separadamente eventual desaparecimento na animação. |
| V09 | Overview, lock/unlock do guest | Protótipo oculto no overview/lock; reaparece no desktop após retorno. |
| V10 | Segundo monitor virtual | Um cartão por monitor, dentro da work area. Se hipervisor não oferecer, marcar bloqueado. |
| V11 | Trocar principal, hotplug, resolução e escala 100/200% | Cartões reposicionados sem duplicação; texto/cortes registrados. |
| V12 | Alterar wallpaper no guest | Widget fica acima do wallpaper e abaixo das janelas, sem apagar/alterar o fundo. |
| V13 | Esperar atualização de 60 s | Sem erro ou duplicação observável; lista continua sintética. |
| V14 | Texto ampliado, alto contraste, lupa/Orca se disponíveis | Registrar legibilidade e limitações. Ausência de foco por teclado é limite conhecido do protótipo passivo. |
| V15 | Desativar com janela sobreposta, reativar somente com novo consentimento | Cartão some sem afetar janela; ao reativar não duplica. |
| V16 | Desativação final e logs | Nenhum cartão órfão; Shell continua utilizável e sem novas exceções do protótipo. |

Critérios centrais: V02–V08 não podem falhar para aprovar stacking/input. Itens bloqueados não contam como aprovados. Sumir durante animação de workspace é limitação conhecida a registrar, não evidência de widget acima de janelas. Acessibilidade e clipping continuam pendentes até validação real. Não substituir o produto por menu de painel para contornar falhas.

## 7. Encerrar e repetir no outro backend

No guest, desativar apenas o protótipo:

```bash
gnome-extensions disable agenda-desktop-linux-desktop-prototype@extensions.local
gnome-extensions info agenda-desktop-linux-desktop-prototype@extensions.local
journalctl --user -b _COMM=gnome-shell --since "$agenda_test_start" --no-pager -n 200 -o cat
```

Confirmar desaparecimento de todos os cartões e funcionamento das janelas. Logs e observação não comprovam sozinhos ausência absoluta de timers; testes com mocks verificam essa limpeza em código.

Salvar apenas evidências sanitizadas fora da VM se necessário. Para repetir com base idêntica, desligar guest, **confirmar restauração de S0**, restaurar e repetir transferência/verificação/C1/C2 no outro backend. Alternativamente usar snapshot clonado com a instalação ainda desativada, registrando a diferença. Sempre reiniciar o marcador de logs após login. Não contar resultados Wayland como X11 ou vice-versa.

Não há motivo para desinstalar/desativar a extensão original do host. O UUID é distinto e todos os comandos de alteração se limitam ao guest descartável.

## Verificações locais desta preparação

29 testes Python passaram, sem skips; GJS de eventos, DST, ciclo de vida e camada passou; sintaxe dos módulos conferida. O ZIP foi conferido contra seis fontes, e o checksum foi validado. Não foram lidos logs do host nem executadas instalação, ativação, criação de VM, commit, push ou merge. Resultados visuais permanecem não executados.
