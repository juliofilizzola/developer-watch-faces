# Ambiente, compilação e instalação

## Requisitos

| Ferramenta | Versão | Observação |
|---|---|---|
| JDK | 17 | `JAVA_HOME` (o script usa `~/.local/jdk/jdk-17` como padrão) |
| Android SDK | platform 34, build-tools 34+/36, platform-tools | `ANDROID_HOME` (padrão `~/Android/Sdk`); o AGP baixa o que faltar |
| Python | 3.10+ | gerador e scripts; `Pillow` e `fontTools` só para `./build-all.sh assets` |
| Emulador (opcional) | system image `android-34;android-wear;x86_64` | testes e screenshots |
| Android Studio (opcional) | recente | o projeto abre como projeto Gradle normal |

Instalação sem Android Studio (Linux, em pasta do usuário):

```bash
mkdir -p ~/.local/jdk ~/Android/Sdk/cmdline-tools
```

```bash
curl -fL -o /tmp/jdk.tgz "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse" && tar -xzf /tmp/jdk.tgz -C ~/.local/jdk && mv ~/.local/jdk/jdk-17* ~/.local/jdk/jdk-17
```

```bash
curl -fL -o /tmp/clt.zip https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip && unzip -q /tmp/clt.zip -d /tmp/clt && mv /tmp/clt/cmdline-tools ~/Android/Sdk/cmdline-tools/latest
```

```bash
~/Android/Sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=$HOME/Android/Sdk "platform-tools" "platforms;android-34" "build-tools;34.0.0" "emulator" "system-images;android-34;android-wear;x86_64"
```

(o `sdkmanager --licenses` pede que você aceite as licenças do SDK.)

## Compilar

```bash
./build-all.sh
```

Saída em `dist/` e relatório em `reports/build-report.md`. Para uma face: `./build-all.sh json` (ou `code`, `matrix`).
Para só validar os XMLs: `./build-all.sh validate`.

Editar uma face = editar `<face>/generator/<face>_face.py` e rodar o build (o `watchface.xml` é regenerado).

## Instalar no Galaxy Watch 6

1. No relógio: Configurações → Sobre o relógio → Software → toque 5× em "Versão do software" (modo desenvolvedor).
2. Configurações → Opções do desenvolvedor → ative **Depuração ADB** e **Depurar por Wi-Fi**; anote IP:porta.
3. Pareie e conecte (o relógio mostra o código de pareamento):

```bash
~/Android/Sdk/platform-tools/adb pair IP:PORTA_DE_PAREAMENTO
```

```bash
~/Android/Sdk/platform-tools/adb connect IP:PORTA
```

4. Instale e ative:

```bash
~/Android/Sdk/platform-tools/adb install -r dist/json-developer/json-developer-1.0.0-debug.apk
```

```bash
~/Android/Sdk/platform-tools/adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE --es operation set-watchface --es watchFaceId dev.devtime.watchface.json
```

Ou escolha o mostrador manualmente: toque longo na tela → deslize até o fim → "+ Adicionar mostrador".

## Emulador

```bash
~/Android/Sdk/cmdline-tools/latest/bin/avdmanager create avd -n devtime_wear_large_round -k "system-images;android-34;android-wear;x86_64" -d wearos_large_round
```

Ajuste `~/.android/avd/devtime_wear_large_round.avd/config.ini` para `hw.lcd.width=480`, `hw.lcd.height=480`
(resolução do Galaxy Watch 6 44 mm), e inicie:

```bash
~/Android/Sdk/emulator/emulator -avd devtime_wear_large_round -no-snapshot-save
```

Com o emulador rodando, `./build-all.sh screenshots` gera capturas reais de todos os cenários.
