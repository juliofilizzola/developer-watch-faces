# Watch Face Format — versão escolhida, limitações e alternativas

## Versão escolhida: WFF v2 (minSdk 34 / Wear OS 5)

| Versão WFF | Wear OS / API | Recursos relevantes para este projeto |
|---|---|---|
| v1 | Wear OS 4 / 33 | Configurações (List/Boolean/Color), complicações, expressões, AOD via `Variant` |
| **v2** | **Wear OS 5 / 34** | **Flavors (presets)**, **clima** (`WEATHER.*`), **frequência cardíaca** (`HEART_RATE`), complicações GOAL_PROGRESS/WEIGHTED_ELEMENTS |
| v3 | Wear OS 5.1 / 35 | Texto com auto-size, blend mode, fontes de fuso horário |
| v4 | Wear OS 6 / 36 | Fotos, transições de AOD, `Reference`, cores transformáveis, tint em grupos |
| v5 | Wear OS 6+ | Opções aninhadas e complicações dinâmicas em `ListOption` |

**Por que v2:** é a menor versão que entrega presets (Flavors), clima e frequência cardíaca nativos — requisitos do projeto.
O Galaxy Watch 6 saiu com Wear OS 4 e recebeu Wear OS 5 (One UI 6 Watch) e Wear OS 6 (One UI 8 Watch), portanto todo
Galaxy Watch 6 atualizado executa v2. Subir para v4/v5 reduziria a base compatível sem ganho essencial.
A Google recomenda declarar **a menor versão que suporta os recursos usados**.

Fonte: <https://developer.android.com/training/wearables/wff/features> e o XSD oficial vendorizado em `shared/wff-spec/2`.

## Limites estruturais (verificados no XSD v2)

| Limite | Valor | Impacto / como foi tratado |
|---|---|---|
| Configurações de usuário por mostrador | **20** (Flavors conta como 1) | Cada face usa exatamente 19 configurações + Flavors. Algumas opções foram combinadas (ver abaixo). |
| Flavors (presets) | 20 | JSON 4, Code 7, Matrix 5. |
| Cores por `ColorOption` | **5** | Paleta de sintaxe do Code usa 5 cores: keyword, identificador, string, número, pontuação/comentário. |
| Slots de complicação | 8 | 2 por face (`ext1`, `ext2`) para calorias, distância ou qualquer provedor. |
| Modo de `Variant` | só `AMBIENT` | AOD é feito com grupos `active` (some no ambient) e `ambient` (aparece no ambient). |
| Geometria (`x`, `y`, `width`, `height`) | inteiros | O gerador arredonda toda geometria. |
| Filhos de `ListOption`/`BooleanOption`/`Compare` | 1 elemento, que não pode ser outra configuração | O gerador envolve automaticamente em `Group`. |

## Limitações de comportamento (descobertas e validadas no runtime Wear OS 5)

| # | Limitação | Alternativa adotada |
|---|---|---|
| 1 | **Expressões não leem valores de `ListConfiguration`/`BooleanConfiguration`** em v2. Cada combinação de opções precisa de uma sub-árvore XML própria. | Gerador Python que expande as combinações e mantém o XML ≤ ~0,9 MB por face. Configurações independentes ficam em camadas separadas para não multiplicar. |
| 2 | **Posição de complicações é fixa** (não pode variar por layout em v2; só v5 permite complicações em `ListOption`). | Todos os layouts reservam as mesmas duas linhas (`ext1`/`ext2`). Nos layouts que não exibem complicações, o conteúdo do slot fica vazio via `ListConfiguration` interna. |
| 3 | **Sem "reflow"**: esconder um indicador não reposiciona os demais (não há layout dinâmico dependente de configuração). | A linha oculta vira uma linha em branco — natural num editor de código. A *quantidade* de informação é escolhida pelo layout (Minimal → Informative). |
| 4 | `icuText()` **reordena o padrão para o locale** do aparelho (em en-US, `dd MMM` vira `NOV 04`). | Datas compostas a partir de fontes cruas (`[DAY_Z]`, `[MONTH_Z]`, `[YEAR]`, `[MONTH_S]`, `[MONTH_F]`, `[DAY_OF_WEEK_S/F]`). Nomes de mês/dia continuam localizados pelo idioma do relógio. |
| 5 | Atributo `size` de `Font` é lido como **inteiro** (log `fail to parseInt`), apesar do XSD aceitar float. | Tamanhos de fonte arredondados. |
| 6 | Quebra de linha `\n` dentro de texto **é ignorada**. | Colunas da chuva Matrix: `PartText` com largura de 1 glifo + `maxLines`; o runtime quebra cada caractere numa linha. Espaços nas colunas usam NO-BREAK SPACE. |
| 7 | Espaço na fronteira entre dois `Font` runs pode ser descartado. | Rótulos que precisam do espaço são um único run (ex.: `"> BAT "`). |
| 8 | `null` literal numa expressão é renderizado como texto vazio. | O JSON mostra a string `"null"` quando não há leitura (honesto, nunca inventa valor). |
| 9 | `Group tintColor` **multiplica** a cor dos filhos. | Matrix: glifos em tons de cinza (intensidade) × tint (matiz) = matiz × intensidade sem duplicar sub-árvores. |
| 10 | Após reinstalar, o sistema mantém o estilo salvo do favorito. | `scripts/capture.py` desinstala antes de instalar para testar defaults. |
| 11 | Mostradores de ~0,9 MB levam alguns segundos para carregar no emulador. | Tempo de espera maior na captura; documentado para teste físico. |
| 12 | Bundletool rejeita watch faces (minSdk ≥ 33) com dex. | `isMinifyEnabled = true` (R8 remove as classes R geradas); recursos não são encolhidos. |

## Dados e fontes

| Informação | Fonte | Observação |
|---|---|---|
| Hora, data, dia da semana, segundos, AM/PM, 12/24h do sistema | Fontes nativas (`HOUR_*`, `MINUTE_Z`, `SECOND_Z`, `IS_24_HOUR_MODE`, `AMPM_STRING`, ...) | — |
| Bateria e carregamento | `BATTERY_PERCENT`, `BATTERY_CHARGING_STATUS`, `BATTERY_IS_LOW` | Usados também na linha de status (`charging`/`low_power`/`running`). |
| Passos, meta, progresso | `STEP_COUNT`, `STEP_GOAL` | Meta 0 → barra/anel vazios (divisão por zero = 0 no WFF). |
| Frequência cardíaca | `HEART_RATE` (v2) | Sem leitura → `null` / `--`. O sistema controla permissão e frequência de medição. **Validar no Galaxy Watch 6.** |
| Clima | `WEATHER.*` (v2) | Requer provedor de clima no relógio. Sem dados → `null` / `nil` / `NO SIGNAL`. Conversão °C/°F feita na expressão. |
| **Calorias e distância** | **Não existem como fonte nativa no WFF v2** | Exibidas por **complicações** (`ext1`/`ext2`). O usuário escolhe, no editor do relógio, o provedor (ex.: Samsung Health, se o app expuser essas complicações no aparelho). Os defaults usam provedores de sistema documentados (`SUNRISE_SUNSET`, `UNREAD_NOTIFICATION_COUNT`) — não inventamos nomes de componentes de terceiros. |

Nenhum serviço externo, rede ou código Kotlin roda dentro dos pacotes: WFF é declarativo (`android:hasCode="false"`).

## O que não é possível e o que foi feito no lugar

| Pedido | Situação no WFF v2 | Entregue |
|---|---|---|
| Fonte e espaçamento do código ajustáveis separadamente (Code) | Cada configuração extra multiplica o XML; limite de 20 configurações | Uma configuração "Tamanho e espaçamento do código" (S·justo / M·normal / L·espaçado) + densidade pelo layout. |
| Posição livre de cada indicador | Sem reflow nem posição por expressão de configuração | 5 layouts por face com posições projetadas para o círculo + estilo por indicador (incl. ocultar). |
| Cor individual por indicador | Limite de 20 configurações | Cores por papel (chave, valor/número, relógio, pontuação, destaque) + paletas; anéis usam as cores da paleta. |
| Animação contínua da chuva Matrix | Possível, mas proibida pelo requisito de bateria | Chuva muda um passo por minuto via expressão (sem animação contínua). |
| Katakana na chuva Matrix | Exigiria fonte CJK grande (MBs) | Estilos binário, hexadecimal, dígitos e símbolos de código. |
| Preset "Custom" como flavor | Flavor é ponto de partida; editar qualquer opção já é "custom" | Documentado: após escolher um preset, cada opção é editável individualmente. |
