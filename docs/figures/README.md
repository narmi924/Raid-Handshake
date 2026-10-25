# Architecture and raid sequence figures

These figures describe the implemented application. They are documentation, not substituted
demo footage or measured latency charts. The [real demo recording script](../DEMO_SCRIPT.md)
covers the Twitch evidence to capture.

| View | Editable source | Display / export | Code provenance |
| --- | --- | --- | --- |
| Runtime deployment | [architecture.drawio](architecture/architecture.drawio) | [SVG](architecture/architecture.svg), [2× PNG](architecture/architecture.png), [PDF](architecture/architecture.pdf) | [Brief and source map](architecture/brief.md), [generator](architecture/gen.py) |
| Default manual-send raid sequence | [raid-sequence.drawio](raid-sequence/raid-sequence.drawio) | [SVG](raid-sequence/raid-sequence.svg), [2× PNG](raid-sequence/raid-sequence.png), [PDF](raid-sequence/raid-sequence.pdf) | [Brief and source map](raid-sequence/brief.md), [generator](raid-sequence/gen.py) |

The architecture is a deployment view: a local Windows boundary, the two external APIs and
separate studio/OBS surfaces. The sequence is an ordering view: default manual confirmation,
parallel card preparation and observation windows. It does not promise network latency or
claim that chat connections identify raid members or video viewers.

## Editing and regeneration

Open the `.drawio` files in draw.io to edit their native shapes and connectors. They are the
editable deliverables. If you edit them by hand, preserve those edits before re-running a
generator, which otherwise overwrites the export.

The generators use the author's local **paper-figures** workbench. That optional drawing tool
is not needed to install or run Raid Handshake. From the project root, on the author's machine:

```powershell
Get-Content E:/Projects/UniBuni/paper-figures/config/taste.md
pwsh -NoProfile -File E:/Projects/UniBuni/paper-figures/fig.ps1 build docs/figures/architecture/gen.py --look readme
Get-Content E:/Projects/UniBuni/paper-figures/config/taste.md
pwsh -NoProfile -File E:/Projects/UniBuni/paper-figures/fig.ps1 build docs/figures/raid-sequence/gen.py --look readme
pwsh -NoProfile -File E:/Projects/UniBuni/paper-figures/fig.ps1 show docs/figures/architecture/architecture.svg --width 920
pwsh -NoProfile -File E:/Projects/UniBuni/paper-figures/fig.ps1 show docs/figures/raid-sequence/raid-sequence.svg --width 920
```

Each export includes the native draw.io source, static SVG, 2× PNG, vector PDF and geometry
metadata. The tool's local `.look` inspection images are ignored by Git. Both figures target
a GitHub display width of approximately 920 px. Source tables list the functions behind every
node and relationship; re-check those tables when behavior changes.

## Asset credits

Twitch, OBS Studio and FastAPI marks are from [Simple Icons](https://simpleicons.org/), whose
icon collection uses [CC0](https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md).
The marks identify the real integrations and belong to their respective owners. The Raid
Handshake mark is the same SVG path used in `frontend/src/studio.ts`.

Inter is used to match the interface. Its embedded export font is covered by the
[SIL Open Font License](INTER-LICENSE.txt), copied from the
[Google Fonts Inter distribution](https://github.com/google/fonts/blob/main/ofl/inter/OFL.txt).
No proprietary Roobert font is included.
