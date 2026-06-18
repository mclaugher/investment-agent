# Vendored skills — Matt Pocock's "Skills For Real Engineers"

The 17 skill folders in this directory are vendored from
[`mattpocock/skills`](https://github.com/mattpocock/skills) (the official plugin
set, flattened from its `engineering/` and `productivity/` groupings). They are
included here so they are committed, work immediately, and travel with the repo —
rather than installed via the interactive `npx skills@latest add mattpocock/skills`
flow, which assumes a local agent and prompts.

To update: re-clone the upstream repo and re-copy the folders listed in its
`.claude-plugin/plugin.json`.

## First-time setup

Several engineering skills (`/triage`, `/to-issues`, `/to-prd`) expect a
configured issue tracker and domain-doc layout. Run **`/setup-matt-pocock-skills`**
once to configure them for this repo (issue tracker, triage labels, doc location).

## License & attribution

These skills are © 2026 Matt Pocock, distributed under the MIT License, reproduced
below per its terms. They are unmodified vendored copies; our own first-party
skills/commands live in `.claude/commands/` and are not covered by this notice.

```
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
