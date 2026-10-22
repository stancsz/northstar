# Actual desktop host discovery

2026-10-21; bounded read-only worker assignment. No install, rename, hook configuration/trust write, UI/process mutation, provider/model call or probe. Primary owns activation and acceptance. OpenAI Docs skill applied; no delegate or Advisor call was useful for this bounded source/schema lookup.

## Result

The running desktop native executable is `C:/Users/stanc/AppData/Local/OpenAI/Codex/bin/6257d9e8f63c0f2b/codex.exe`. Its actual `--version` is **`codex-cli 0.163.0-alpha.11`**, SHA-256 **`00c0f1e4099246fddcd67ec620ca8ed50827c7d70e113b7224f7a2933cf2d67c`**. Running process executable path was inspected; process arguments, authentication and global configuration values were not printed. Read-only `features list` reports `hooks stable true`; this is the standalone command's effective view, not proof of every setting in the already-running desktop server.

This is distinct from the earlier npm CLI **0.154.0** (`be96b992...`). Its failed probes cannot establish this desktop runtime's activation behavior. Exact 0.163.0-alpha.11 protocol bindings were generated locally by this native binary into `tmp/stop-hook-install/discovery/protocol/`, without starting a model turn or app server.

## Normal supported activation route

Official [Hooks documentation](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks) describes normal `/hooks` review of the exact current declaration before trust. Hook sources can be user or trusted project scopes; matching sources merge, so preserve unrelated configuration and avoid duplicate declarations. A changed command requires new review. Primary reports existing unrelated inline hook state and no hooks.json; this worker did not independently inspect that private configuration. Scope/name questions remain primary-owned.

The actual generated protocol exposes **`hooks/list`**, `config/value/write` and **`config/batchWrite`**. It exposes **no `hooks/update` or dedicated `hooks/trust` method**. [App-server documentation](https://learn.chatgpt.com/docs/app-server) documents hooks discovery and lifecycle notifications. Do not invent a trust RPC name.

Pinned upstream tag `rust-v0.163.0-alpha.11` annotated object `40f4a054d875a76b18a2b733b6224976cf64a826` resolves to commit **`5425d3e625daa58eea3ad1de27c087eb3b2ffbd3`**. [TUI hooks_rpc.rs:24–99](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/tui/src/hooks_rpc.rs) supplies the exact normal review/trust API flow:

1. `hooks/list` with `params:{cwds:["D:/github/northstar"]}`. Review the intended Stop entry's exact command, source/scope, enablement and errors/warnings. Response is `{data:[{cwd,hooks,warnings,errors}]}`. Each hook supplies `key`, `currentHash`, `trustStatus`, `enabled`, `eventName`, `sourcePath`, handler details and managed status.
2. After reviewing that exact entry, the upstream normal TUI invokes `config/batchWrite` with the returned **key and currentHash**, using the shape below. This is the host's own mediated trust workflow, not a hand-authored TOML hash or bypass.
3. Re-list through the intended host: require the same reviewed declaration, `trusted` status and enabled Stop entry, with no load errors. Retain existing state. New/modified definitions must be reviewed again.

```json
{
  "method": "config/batchWrite",
  "params": {
    "edits": [{
      "keyPath": "hooks.state",
      "value": {"<returned-reviewed-key>": {"trusted_hash": "<returned-currentHash>"}},
      "mergeStrategy": "upsert"
    }],
    "filePath": null,
    "expectedVersion": null,
    "reloadUserConfig": true
  }
}
```

Those null version/file fields match the normal upstream TUI; they are not permission to overwrite unrelated state. Native generated `ConfigBatchWriteParams`, `ConfigEdit`, `HookMetadata` and `HookTrustStatus` confirm the field names/types. [Config processor:161–187](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/app-server/src/request_processors/config_processor.rs) applies mutation handling and reloads loaded-thread settings when requested. A different freshly started server's reload does not prove the existing desktop process reloaded; prefer the current host's normal settings/trust interface or its established connection. The exact UI route label was not inspected, so no invented desktop menu path is prescribed.

Native help supplies `app-server proxy --sock <socket>` to proxy stdio to an existing control socket, and `app-server --stdio` for a fresh server. No socket, secret or authenticated endpoint was read or connected here. Current tools expose no general raw app-server RPC method. Primary must establish its supported connection to the actual desktop host before treating an RPC readback/reload as active here; do not restart the app or create a daemon merely to manufacture that proof.

## Why old probes still matter

Preserved 0.154 history: (1) inline CLI hook with ignored user config, no trust; (2) fresh user inline declaration with normal trust rules, no trust state; (3) same declaration/stub reviewed Trusted/[x] through normal `/hooks`, unchanged bytes, still zero stub calls; (4) corrected PowerShell `&` command passed parse-only validation, reviewed normally, still one loopback response, exit 0, no hook lifecycle/stub events. Fourth receipt: `tmp/completion-guardian/qa/host-powershell-probe-2026-10-22T01-13-33-145Z/receipt.json`.

The first two lacked a required trust prerequisite. The latter two mean **neither missing trust nor missing PowerShell call operator alone explains the complete observed failure**. Full pinned 0.154 source tracing preserved CLI/config reload/layer stack through Hooks construction and showed a real Stop callsite; it did not prove the runtime's selected shell or execution status. Zero stub calls can also result from launch failure before the stub, and hooks can fail open. Do not claim no handler attempt, a proven CLI bug, an unsupported desktop feature or a resolved cause.

## Concrete acceptance after primary activation

Use this actual desktop host and a bounded benign Stop declaration to observe the real `hook/started` and `hook/completed` notifications, including status/error entries and selected command/scope. Generated `HookRunSummary` supplies event, handler/execution mode, source, status and entries. The normal hook inventory and run diagnostics distinguish skipped/untrusted/absent declaration from an attempted command failure. No named UI Test command was verified in this source slice.

Then verify one genuine continuation and later allowed stop in the intended desktop thread, plus explicit user-stop behavior and visible reviewer failure. A trusted entry and successful direct script invocation alone are insufficient. Only after that should the real adapter's configured reviewer be considered active; its earlier generic reviewer failure remains separate from hook lifecycle wiring. Manual Guardian review is the currently accepted capability. No automatic enforcement claim is supported by this discovery pass.

Scratch holds generated protocol, exact tagged sources and public tag metadata under `tmp/stop-hook-install/discovery/`; full requests, process args, authentication and private config were not copied. Local native schema/help/source evidence supports the prepared route; it does not assert current activation or product readiness.
