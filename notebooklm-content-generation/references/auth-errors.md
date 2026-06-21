# NotebookLM Auth Error Signatures

## Token Expired (storage_state.json exists but invalid)

**Symptom**: `notebooklm list --json` returns a 4XX HTTP error with message "Authentication expired or invalid"

**Root cause**: `storage_state.json` exists at the correct path, but the OAuth tokens inside have expired. This is different from Step 0 (file missing/wrong path) — Step 0 copy won't fix it.

**Recognize it by**:
```json
{"error": "Authentication expired or invalid"}
```

## Login Failure (background/non-PTY mode)

**Symptom**: `notebooklm login` exits immediately with:
```
EOFError: EOF when reading a line
```

**Root cause**: `notebooklm login` opens a Chromium browser, waits for `input("Press ENTER...")`, and the prompt hits EOF in background/non-PTY mode.

**Fix**: User must run `notebooklm login` interactively, or the agent must use PTY mode + browser tool for Google OAuth.

## Storage Paths

| Component | Path |
|-----------|------|
| Default auth | `~/.notebooklm/profiles/default/storage_state.json` |
| Hermes profile (her-m2) | `~/.hermes/profiles/her-m2/home/.notebooklm/profiles/default/storage_state.json` |
| Hermes profile (her-m2-profile) | `~/.hermes/profiles/her-m2-profile/home/.notebooklm/profiles/default/storage_state.json` |
| Hermes profile (default) | `~/.hermes/profiles/default/home/.notebooklm/profiles/default/storage_state.json` |
