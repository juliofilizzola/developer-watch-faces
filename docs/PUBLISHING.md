# Publicação na Google Play

Três produtos independentes, cada um com seu próprio app no Play Console.

| Produto | Application ID | AAB | Textos | Assets |
|---|---|---|---|---|
| JSON Developer | `dev.devtime.watchface.json` | `dist/json-developer/json-developer-1.0.0-release.aab` | `store-assets/json-developer/listing.md` | `store-assets/json-developer/` |
| Code Developer | `dev.devtime.watchface.code` | `dist/code-developer/code-developer-1.0.0-release.aab` | `store-assets/code-developer/listing.md` | `store-assets/code-developer/` |
| Matrix Developer | `dev.devtime.watchface.matrix` | `dist/matrix-developer/matrix-developer-1.0.0-release.aab` | `store-assets/matrix-developer/listing.md` | `store-assets/matrix-developer/` |

> ⚠️ **Antes de publicar**: confirme se o domínio `devtime.dev` (prefixo `dev.devtime`) é seu. O Application ID
> não pode mudar depois da primeira publicação. Para trocar, altere `namespace`/`applicationId` em cada
> `build.gradle.kts` e `PACKAGE` em `build-all.sh`/`scripts/capture.py`.

> ⚠️ **Marca "Matrix"**: "The Matrix" é marca registrada da Warner Bros. Usar "Matrix" no nome comercial pode
> levar a rejeição por propriedade intelectual. O mostrador não usa personagens, falas, logotipos nem katakana do
> filme, mas o nome ainda é um risco. Alternativas sugeridas: **Digital Rain Developer**, **Rain Code**,
> **Green Code Developer**. O nome exibido vem de `watch_face_name` em `matrix-developer/generator/matrix_face.py`.

## 1. Chave de upload (uma vez)

Gere a chave **você mesmo** (a senha nunca deve ir para o repositório):

```bash
keytool -genkeypair -v -keystore upload-keystore.jks -keyalg RSA -keysize 4096 -validity 10000 -alias devtime-upload
```

Crie `keystore.properties` na raiz (já ignorado pelo Git):

```properties
storeFile=upload-keystore.jks
storePassword=<sua senha>
keyAlias=devtime-upload
keyPassword=<sua senha>
```

Com o arquivo presente, `./build-all.sh` assina os AABs automaticamente (o relatório mostra `signed`).
Guarde a keystore em local seguro: perdê-la exige o processo de redefinição de chave de upload do Play.

## 2. Gerar os AABs

```bash
./build-all.sh
```

Confira `reports/build-report.md`: todas as checagens `PASS` e "AAB upload signature: signed".
Para cada nova versão, incremente `versionCode` e `versionName` no `build.gradle.kts` do módulo.

## 3. Play Console (para cada produto)

1. **Criar app** → nome (de `listing.md`), idioma padrão, *App*, gratuito ou pago.
2. **Configuração → Formatos avançados → Wear OS**: o app é standalone (`com.google.android.wearable.standalone=true`).
3. **Versões → Produção (ou Teste interno) → Criar versão** → envie o `.aab`. Aceite o **Play App Signing**.
   O Play valida o WFF e o consumo de memória do mostrador na revisão.
4. **Presença na loja → Página principal**:
   - Título (≤ 30), descrição curta (≤ 80), descrição completa (≤ 4000) — de `listing.md` (en-US e pt-BR).
   - Ícone: `icon/icon-512.png` (512×512).
   - Feature graphic: `feature-graphic/feature-graphic-1024x500.png`.
   - **Screenshots de Wear OS**: `screenshots/*.png` (480×480, 1:1, sem moldura de relógio, capturas reais).
     Envie-os na seção **Wear OS** (não na de telefone).
   - Os arquivos `promotional/promo-*.png` e `store-assets/collection/` são materiais de divulgação
     (site, redes sociais, anúncios) — **não** os envie como screenshots.
5. **Categoria**: Personalização. Tag: Watch faces.
6. **Segurança dos dados**: o pacote não tem código, não coleta nem compartilha dados → "Nenhum dado coletado".
   Dados de saúde (passos, frequência cardíaca) são lidos e exibidos pelo sistema na própria tela, sem sair do relógio.
7. **Classificação de conteúdo**: questionário → sem conteúdo sensível.
8. **Política de privacidade**: recomendada mesmo sem coleta; publique uma página simples declarando que o mostrador
   não coleta dados e informe a URL.
9. **Público-alvo**: 13+ (ou conforme sua estratégia).
10. Envie para revisão. Recomendado: primeiro um **teste interno** com o Galaxy Watch 6.

## 4. Checklist antes de enviar

- [ ] `./build-all.sh` sem falhas; AAB assinado.
- [ ] Itens pendentes de validação física concluídos (`docs/TESTING.md`, seção "Pendências no Galaxy Watch 6").
- [ ] Application IDs e nome comercial definitivos (atenção à marca "Matrix").
- [ ] Screenshots atualizados se o visual mudou (`./build-all.sh screenshots` + `./build-all.sh assets`).
- [ ] Política de privacidade publicada.
