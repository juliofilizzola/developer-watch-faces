# Arquitetura

## Visão geral

```
generator/*.py ──(wffgen)──▶ res/raw/watchface.xml ──▶ wff-validator (XSD v2 + semântica)
     │                        res/values*/strings.xml          │
     │                        res/xml/watch_face_info.xml      ▼
     └── scenarios.py         AndroidManifest.xml        Gradle (AGP 9) ──▶ APK debug / AAB release
                                                              │
                         scripts/capture.py ◀── adb ◀── emulador/relógio (runtime WFF real)
                                │
                         reports/screens ──▶ scripts/store_assets.py ──▶ store-assets/
```

### Por que um gerador

O WFF é declarativo e, na v2, **expressões não conseguem ler o valor de uma configuração de lista/booleana**.
Toda combinação de opções que muda a geometria precisa existir como sub-árvore XML. Escrever isso à mão para
5 layouts × 4 tamanhos × 4 formatos de hora × 11 formatos de data × estilos de indicador seria inviável e
propenso a erro. O gerador (`shared/scripts/wffgen`, Python 3 só com stdlib) expande as combinações a partir de
uma descrição compacta e garante: geometria inteira, filhos de opção envolvidos em `Group`, tamanhos de fonte
inteiros e checagem de overflow no círculo de 480 px (`LayoutCheck`).

O `watchface.xml` gerado **é versionado**: o pacote não depende do gerador para compilar, e o diff do XML mostra
exatamente o que muda no produto. Os arquivos gerados começam com um comentário indicando o gerador de origem.

Python foi escolhido para o gerador por não exigir dependências; o **validador** é Kotlin (JVM), porque o XSD
oficial do WFF é XSD 1.1 e precisa do Xerces 1.1 — o mesmo usado pelo validador de referência da Google.

### Camadas de cada mostrador

```
Scene
├── Group "active"           (Variant AMBIENT alpha=0 → some no AOD)
│   ├── fundo (Color config)               JSON/Code
│   ├── chuva digital (density × glyphs)   Matrix
│   ├── ListConfiguration layout
│   │   └── por layout: decoração, relógio (clock_size × time_format × show_seconds), linhas de indicadores
│   └── anéis de bateria/passos (estilo "ring")
├── Group "ambient"          (alpha=0, Variant AMBIENT alpha=200 → só no AOD)
│   └── ListConfiguration aod_mode: hora | hora+data | hora+data+stats
└── ComplicationSlot ext1, ext2 (Variant AMBIENT alpha=0)
```

Técnicas para manter o XML pequeno (≤ ~0,9 MB):

- **Camadas independentes**: no Code, valores (bateria, passos…) não dependem da linguagem — Go usa struct literal
  alinhado pelo gofmt e JS um object literal com a mesma coluna de valores; só as chaves variam com a linguagem.
- **Máscara em vez de duplicação**: no Code, a chave de um indicador oculto é coberta por um retângulo na cor do
  fundo, em vez de repetir a chave dentro de cada opção visível.
- **Tint multiplicativo** (Matrix): intensidade (cinza) × matiz (tint do grupo) sem sub-árvores extras.
- **Cores por configuração**: `[CONFIGURATION.<id>.<n>]` em atributos de cor, sem duplicar nós.

| Face | XML | PartText | Configurações | Flavors |
|---|---|---|---|---|
| JSON Developer | ~0,55 MB | ~460 | 19 + Flavors | 4 |
| Code Developer | ~0,89 MB | ~960 | 19 + Flavors | 7 |
| Matrix Developer | ~0,74 MB | ~700 | 19 + Flavors | 5 |

### Pacotes

Cada módulo Gradle é um app resource-only (`android:hasCode="false"`), `minSdk 34`, propriedade
`com.google.wear.watchface.format.version = 2`, com fontes, ícones e strings próprios. O R8
(`isMinifyEnabled = true`) remove as classes `R` geradas (bundletool rejeita watch faces com dex);
`isShrinkResources = false` porque os recursos são referenciados por nome no XML.

## Tecnologias

| Item | Versão |
|---|---|
| Watch Face Format | v2 |
| Android Gradle Plugin | 9.0.0 (mesma dos samples oficiais) |
| Gradle | 9.2.1 (wrapper) |
| compileSdk / targetSdk / minSdk | 34 / 36 / 34 |
| JDK | 17 (Temurin) |
| Kotlin (validador) | 2.2.21 |
| Python (gerador, assets, captura) | 3.10+ (stdlib; Pillow e fontTools só para assets) |

## Design system

Ver `shared/design-system/README.md`: grade 480×480 com margem de segurança circular, tipografia monoespaçada
(JetBrains Mono para JSON/Code, Share Tech Mono para Matrix), 11 paletas de editor, regras de AMOLED/AOD.
