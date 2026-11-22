# toon-shorts-factory

**Free, fully automated YouTube Shorts in paper-cutout cartoon style, for any niche, in any language.**

Your own original characters talk to each other, mouths synced to every word, in front of a new background each scene. A script is written from real facts (checked against Wikipedia), voiced, animated, subtitled and uploaded to your channel, twice a day, with zero paid APIs.

🇧🇷 [Leia em português](#-português)

<p align="center">
  <img src="docs/assets/world-tour-sample.gif" width="270" alt="World Tour Toons sample">
  <img src="docs/assets/frame-danakil.png" width="270" alt="Frame from an episode">
</p>
<p align="center"><img src="docs/assets/cast-world-tour.png" height="200" alt="Cast drawn in code"></p>

## What it does

| Step | How | Cost |
|---|---|---|
| Pick a topic | From your `topics.json`, never repeating recent ones, rotating episode formats | free |
| Get the facts | Wikipedia API (any language) | free |
| Write the script | Pollinations text (LLM) with a strict JSON contract: hook ≤ 9 words, escalating facts, loop or comment question | free |
| Fact check | Every sentence the script relies on must exist in the source article, or the script is rejected and rewritten | free |
| Voices | edge-tts neural voices, one voice per character, with word timings | free |
| Animation | Characters drawn 100% in code (Pillow): lip sync, blinking, gaze, gestures | free |
| Backgrounds | Pollinations Flux in a consistent paper-cutout style, cached; code-drawn fallback offline | free |
| Subtitles | Word-by-word karaoke + on-screen hook text for the first 3 s | free |
| SEO | Real YouTube autocomplete searches feed the title, tags and description | free |
| Upload | YouTube Data API v3 (your own OAuth app, your channel) | free |
| Learn | Reads views of past episodes and logs your top topics and formats | free |

## Why it is built this way (monetization)

YouTube demonetizes channels for **inauthentic content**: mass-produced, template-like or repetitive videos. This project is designed against that:

* a **recurring original cast** with personalities, not a faceless slideshow;
* **real, verifiable facts** with the source credited in every description;
* **rotating formats** (facts, myth vs fact, guess where, could you survive...) so episodes do not look templated;
* **no sensitive personas**: characters never act as financial, medical or legal experts.

Read [docs/monetization.md](docs/monetization.md) before you start. Shorts alone pay little; the doc explains the path that actually reaches the Partner Program.

## Quick start (Windows)

```bat
git clone https://github.com/superaplicativos/toon-shorts-factory
cd toon-shorts-factory
setup_windows.bat
```

The installer puts Python, ffmpeg and every package inside the project folder. Then:

1. **Keys** (both free): create the Google OAuth file and the Pollinations key, see [docs/youtube-setup.md](docs/youtube-setup.md). Save them in `secrets/`.
2. **Your channel**: `toonshorts new my-channel` and edit `channels/my-channel/channel.json` + `topics.json` ([docs/channel-config.md](docs/channel-config.md)). Or let Claude do it with the skill (below).
3. **See your cast**: `toonshorts cast my-channel` creates `cast_preview.png`.
4. **Test without uploading**: `toonshorts preview my-channel`.
5. **Connect YouTube**: create the channel on YouTube first, then `toonshorts authorize my-channel` and pick that channel on Google's screen (add `--paste` if the browser cannot reach localhost).
6. **Private pilot**: `toonshorts pilot my-channel`, then check it in YouTube Studio.
7. **Go daily**: `toonshorts schedule my-channel`. The PC must be on at the scheduled times.

macOS / Linux: `./setup.sh`, then the same commands with `.venv/bin/python -m toonshorts <command>`; `schedule` prints crontab lines.

## Use it with Claude (skill)

The folder [`skill/toon-shorts-channel`](skill/toon-shorts-channel/SKILL.md) is an Agent Skill. Add it to Claude (claude.ai → Settings → Capabilities → Skills, or copy it into your Claude Code skills folder) and say:

> "Create a toon-shorts channel about ___ in ___ language"

Claude interviews you about the niche, designs the cast (looks, voices, personalities), writes the formats and a topic list of 200+ items, renders the cast preview and walks you through authorization, the pilot and scheduling.

## Examples included

| Channel | Niche | Language |
|---|---|---|
| `world-tour-toons` | travel and geography facts, a new place every episode | English |
| `historia-em-1-minuto` | "what if you lived in..." history | Portuguese (BR) |
| `_template` | starting point for `toonshorts new` | English |

<p align="center"><img src="docs/assets/cast-historia.png" height="180" alt="Portuguese example cast"></p>

## Project layout

```
toonshorts/          the engine (pipeline, animation, characters, free AI providers, YouTube)
channels/<slug>/     one folder per channel: channel.json, topics.json, history.json, output/
secrets/             your keys (git-ignored)
skill/               Claude skill that builds a channel with you
docs/                setup, config reference, monetization, troubleshooting
```

## Commands

| Command | What |
|---|---|
| `toonshorts list` | list channels |
| `toonshorts new <slug> [--from <other>]` | create a channel from the template or another channel |
| `toonshorts cast <slug>` | render the cast preview |
| `toonshorts check [<slug>]` | check tools, keys and YouTube connection |
| `toonshorts authorize <slug> [--paste]` | connect the YouTube channel (once) |
| `toonshorts preview <slug>` | make one video, no upload |
| `toonshorts pilot <slug>` | make one video and upload it as private |
| `toonshorts run <slug> [--private] [--force]` | the daily job |
| `toonshorts schedule <slug>` | daily tasks (Windows) or crontab lines |

## Hard-won lessons (already handled)

* On some Windows ffmpeg builds, piping frames + audio + subtitles in one pass, or using `loudnorm`, **hangs forever**. Rendering is two-pass and uses `volume + alimiter`.
* Child ffmpeg processes must get `-nostdin`, or they can block on the console.
* edge-tts sometimes answers "No audio was received" for no reason; every line is retried.
* Google's OAuth redirect to localhost does not always fire in embedded browsers; `authorize --paste` solves it.
* Unverified Google Cloud apps may get uploads locked as private until the app passes the audit. See [docs/youtube-setup.md](docs/youtube-setup.md).

More in [docs/troubleshooting.md](docs/troubleshooting.md).

## License

MIT for the code. Facts come from Wikipedia under CC BY-SA 4.0 and are credited in each video description. You are responsible for following YouTube's policies on your channel.

---

## 🇧🇷 Português

**Shorts do YouTube em desenho animado estilo papel recortado, 100% automáticos e gratuitos, para qualquer nicho e em qualquer idioma.**

Os seus próprios personagens originais conversam entre si, com a boca sincronizada a cada palavra, na frente de um cenário diferente em cada cena. O roteiro é escrito a partir de fatos reais (conferidos na Wikipedia), ganha voz, animação e legenda, e é publicado no seu canal duas vezes por dia, sem nenhuma API paga.

🇺🇸 [Read in English](#toon-shorts-factory)

<p align="center"><img src="docs/assets/cast-historia.png" height="200" alt="Elenco desenhado em código"></p>

### O que ele faz

| Etapa | Como | Custo |
|---|---|---|
| Escolhe o tema | Do seu `topics.json`, sem repetir os recentes e alternando formatos de episódio | grátis |
| Busca os fatos | API da Wikipedia (qualquer idioma) | grátis |
| Escreve o roteiro | IA de texto do Pollinations com contrato JSON rígido: gancho de até 9 palavras, fatos em escalada, final em loop ou pergunta para os comentários | grátis |
| Checa os fatos | Toda frase em que o roteiro se apoia precisa existir no artigo de origem, senão o roteiro é reprovado e reescrito | grátis |
| Vozes | Vozes neurais do edge-tts, uma voz para cada personagem, com o tempo de cada palavra | grátis |
| Animação | Personagens desenhados 100% em código (Pillow): sincronia labial, piscadas, olhar e gestos | grátis |
| Cenários | Pollinations Flux num estilo de papel recortado consistente, com cache e cenário desenhado por código quando está sem internet | grátis |
| Legendas | Karaokê palavra por palavra e texto de gancho na tela nos 3 primeiros segundos | grátis |
| SEO | Buscas reais do autocompletar do YouTube alimentam título, tags e descrição | grátis |
| Publicação | YouTube Data API v3 (seu próprio app OAuth, seu canal) | grátis |
| Aprendizado | Lê as views dos episódios anteriores e registra os temas e formatos que mais rendem | grátis |

### Por que é feito assim (monetização)

O YouTube tira a monetização de canais com **conteúdo inautêntico**, ou seja, vídeos produzidos em massa, com cara de molde ou repetitivos. Este projeto foi desenhado contra isso. Ele usa um **elenco original e fixo**, com personalidade, e não um slideshow sem rosto. Usa **fatos reais e verificáveis**, com a fonte creditada em toda descrição. **Alterna formatos** (fatos, mito ou verdade, adivinhe onde estamos, você sobreviveria...) para os episódios não parecerem feitos em série. E **nenhum personagem se passa por especialista** em finanças, saúde ou direito.

Leia o [docs/monetization.md](docs/monetization.md) antes de começar. Shorts sozinhos pagam pouco, e o documento explica o caminho que de fato chega ao Programa de Parcerias.

### Começo rápido (Windows)

```bat
git clone https://github.com/superaplicativos/toon-shorts-factory
cd toon-shorts-factory
setup_windows.bat
```

O instalador coloca Python, ffmpeg e todos os pacotes dentro da própria pasta do projeto. Depois:

1. **Chaves** (as duas grátis): crie o arquivo OAuth do Google e a chave do Pollinations seguindo o [docs/youtube-setup.md](docs/youtube-setup.md). Salve as duas em `secrets/`.
2. **Seu canal**: rode `toonshorts new meu-canal` e edite `channels/meu-canal/channel.json` e `topics.json` ([docs/channel-config.md](docs/channel-config.md)). Ou deixe o Claude fazer isso com a skill (veja abaixo).
3. **Veja o elenco**: `toonshorts cast meu-canal` gera o `cast_preview.png`.
4. **Teste sem publicar**: `toonshorts preview meu-canal`.
5. **Conecte o YouTube**: crie o canal no YouTube primeiro, depois rode `toonshorts authorize meu-canal` e escolha esse canal na tela do Google. Se o navegador não conseguir abrir o localhost, acrescente `--paste`.
6. **Piloto privado**: `toonshorts pilot meu-canal`, e confira o vídeo no YouTube Studio.
7. **Rodando todo dia**: `toonshorts schedule meu-canal`. O PC precisa estar ligado nos horários agendados.

No macOS ou Linux, rode `./setup.sh` e depois os mesmos comandos com `.venv/bin/python -m toonshorts <comando>`. O `schedule` mostra as linhas para o crontab.

### Usando com o Claude (skill)

A pasta [`skill/toon-shorts-channel`](skill/toon-shorts-channel/SKILL.md) é uma Skill de agente. Adicione ao Claude (claude.ai → Configurações → Capacidades → Skills, ou copie para a pasta de skills do Claude Code) e diga:

> "Crie um canal toon-shorts sobre ___ em ___"

O Claude entrevista você sobre o nicho, cria o elenco (visual, vozes e personalidades), escreve os formatos e uma lista com mais de 200 temas, gera a prévia do elenco e acompanha você na autorização, no piloto e no agendamento.

### Exemplos incluídos

| Canal | Nicho | Idioma |
|---|---|---|
| `world-tour-toons` | fatos de viagem e geografia, um lugar novo por episódio | inglês |
| `historia-em-1-minuto` | história no formato "e se você vivesse em..." | português |
| `_template` | ponto de partida do `toonshorts new` | inglês |

### Estrutura

```
toonshorts/          o motor (pipeline, animação, personagens, IAs grátis, YouTube)
channels/<slug>/     uma pasta por canal: channel.json, topics.json, history.json, output/
secrets/             suas chaves (fora do git)
skill/               skill do Claude que monta o canal com você
docs/                instalação, referência de configuração, monetização, problemas comuns
```

### Comandos

| Comando | O que faz |
|---|---|
| `toonshorts list` | lista os canais |
| `toonshorts new <slug> [--from <outro>]` | cria um canal a partir do modelo ou de outro canal |
| `toonshorts cast <slug>` | gera a prévia do elenco |
| `toonshorts check [<slug>]` | confere ferramentas, chaves e a conexão com o YouTube |
| `toonshorts authorize <slug> [--paste]` | conecta o canal do YouTube (uma vez só) |
| `toonshorts preview <slug>` | gera um vídeo sem publicar |
| `toonshorts pilot <slug>` | gera um vídeo e publica como privado |
| `toonshorts run <slug> [--private] [--force]` | a tarefa diária |
| `toonshorts schedule <slug>` | cria as tarefas diárias no Windows ou mostra as linhas do crontab |

### Lições aprendidas (já resolvidas no código)

* Em alguns builds do ffmpeg para Windows, mandar quadros, áudio e legendas numa passada só, ou usar o filtro `loudnorm`, **trava para sempre**. Por isso a renderização é feita em duas passadas e o volume usa `volume + alimiter`.
* Os processos do ffmpeg precisam do `-nostdin`, senão podem ficar presos no console.
* O edge-tts às vezes responde "No audio was received" sem motivo. Toda fala é tentada de novo.
* O redirecionamento do OAuth do Google para o localhost nem sempre dispara em navegadores embutidos. O `authorize --paste` resolve.
* Apps do Google Cloud não verificados podem ter os uploads travados como privados até passar pela auditoria. Veja o [docs/youtube-setup.md](docs/youtube-setup.md).

Mais detalhes em [docs/troubleshooting.md](docs/troubleshooting.md).

### Licença

O código é MIT. Os fatos vêm da Wikipedia sob CC BY-SA 4.0 e são creditados na descrição de cada vídeo. Seguir as políticas do YouTube no seu canal é responsabilidade sua.
