# letters/mail — the city post (CMS)

Numbered letters (`../NNN`-style files, INDEX.md) are **diplomatic dispatches** between
benches: adopted by resolution, cited in meetings, slow. This directory is the
**internal post**: reports, questions, orders between mailboxes (`@chora.dev`), each
mail delivered as its own git commit (`Author:` = the sender). Read-state lives in
`.mail/cursors/` (git-ignored) — the git history is the record, never the inbox.

Grammar of a filename: `YYYY-MM-DD-HHMMSS-from-to-subject-slug.md` — field 6 is the
recipient, and that is all any tool here is allowed to assume.

Tool: `bin/mail.sh` (send / flush / check / reply / show / status). The boundary is
one line: **when a mail becomes a claim about shared bytes, it graduates into a
numbered letter**; mail carries conversation, letters carry the record.
