# Configurações suportadas por watch face

Todas as configurações são nativas do WFF v2 (`UserConfigurations`) e aparecem no editor do relógio
(toque longo no mostrador → Personalizar) e no app complementar. Os rótulos estão em inglês e pt-BR.
Legenda: ✅ suportado · ➖ não se aplica · ⚠️ suportado com limitação (ver coluna).

## Tabela geral

| Configuração | Tipo WFF | JSON | Code | Matrix | Opções | Limitações |
|---|---|---|---|---|---|---|
| Layout | List | ✅ | ✅ (layout / densidade) | ✅ | Minimal, Compact, Balanced, Full, Informative | Indicador oculto deixa linha vazia (sem reflow) |
| Formato da hora | List | ✅ | ✅ | ✅ | Seguir o celular, 24h, 12h, 12h + AM/PM | — |
| Mostrar segundos | Boolean | ✅ | ✅ | ✅ | sim/não | Nunca exibidos no AOD |
| Tamanho do relógio | List | ✅ | ✅ | ✅ | S, M, L, XL | Ajuste automático à largura do círculo |
| Formato da data | List | ✅ | ✅ | ✅ | DD/MM/AAAA, MM/DD/AAAA, DD-MM-AAAA, AAAA-MM-DD, DD MMM, MMM DD, Dia + data, Dia abreviado, Dia da semana, Data completa, Oculta | Nomes de mês/dia seguem o idioma do relógio |
| Bateria | List | ✅ | ✅ | ✅ | Percentual, Barra, Anel circular, Ícone + valor, Oculto | — |
| Passos | List | ✅ | ✅ | ✅ | Número, Passos/meta, Barra da meta, Anel, Ícone + quantidade, Oculto | Meta vem do app de saúde |
| Frequência cardíaca | List | ✅ | ✅ | ✅ | Valor, Ícone + valor, Compacto, Oculto | Sem leitura → `null`/`--` |
| Clima | List | ✅ | ✅ | ✅ | Temp + condição, Temperatura, Ícone + temperatura, Condição, Oculto | Precisa de provedor de clima; sem dados → `null`/`nil`/`NO SIGNAL` |
| Unidade de temperatura | List | ✅ | ✅ | ✅ | Padrão do aparelho, Celsius, Fahrenheit | — |
| Linhas de complicações (calorias, distância…) | Boolean + 2 ComplicationSlot | ✅ | ✅ | ✅ | ligado/desligado + provedor livre | Visíveis nos layouts Full e Informative (posição fixa no WFF v2) |
| Always-On Display | List | ✅ | ✅ | ✅ | Só hora, Hora + data, Hora + data + bateria + passos | — |
| Fundo | Color | ✅ | ✅ | ➖ (sempre preto) | Preto AMOLED, Grafite, Cinza editor, Azul meia-noite, Verde profundo | AOD sempre preto |
| Estilo do JSON | List | ✅ | ➖ | ➖ | Formatado, Números de linha, Guias de indentação, Sem chaves | — |
| Linha de status do aparelho | Boolean | ✅ | ➖ (fixa no Balanced/Info) | ➖ (SYS no Info) | — | Estados reais: charging / low_power / running |
| Cor das chaves | Color | ✅ | ➖ | ➖ | 11 paletas | — |
| Cores dos valores (string + número) | Color (2 cores) | ✅ | ➖ | ➖ | 11 paletas | — |
| Cor do relógio | Color | ✅ | ✅ | ➖ (usa cor principal) | 10 cores | — |
| Pontuação / chaves `{}` | Color | ✅ | ➖ | ➖ | 11 paletas | — |
| Linguagem | List | ➖ | ✅ | ➖ | Go, JavaScript | — |
| Tema de sintaxe | Color (5 cores) | ➖ | ✅ | ➖ | VS Code Dark+, Dracula, Monokai, One Dark, GitHub Dark, Nord, Solarized, Gruvbox, Terminal, Âmbar CRT, Mono | Máx. 5 cores por opção no WFF |
| Numeração de linhas | Boolean | ✅ (via estilo) | ✅ | ➖ | — | — |
| Tamanho e espaçamento do código | List | ➖ | ⚠️ | ➖ | S·justo, M·normal, L·espaçado | Fonte e espaçamento combinados (limite de 20 configurações) |
| Aba do editor e barra de status | Boolean | ➖ | ✅ | ➖ | — | — |
| Densidade da chuva | List | ➖ | ➖ | ✅ | Desligada, Baixa, Média, Alta | — |
| Caracteres | List | ➖ | ➖ | ✅ | Binário, Hexadecimal, Dígitos, Símbolos de código | Sem katakana (fonte CJK pesada) |
| Cor principal (tons de verde e alternativas) | Color (2 cores) | ➖ | ➖ | ✅ | 11 tons (6 verdes + ciano, âmbar, vermelho, roxo, branco) | — |
| Cor de destaque | Color | ➖ | ➖ | ✅ | 6 cores | — |
| Intensidade visual | Color (cinza × tint) | ➖ | ➖ | ✅ | Discreta, Baixa, Média, Alta, Máxima | — |
| Brilho do relógio | Color | ➖ | ➖ | ✅ | Sem brilho, verde suave/forte, ciano, âmbar, branco | — |
| Moldura decorativa | Boolean | ➖ | ➖ | ✅ | — | — |

Cada face usa **19 configurações + Flavors = 20**, o máximo permitido pelo WFF v2.

## Presets (Flavors)

| Face | Presets | Mapeamento para o requisito 8 |
|---|---|---|
| JSON Developer | Clean JSON, **Developer** (padrão), Full JSON, AMOLED | Minimal = Clean JSON · Developer · Full Stats = Full JSON · AMOLED |
| Code Developer | **Go Developer** (padrão), JavaScript Developer, VS Code Dark, Terminal, Minimal Code, Full Stats, AMOLED | Minimal = Minimal Code · Developer = Go/JS Developer · Full Stats · AMOLED |
| Matrix Developer | **Classic Matrix** (padrão), Dark Matrix, Minimal Matrix, Full Digital, AMOLED Green | Minimal = Minimal Matrix · Developer = Classic · Full Stats = Full Digital · AMOLED = AMOLED Green |

**Custom:** um preset é só o ponto de partida. Qualquer opção alterada depois vira a configuração personalizada do
usuário (o WFF não tem um "flavor custom" — qualquer edição já é custom).

## Complicações

| Slot | Tipos aceitos | Default | Uso sugerido |
|---|---|---|---|
| `ext1` | SHORT_TEXT, LONG_TEXT, RANGED_VALUE, EMPTY | Nascer/pôr do sol (sistema) | Calorias |
| `ext2` | SHORT_TEXT, LONG_TEXT, RANGED_VALUE, EMPTY | Notificações não lidas (sistema) | Distância |

Renderização: JSON `"<título>": "<texto>",` · Go/JS `<título>: "<texto>",` · Matrix `> <TÍTULO> <texto>`.
Complicações não são configurações de personalização: são fontes de dados externas que o usuário escolhe.
