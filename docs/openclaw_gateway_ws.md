# OpenClaw Gateway WebSocket Protocol

This document describes how to interact with the OpenClaw Gateway over WebSocket. It is intended for humans and LLMs and includes frame formats, auth/scopes, events, and all known methods with params and response payloads.

Protocol version: `3`
Default URL: `ws://127.0.0.1:18789`

All timestamps are milliseconds since Unix epoch unless noted.

## Connection Lifecycle

1. Open a WebSocket connection to the gateway.
2. Server immediately sends an `event` frame named `connect.challenge` with a nonce.
3. Client must send a `req` frame with `method: "connect"` and `params: ConnectParams` as the first request.
4. Server responds with a `res` frame whose `payload` is a `HelloOk` object.

If `connect` is not the first request, the server returns an error.

### Connect Challenge

Event payload:

```ts
type ConnectChallenge = { nonce: string; ts: number };
```

If you provide `device.nonce` in `connect`, it must match this `nonce`.

## Frame Formats

```ts
type RequestFrame = {
  type: "req";
  id: string; // client-generated
  method: string;
  params?: unknown;
};

type ResponseFrame = {
  type: "res";
  id: string; // matches RequestFrame.id
  ok: boolean;
  payload?: unknown;
  error?: ErrorShape;
};

type EventFrame = {
  type: "event";
  event: string;
  payload?: unknown;
  seq?: number; // optional event sequence counter
  stateVersion?: { presence: number; health: number };
};
```

### Error Shape

```ts
type ErrorShape = {
  code: string;
  message: string;
  details?: unknown;
  retryable?: boolean;
  retryAfterMs?: number;
};
```

Known error codes include:
`NOT_LINKED`, `NOT_PAIRED`, `AGENT_TIMEOUT`, `INVALID_REQUEST`, `UNAVAILABLE`.

## Connect Params and HelloOk

```ts
type ConnectParams = {
  minProtocol: number;
  maxProtocol: number;
  client: {
    id: "webchat-ui" | "openclaw-control-ui" | "webchat" | "cli" | "gateway-client" | "openclaw-macos" | "openclaw-ios" | "openclaw-android" | "node-host" | "test" | "fingerprint" | "openclaw-probe";
    displayName?: string;
    version: string;
    platform: string;
    deviceFamily?: string;
    modelIdentifier?: string;
    mode: "webchat" | "cli" | "ui" | "backend" | "node" | "probe" | "test";
    instanceId?: string;
  };
  caps?: string[];
  commands?: string[];
  permissions?: Record<string, boolean>;
  pathEnv?: string;
  role?: string; // default "operator"
  scopes?: string[];
  device?: {
    id: string;
    publicKey: string;
    signature: string;
    signedAt: number;
    nonce?: string;
  };
  auth?: {
    token?: string;
    password?: string;
  };
  locale?: string;
  userAgent?: string;
};
```

Notes:
- `minProtocol`/`maxProtocol` must include `3` (the server's expected protocol).
- If you send `device.nonce`, it must match the `connect.challenge` nonce.

```ts
type HelloOk = {
  type: "hello-ok";
  protocol: number;
  server: {
    version: string;
    commit?: string;
    host?: string;
    connId: string;
  };
  features: {
    methods: string[]; // advertised methods
    events: string[];  // advertised events
  };
  snapshot: Snapshot;
  canvasHostUrl?: string;
  auth?: {
    deviceToken: string;
    role: string;
    scopes: string[];
    issuedAtMs?: number;
  };
  policy: {
    maxPayload: number;
    maxBufferedBytes: number;
    tickIntervalMs: number;
  };
};
```

## Auth, Roles, and Scopes

Gateway methods are authorized by role + scopes set during `connect`.

Roles:
`operator` (default) and `node`.

Scopes:
`operator.read`, `operator.write`, `operator.admin`, `operator.pairing`, `operator.approvals`.

Notes:
- `node` role can only call `node.invoke.result`, `node.event`, `skills.bins`.
- `operator.admin` is required for config, wizard, update, and several maintenance methods.
- If a method is not explicitly read/write/pairing/approvals, it generally requires `operator.admin`.

## Idempotency

The following methods require `idempotencyKey` in params and dedupe repeated requests:
`send`, `poll`, `agent`, `chat.send`, `node.invoke`.

For `send`, `poll`, `agent`, and `chat.send` the `idempotencyKey` is used as the `runId` in responses/events.

## Common Types

```ts
type Snapshot = {
  presence: PresenceEntry[];
  health: HealthSummary;
  stateVersion: { presence: number; health: number };
  uptimeMs: number;
  configPath?: string;
  stateDir?: string;
  sessionDefaults?: {
    defaultAgentId: string;
    mainKey: string;
    mainSessionKey: string;
    scope?: string;
  };
};

type PresenceEntry = {
  host?: string;
  ip?: string;
  version?: string;
  platform?: string;
  deviceFamily?: string;
  modelIdentifier?: string;
  mode?: string;
  lastInputSeconds?: number;
  reason?: string;
  tags?: string[];
  text?: string;
  ts: number;
  deviceId?: string;
  roles?: string[];
  scopes?: string[];
  instanceId?: string;
};
```

Health summary (used by `health` method and `health` event):

```ts
type HealthSummary = {
  ok: true;
  ts: number;
  durationMs: number;
  channels: Record<string, ChannelHealthSummary>;
  channelOrder: string[];
  channelLabels: Record<string, string>;
  heartbeatSeconds: number;
  defaultAgentId: string;
  agents: AgentHealthSummary[];
  sessions: {
    path: string;
    count: number;
    recent: Array<{ key: string; updatedAt: number | null; age: number | null }>;
  };
};
```

Status summary (used by `status` method):

```ts
type StatusSummary = {
  linkChannel?: { id: string; label: string; linked: boolean; authAgeMs: number | null };
  heartbeat: { defaultAgentId: string; agents: HeartbeatStatus[] };
  channelSummary: string[];
  queuedSystemEvents: string[];
  sessions: {
    paths: string[];
    count: number;
    defaults: { model: string | null; contextTokens: number | null };
    recent: SessionStatus[];
    byAgent: Array<{ agentId: string; path: string; count: number; recent: SessionStatus[] }>;
  };
};
```

Usage summaries:

```ts
type UsageSummary = {
  updatedAt: number;
  providers: Array<{
    provider: string;
    displayName: string;
    windows: Array<{ label: string; usedPercent: number; resetAt?: number }>;
    plan?: string;
    error?: string;
  }>;
};

type CostUsageSummary = {
  updatedAt: number;
  days: number;
  daily: Array<{ date: string; input: number; output: number; cacheRead: number; cacheWrite: number; totalTokens: number; totalCost: number; missingCostEntries: number }>;
  totals: { input: number; output: number; cacheRead: number; cacheWrite: number; totalTokens: number; totalCost: number; missingCostEntries: number };
};
```

Heartbeat event payload (used by `heartbeat` event and `last-heartbeat` method):

```ts
type HeartbeatEventPayload = {
  ts: number;
  status: "sent" | "ok-empty" | "ok-token" | "skipped" | "failed";
  to?: string;
  preview?: string;
  durationMs?: number;
  hasMedia?: boolean;
  reason?: string;
  channel?: string;
  silent?: boolean;
  indicatorType?: "ok" | "alert" | "error";
};
```

Chat and agent events:

```ts
type AgentEvent = {
  runId: string;
  seq: number;
  stream: string;
  ts: number;
  data: Record<string, unknown>;
};

type ChatEvent = {
  runId: string;
  sessionKey: string;
  seq: number;
  state: "delta" | "final" | "aborted" | "error";
  message?: unknown;
  errorMessage?: string;
  usage?: unknown;
  stopReason?: string;
};
```

Cron types:

```ts
type CronSchedule =
  | { kind: "at"; at: string }
  | { kind: "every"; everyMs: number; anchorMs?: number }
  | { kind: "cron"; expr: string; tz?: string };

type CronPayload =
  | { kind: "systemEvent"; text: string }
  | { kind: "agentTurn"; message: string; model?: string; thinking?: string; timeoutSeconds?: number };

type CronDelivery = { mode: "none" | "announce"; channel?: "last" | string; to?: string; bestEffort?: boolean };

type CronJob = {
  id: string;
  agentId?: string;
  name: string;
  description?: string;
  enabled: boolean;
  deleteAfterRun?: boolean;
  createdAtMs: number;
  updatedAtMs: number;
  schedule: CronSchedule;
  sessionTarget: "main" | "isolated";
  wakeMode: "next-heartbeat" | "now";
  payload: CronPayload;
  delivery?: CronDelivery;
  state: {
    nextRunAtMs?: number;
    runningAtMs?: number;
    lastRunAtMs?: number;
    lastStatus?: "ok" | "error" | "skipped";
    lastError?: string;
    lastDurationMs?: number;
  };
};

type CronEvent = {
  jobId: string;
  action: "added" | "updated" | "removed" | "started" | "finished";
  runAtMs?: number;
  durationMs?: number;
  status?: "ok" | "error" | "skipped";
  error?: string;
  summary?: string;
  nextRunAtMs?: number;
};
```

Node and device pairing types:

```ts
type NodePairingPendingRequest = {
  requestId: string;
  nodeId: string;
  displayName?: string;
  platform?: string;
  version?: string;
  coreVersion?: string;
  uiVersion?: string;
  deviceFamily?: string;
  modelIdentifier?: string;
  caps?: string[];
  commands?: string[];
  permissions?: Record<string, boolean>;
  remoteIp?: string;
  silent?: boolean;
  isRepair?: boolean;
  ts: number;
};

type NodePairingPairedNode = {
  nodeId: string;
  token: string;
  displayName?: string;
  platform?: string;
  version?: string;
  coreVersion?: string;
  uiVersion?: string;
  deviceFamily?: string;
  modelIdentifier?: string;
  caps?: string[];
  commands?: string[];
  bins?: string[];
  permissions?: Record<string, boolean>;
  remoteIp?: string;
  createdAtMs: number;
  approvedAtMs: number;
  lastConnectedAtMs?: number;
};

type DevicePairingPendingRequest = {
  requestId: string;
  deviceId: string;
  publicKey: string;
  displayName?: string;
  platform?: string;
  clientId?: string;
  clientMode?: string;
  role?: string;
  roles?: string[];
  scopes?: string[];
  remoteIp?: string;
  silent?: boolean;
  isRepair?: boolean;
  ts: number;
};

type PairedDevice = {
  deviceId: string;
  publicKey: string;
  displayName?: string;
  platform?: string;
  clientId?: string;
  clientMode?: string;
  role?: string;
  roles?: string[];
  scopes?: string[];
  remoteIp?: string;
  tokens?: Record<string, { role: string; scopes: string[]; createdAtMs: number; rotatedAtMs?: number; revokedAtMs?: number; lastUsedAtMs?: number }>;
  createdAtMs: number;
  approvedAtMs: number;
};
```

Sessions list/preview results:

```ts
type SessionsListResult = {
  ts: number;
  path: string;
  count: number;
  defaults: { modelProvider: string | null; model: string | null; contextTokens: number | null };
  sessions: Array<{
    key: string;
    kind: "direct" | "group" | "global" | "unknown";
    label?: string;
    displayName?: string;
    derivedTitle?: string;
    lastMessagePreview?: string;
    channel?: string;
    subject?: string;
    groupChannel?: string;
    space?: string;
    chatType?: string;
    origin?: unknown;
    updatedAt: number | null;
    sessionId?: string;
    systemSent?: boolean;
    abortedLastRun?: boolean;
    thinkingLevel?: string;
    verboseLevel?: string;
    reasoningLevel?: string;
    elevatedLevel?: string;
    sendPolicy?: "allow" | "deny";
    inputTokens?: number;
    outputTokens?: number;
    totalTokens?: number;
    responseUsage?: "on" | "off" | "tokens" | "full";
    modelProvider?: string;
    model?: string;
    contextTokens?: number;
    deliveryContext?: unknown;
    lastChannel?: string;
    lastTo?: string;
    lastAccountId?: string;
  }>;
};

type SessionsPreviewResult = {
  ts: number;
  previews: Array<{
    key: string;
    status: "ok" | "empty" | "missing" | "error";
    items: Array<{ role: "user" | "assistant" | "tool" | "system" | "other"; text: string }>;
  }>;
};
```

## Events

The gateway may emit these events. Payloads use the types above.

- `connect.challenge`: `ConnectChallenge`
- `agent`: `AgentEvent`
- `chat`: `ChatEvent`
- `presence`: `{ presence: PresenceEntry[] }`
- `tick`: `{ ts: number }`
- `talk.mode`: `{ enabled: boolean; phase: string | null; ts: number }`
- `shutdown`: `{ reason: string; restartExpectedMs?: number }`
- `health`: `HealthSummary`
- `heartbeat`: `HeartbeatEventPayload`
- `cron`: `CronEvent`
- `node.pair.requested`: `NodePairingPendingRequest`
- `node.pair.resolved`: `{ requestId: string; nodeId: string; decision: "approved" | "rejected"; ts: number }`
- `node.invoke.request`: `{ id: string; nodeId: string; command: string; paramsJSON?: string; timeoutMs?: number; idempotencyKey?: string }`
- `device.pair.requested`: `DevicePairingPendingRequest`
- `device.pair.resolved`: `{ requestId: string; deviceId: string; decision: string; ts: number }`
- `voicewake.changed`: `{ triggers: string[] }`
- `exec.approval.requested`: `{ id: string; request: { command: string; cwd?: string | null; host?: string | null; security?: string | null; ask?: string | null; agentId?: string | null; resolvedPath?: string | null; sessionKey?: string | null }; createdAtMs: number; expiresAtMs: number }`
- `exec.approval.resolved`: `{ id: string; decision: "allow-once" | "allow-always" | "deny"; resolvedBy?: string; ts: number }`

## Method Reference

### Health and Status

#### `health`
Params:
```ts
{ probe?: boolean }
```
Response:
`HealthSummary`
Notes: Uses cached health unless `probe: true`.

#### `status`
Params:
```ts
{}
```
Response:
`StatusSummary`

#### `usage.status`
Params:
```ts
{}
```
Response:
`UsageSummary`

#### `usage.cost`
Params:
```ts
{ days?: number }
```
Response:
`CostUsageSummary`

#### `last-heartbeat`
Params:
```ts
{}
```
Response:
`HeartbeatEventPayload | null`

#### `set-heartbeats`
Params:
```ts
{ enabled: boolean }
```
Response:
```ts
{ ok: true; enabled: boolean }
```
Scope: `operator.admin`

#### `system-presence`
Params:
```ts
{}
```
Response:
`PresenceEntry[]`

#### `system-event`
Params:
```ts
{
  text: string;
  deviceId?: string;
  instanceId?: string;
  host?: string;
  ip?: string;
  mode?: string;
  version?: string;
  platform?: string;
  deviceFamily?: string;
  modelIdentifier?: string;
  lastInputSeconds?: number;
  reason?: string;
  roles?: string[];
  scopes?: string[];
  tags?: string[];
}
```
Response:
```ts
{ ok: true }
```
Scope: `operator.admin`

### Logs

#### `logs.tail`
Params:
```ts
{ cursor?: number; limit?: number; maxBytes?: number }
```
Response:
```ts
{ file: string; cursor: number; size: number; lines: string[]; truncated?: boolean; reset?: boolean }
```

### Channels

#### `channels.status`
Params:
```ts
{ probe?: boolean; timeoutMs?: number }
```
Response:
```ts
{
  ts: number;
  channelOrder: string[];
  channelLabels: Record<string, string>;
  channelDetailLabels?: Record<string, string>;
  channelSystemImages?: Record<string, string>;
  channelMeta?: Array<{ id: string; label: string; detailLabel: string; systemImage?: string }>;
  channels: Record<string, unknown>; // plugin summaries
  channelAccounts: Record<string, Array<{
    accountId: string;
    name?: string;
    enabled?: boolean;
    configured?: boolean;
    linked?: boolean;
    running?: boolean;
    connected?: boolean;
    reconnectAttempts?: number;
    lastConnectedAt?: number;
    lastError?: string;
    lastStartAt?: number;
    lastStopAt?: number;
    lastInboundAt?: number;
    lastOutboundAt?: number;
    lastProbeAt?: number;
    mode?: string;
    dmPolicy?: string;
    allowFrom?: string[];
    tokenSource?: string;
    botTokenSource?: string;
    appTokenSource?: string;
    baseUrl?: string;
    allowUnmentionedGroups?: boolean;
    cliPath?: string | null;
    dbPath?: string | null;
    port?: number | null;
    probe?: unknown;
    audit?: unknown;
    application?: unknown;
    [key: string]: unknown;
  }>>;
  channelDefaultAccountId: Record<string, string>;
}
```

#### `channels.logout`
Params:
```ts
{ channel: string; accountId?: string }
```
Response:
```ts
{ channel: string; accountId: string; cleared: boolean; [key: string]: unknown }
```
Scope: `operator.admin`

#### `web.login.start` (plugin-provided)
Params:
```ts
{ force?: boolean; timeoutMs?: number; verbose?: boolean; accountId?: string }
```
Response: provider-specific, typically includes QR or login URL.

#### `web.login.wait` (plugin-provided)
Params:
```ts
{ timeoutMs?: number; accountId?: string }
```
Response: provider-specific, typically `{ connected: boolean; ... }`.

### TTS

#### `tts.status`
Params:
```ts
{}
```
Response:
```ts
{
  enabled: boolean;
  auto: boolean | string;
  provider: "openai" | "elevenlabs" | "edge";
  fallbackProvider: string | null;
  fallbackProviders: string[];
  prefsPath: string;
  hasOpenAIKey: boolean;
  hasElevenLabsKey: boolean;
  edgeEnabled: boolean;
}
```

#### `tts.providers`
Params:
```ts
{}
```
Response:
```ts
{ providers: Array<{ id: string; name: string; configured: boolean; models: string[]; voices?: string[] }>; active: string }
```

#### `tts.enable`
Params:
```ts
{}
```
Response:
```ts
{ enabled: true }
```

#### `tts.disable`
Params:
```ts
{}
```
Response:
```ts
{ enabled: false }
```

#### `tts.convert`
Params:
```ts
{ text: string; channel?: string }
```
Response:
```ts
{ audioPath: string; provider: string; outputFormat: string; voiceCompatible: boolean }
```

#### `tts.setProvider`
Params:
```ts
{ provider: "openai" | "elevenlabs" | "edge" }
```
Response:
```ts
{ provider: string }
```

### Config and Update

#### `config.get`
Params:
```ts
{}
```
Response:
```ts
{ path: string; exists: boolean; raw: string | null; parsed: unknown; valid: boolean; config: unknown; hash?: string; issues: Array<{ path: string; message: string }>; warnings: Array<{ path: string; message: string }>; legacyIssues: Array<{ path: string; message: string }> }
```

#### `config.schema`
Params:
```ts
{}
```
Response:
```ts
{ schema: unknown; uiHints: Record<string, { label?: string; help?: string; group?: string; order?: number; advanced?: boolean; sensitive?: boolean; placeholder?: string; itemTemplate?: unknown }>; version: string; generatedAt: string }
```

#### `config.set`
Params:
```ts
{ raw: string; baseHash?: string }
```
Response:
```ts
{ ok: true; path: string; config: unknown }
```
Notes: `baseHash` is required if a config already exists.

#### `config.patch`
Params:
```ts
{ raw: string; baseHash?: string; sessionKey?: string; note?: string; restartDelayMs?: number }
```
Response:
```ts
{ ok: true; path: string; config: unknown; restart: unknown; sentinel: { path: string | null; payload: unknown } }
```
Notes: `raw` must be a JSON object for merge patch. Requires `baseHash` if config exists.

#### `config.apply`
Params:
```ts
{ raw: string; baseHash?: string; sessionKey?: string; note?: string; restartDelayMs?: number }
```
Response:
```ts
{ ok: true; path: string; config: unknown; restart: unknown; sentinel: { path: string | null; payload: unknown } }
```
Notes: Requires `baseHash` if config exists.

#### `update.run`
Params:
```ts
{ sessionKey?: string; note?: string; restartDelayMs?: number; timeoutMs?: number }
```
Response:
```ts
{ ok: true; result: { status: "ok" | "error"; mode: string; reason?: string; root?: string; before?: string | null; after?: string | null; steps: Array<{ name: string; command: string; cwd: string; durationMs: number; stdoutTail?: string | null; stderrTail?: string | null; exitCode?: number | null }>; durationMs: number }; restart: unknown; sentinel: { path: string | null; payload: unknown } }
```
Scope: `operator.admin`

### Exec Approvals

#### `exec.approvals.get`
Params:
```ts
{}
```
Response:
```ts
{ path: string; exists: boolean; hash: string; file: { version: 1; socket?: { path?: string }; defaults?: { security?: string; ask?: string; askFallback?: string; autoAllowSkills?: boolean }; agents?: Record<string, { security?: string; ask?: string; askFallback?: string; autoAllowSkills?: boolean; allowlist?: Array<{ id?: string; pattern: string; lastUsedAt?: number; lastUsedCommand?: string; lastResolvedPath?: string }> }> } }
```

#### `exec.approvals.set`
Params:
```ts
{ file: ExecApprovalsFile; baseHash?: string }
```
Response:
Same shape as `exec.approvals.get`.
Notes: `baseHash` required if file exists.

#### `exec.approvals.node.get`
Params:
```ts
{ nodeId: string }
```
Response:
Node-provided exec approvals snapshot for that node.

#### `exec.approvals.node.set`
Params:
```ts
{ nodeId: string; file: ExecApprovalsFile; baseHash?: string }
```
Response:
Node-provided exec approvals snapshot after update.

#### `exec.approval.request`
Params:
```ts
{ id?: string; command: string; cwd?: string | null; host?: string | null; security?: string | null; ask?: string | null; agentId?: string | null; resolvedPath?: string | null; sessionKey?: string | null; timeoutMs?: number }
```
Response:
```ts
{ id: string; decision: "allow-once" | "allow-always" | "deny"; createdAtMs: number; expiresAtMs: number }
```
Notes: This method blocks until a decision is made or timeout occurs.

#### `exec.approval.resolve`
Params:
```ts
{ id: string; decision: "allow-once" | "allow-always" | "deny" }
```
Response:
```ts
{ ok: true }
```

### Wizard

#### `wizard.start`
Params:
```ts
{ mode?: "local" | "remote"; workspace?: string }
```
Response:
```ts
{ sessionId: string; done: boolean; step?: WizardStep; status?: "running" | "done" | "cancelled" | "error"; error?: string }
```

#### `wizard.next`
Params:
```ts
{ sessionId: string; answer?: { stepId: string; value?: unknown } }
```
Response:
```ts
{ done: boolean; step?: WizardStep; status?: "running" | "done" | "cancelled" | "error"; error?: string }
```

#### `wizard.cancel`
Params:
```ts
{ sessionId: string }
```
Response:
```ts
{ status: "running" | "done" | "cancelled" | "error"; error?: string }
```

#### `wizard.status`
Params:
```ts
{ sessionId: string }
```
Response:
```ts
{ status: "running" | "done" | "cancelled" | "error"; error?: string }
```

WizardStep:
```ts
{ id: string; type: "note" | "select" | "text" | "confirm" | "multiselect" | "progress" | "action"; title?: string; message?: string; options?: Array<{ value: unknown; label: string; hint?: string }>; initialValue?: unknown; placeholder?: string; sensitive?: boolean; executor?: "gateway" | "client" }
```

### Talk

#### `talk.mode`
Params:
```ts
{ enabled: boolean; phase?: string }
```
Response:
```ts
{ enabled: boolean; phase: string | null; ts: number }
```
Notes: For webchat clients, requires a connected mobile node.

### Models

#### `models.list`
Params:
```ts
{}
```
Response:
```ts
{ models: Array<{ id: string; name: string; provider: string; contextWindow?: number; reasoning?: boolean }> }
```

### Agents

#### `agents.list`
Params:
```ts
{}
```
Response:
```ts
{ defaultId: string; mainKey: string; scope: "per-sender" | "global"; agents: Array<{ id: string; name?: string; identity?: { name?: string; theme?: string; emoji?: string; avatar?: string; avatarUrl?: string } }> }
```

#### `agents.files.list`
Params:
```ts
{ agentId: string }
```
Response:
```ts
{ agentId: string; workspace: string; files: Array<{ name: string; path: string; missing: boolean; size?: number; updatedAtMs?: number; content?: string }> }
```

#### `agents.files.get`
Params:
```ts
{ agentId: string; name: string }
```
Response:
```ts
{ agentId: string; workspace: string; file: { name: string; path: string; missing: boolean; size?: number; updatedAtMs?: number; content?: string } }
```

#### `agents.files.set`
Params:
```ts
{ agentId: string; name: string; content: string }
```
Response:
```ts
{ ok: true; agentId: string; workspace: string; file: { name: string; path: string; missing: boolean; size?: number; updatedAtMs?: number; content?: string } }
```

#### `agent`
Params:
```ts
{
  message: string;
  agentId?: string;
  to?: string;
  replyTo?: string;
  sessionId?: string;
  sessionKey?: string;
  thinking?: string;
  deliver?: boolean;
  attachments?: Array<{ type?: string; mimeType?: string; fileName?: string; content?: unknown }>;
  channel?: string;
  replyChannel?: string;
  accountId?: string;
  replyAccountId?: string;
  threadId?: string;
  groupId?: string;
  groupChannel?: string;
  groupSpace?: string;
  timeout?: number;
  lane?: string;
  extraSystemPrompt?: string;
  idempotencyKey: string;
  label?: string;
  spawnedBy?: string;
}
```
Response:
```ts
{ runId: string; status: "accepted"; acceptedAt: number }
```
Final response (same request id, later):
```ts
{ runId: string; status: "ok" | "error"; summary: string; result?: unknown }
```
Notes: The gateway may send multiple `res` frames for the same `id`.

#### `agent.identity.get`
Params:
```ts
{ agentId?: string; sessionKey?: string }
```
Response:
```ts
{ agentId: string; name?: string; avatar?: string; emoji?: string }
```

#### `agent.wait`
Params:
```ts
{ runId: string; timeoutMs?: number }
```
Response:
```ts
{ runId: string; status: "ok" | "error" | "timeout"; startedAt?: number; endedAt?: number; error?: string }
```

### Skills

#### `skills.status`
Params:
```ts
{ agentId?: string }
```
Response:
```ts
{ workspaceDir: string; managedSkillsDir: string; skills: Array<{ name: string; description?: string; source?: string; bundled?: boolean; filePath?: string; baseDir?: string; skillKey?: string; emoji?: string; homepage?: string; always?: boolean; disabled?: boolean; blockedByAllowlist?: boolean; eligible?: boolean; requirements?: { bins?: string[]; anyBins?: string[]; env?: string[]; config?: string[]; os?: string[] }; missing?: { bins?: string[]; anyBins?: string[]; env?: string[]; config?: string[]; os?: string[] }; configChecks?: unknown[]; install?: unknown[] }> }
```

#### `skills.bins`
Params:
```ts
{}
```
Response:
```ts
{ bins: string[] }
```

#### `skills.install`
Params:
```ts
{ name: string; installId: string; timeoutMs?: number }
```
Response:
```ts
{ ok: boolean; message?: string; [key: string]: unknown }
```
Notes: Install details are returned from the skill installer.

#### `skills.update`
Params:
```ts
{ skillKey: string; enabled?: boolean; apiKey?: string; env?: Record<string, string> }
```
Response:
```ts
{ ok: true; skillKey: string; config: { enabled?: boolean; apiKey?: string; env?: Record<string, string> } }
```

### Voice Wake

#### `voicewake.get`
Params:
```ts
{}
```
Response:
```ts
{ triggers: string[] }
```

#### `voicewake.set`
Params:
```ts
{ triggers: string[] }
```
Response:
```ts
{ triggers: string[] }
```
Also emits `voicewake.changed` event.

### Sessions

#### `sessions.list`
Params:
```ts
{ limit?: number; activeMinutes?: number; includeGlobal?: boolean; includeUnknown?: boolean; includeDerivedTitles?: boolean; includeLastMessage?: boolean; label?: string; spawnedBy?: string; agentId?: string; search?: string }
```
Response:
`SessionsListResult`

#### `sessions.preview`
Params:
```ts
{ keys: string[]; limit?: number; maxChars?: number }
```
Response:
`SessionsPreviewResult`

#### `sessions.resolve`
Params:
```ts
{ key?: string; sessionId?: string; label?: string; agentId?: string; spawnedBy?: string; includeGlobal?: boolean; includeUnknown?: boolean }
```
Response:
```ts
{ ok: true; key: string }
```

#### `sessions.patch`
Params:
```ts
{ key: string; label?: string | null; thinkingLevel?: string | null; verboseLevel?: string | null; reasoningLevel?: string | null; responseUsage?: "off" | "tokens" | "full" | "on" | null; elevatedLevel?: string | null; execHost?: string | null; execSecurity?: string | null; execAsk?: string | null; execNode?: string | null; model?: string | null; spawnedBy?: string | null; sendPolicy?: "allow" | "deny" | null; groupActivation?: "mention" | "always" | null }
```
Response:
```ts
{ ok: true; path: string; key: string; entry: unknown }
```
Scope: `operator.admin`

#### `sessions.reset`
Params:
```ts
{ key: string }
```
Response:
```ts
{ ok: true; key: string; entry: unknown }
```
Scope: `operator.admin`

#### `sessions.delete`
Params:
```ts
{ key: string; deleteTranscript?: boolean }
```
Response:
```ts
{ ok: true; key: string; deleted: boolean; archived: string[] }
```
Scope: `operator.admin`

#### `sessions.compact`
Params:
```ts
{ key: string; maxLines?: number }
```
Response:
```ts
{ ok: true; key: string; compacted: boolean; reason?: string; archived?: string; kept?: number }
```
Scope: `operator.admin`

### Nodes

#### `node.pair.request`
Params:
```ts
{ nodeId: string; displayName?: string; platform?: string; version?: string; coreVersion?: string; uiVersion?: string; deviceFamily?: string; modelIdentifier?: string; caps?: string[]; commands?: string[]; remoteIp?: string; silent?: boolean }
```
Response:
```ts
{ status: "pending"; request: NodePairingPendingRequest; created: boolean }
```
Scope: `operator.pairing`

#### `node.pair.list`
Params:
```ts
{}
```
Response:
```ts
{ pending: NodePairingPendingRequest[]; paired: NodePairingPairedNode[] }
```
Scope: `operator.pairing`

#### `node.pair.approve`
Params:
```ts
{ requestId: string }
```
Response:
```ts
{ requestId: string; node: NodePairingPairedNode }
```
Scope: `operator.pairing`

#### `node.pair.reject`
Params:
```ts
{ requestId: string }
```
Response:
```ts
{ requestId: string; nodeId: string }
```
Scope: `operator.pairing`

#### `node.pair.verify`
Params:
```ts
{ nodeId: string; token: string }
```
Response:
```ts
{ ok: boolean; node?: NodePairingPairedNode }
```
Scope: `operator.pairing`

#### `node.rename`
Params:
```ts
{ nodeId: string; displayName: string }
```
Response:
```ts
{ nodeId: string; displayName: string }
```
Scope: `operator.pairing`

#### `node.list`
Params:
```ts
{}
```
Response:
```ts
{ ts: number; nodes: Array<{ nodeId: string; displayName?: string; platform?: string; version?: string; coreVersion?: string; uiVersion?: string; deviceFamily?: string; modelIdentifier?: string; remoteIp?: string; caps: string[]; commands: string[]; pathEnv?: string; permissions?: Record<string, boolean>; connectedAtMs?: number; paired: boolean; connected: boolean }> }
```

#### `node.describe`
Params:
```ts
{ nodeId: string }
```
Response:
```ts
{ ts: number; nodeId: string; displayName?: string; platform?: string; version?: string; coreVersion?: string; uiVersion?: string; deviceFamily?: string; modelIdentifier?: string; remoteIp?: string; caps: string[]; commands: string[]; pathEnv?: string; permissions?: Record<string, boolean>; connectedAtMs?: number; paired: boolean; connected: boolean }
```

#### `node.invoke`
Params:
```ts
{ nodeId: string; command: string; params?: unknown; timeoutMs?: number; idempotencyKey: string }
```
Response:
```ts
{ ok: true; nodeId: string; command: string; payload: unknown; payloadJSON?: string | null }
```
Notes: Requires the node to be connected and command allowed by policy/allowlist.

#### `node.invoke.result`
Params:
```ts
{ id: string; nodeId: string; ok: boolean; payload?: unknown; payloadJSON?: string; error?: { code?: string; message?: string } }
```
Response:
```ts
{ ok: true } | { ok: true; ignored: true }
```
Scope: `node` role only.

#### `node.event`
Params:
```ts
{ event: string; payload?: unknown; payloadJSON?: string }
```
Response:
```ts
{ ok: true }
```
Scope: `node` role only.

### Devices

#### `device.pair.list`
Params:
```ts
{}
```
Response:
```ts
{ pending: DevicePairingPendingRequest[]; paired: Array<PairedDevice & { tokens?: Array<{ role: string; scopes: string[]; createdAtMs: number; rotatedAtMs?: number; revokedAtMs?: number; lastUsedAtMs?: number }> }> }
```
Scope: `operator.pairing`

#### `device.pair.approve`
Params:
```ts
{ requestId: string }
```
Response:
```ts
{ requestId: string; device: PairedDevice }
```
Scope: `operator.pairing`

#### `device.pair.reject`
Params:
```ts
{ requestId: string }
```
Response:
```ts
{ requestId: string; deviceId: string }
```
Scope: `operator.pairing`

#### `device.token.rotate`
Params:
```ts
{ deviceId: string; role: string; scopes?: string[] }
```
Response:
```ts
{ deviceId: string; role: string; token: string; scopes: string[]; rotatedAtMs: number }
```
Scope: `operator.pairing`

#### `device.token.revoke`
Params:
```ts
{ deviceId: string; role: string }
```
Response:
```ts
{ deviceId: string; role: string; revokedAtMs: number }
```
Scope: `operator.pairing`

### Cron and Wake

#### `wake`
Params:
```ts
{ mode: "now" | "next-heartbeat"; text: string }
```
Response:
```ts
{ ok: boolean }
```

#### `cron.list`
Params:
```ts
{ includeDisabled?: boolean }
```
Response:
```ts
{ jobs: CronJob[] }
```

#### `cron.status`
Params:
```ts
{}
```
Response:
```ts
{ enabled: boolean; storePath: string; jobs: number; nextWakeAtMs: number | null }
```

#### `cron.add`
Params:
```ts
{ name: string; agentId?: string | null; description?: string; enabled?: boolean; deleteAfterRun?: boolean; schedule: CronSchedule; sessionTarget: "main" | "isolated"; wakeMode: "next-heartbeat" | "now"; payload: CronPayload; delivery?: CronDelivery }
```
Response:
`CronJob`
Scope: `operator.admin`

#### `cron.update`
Params:
```ts
{ id?: string; jobId?: string; patch: Partial<CronJob> }
```
Response:
`CronJob`
Scope: `operator.admin`

#### `cron.remove`
Params:
```ts
{ id?: string; jobId?: string }
```
Response:
```ts
{ ok: true; removed: boolean }
```
Scope: `operator.admin`

#### `cron.run`
Params:
```ts
{ id?: string; jobId?: string; mode?: "due" | "force" }
```
Response:
```ts
{ ok: true; ran: true } | { ok: true; ran: false; reason: "not-due" }
```
Scope: `operator.admin`

#### `cron.runs`
Params:
```ts
{ id?: string; jobId?: string; limit?: number }
```
Response:
```ts
{ entries: Array<{ ts: number; jobId: string; action: "finished"; status?: "ok" | "error" | "skipped"; error?: string; summary?: string; runAtMs?: number; durationMs?: number; nextRunAtMs?: number }> }
```

### Messaging

#### `send`
Params:
```ts
{ to: string; message: string; mediaUrl?: string; mediaUrls?: string[]; gifPlayback?: boolean; channel?: string; accountId?: string; sessionKey?: string; idempotencyKey: string }
```
Response:
```ts
{ runId: string; messageId: string; channel: string; chatId?: string; channelId?: string; toJid?: string; conversationId?: string }
```
Notes: `runId` is `idempotencyKey`.

#### `poll` (undocumented but implemented)
Params:
```ts
{ to: string; question: string; options: string[]; maxSelections?: number; durationHours?: number; channel?: string; accountId?: string; idempotencyKey: string }
```
Response:
```ts
{ runId: string; messageId: string; channel: string; toJid?: string; channelId?: string; conversationId?: string; pollId?: string }
```
Notes: `poll` is not advertised in `features.methods` but is implemented.

### Chat (WebSocket-native)

#### `chat.history`
Params:
```ts
{ sessionKey: string; limit?: number }
```
Response:
```ts
{ sessionKey: string; sessionId?: string; messages: unknown[]; thinkingLevel?: string }
```

#### `chat.send`
Params:
```ts
{ sessionKey: string; message: string; thinking?: string; deliver?: boolean; attachments?: unknown[]; timeoutMs?: number; idempotencyKey: string }
```
Response (immediate ack):
```ts
{ runId: string; status: "started" }
```
Possible cached response:
```ts
{ runId: string; status: "in_flight" }
```
Final state is delivered via `chat` events.

#### `chat.abort`
Params:
```ts
{ sessionKey: string; runId?: string }
```
Response:
```ts
{ ok: true; aborted: boolean; runIds: string[] }
```

#### `chat.inject` (undocumented but implemented)
Params:
```ts
{ sessionKey: string; message: string; label?: string }
```
Response:
```ts
{ ok: true; messageId: string }
```
Notes: `chat.inject` is not advertised in `features.methods` but is implemented.

### Browser

#### `browser.request`
Params:
```ts
{ method: "GET" | "POST" | "DELETE"; path: string; query?: Record<string, unknown>; body?: unknown; timeoutMs?: number }
```
Response:
`unknown` (proxy result body)
Notes: If a connected browser-capable node is available, requests are proxied through it. Otherwise, the local browser control service is used if enabled.

### Misc

#### `system-presence`, `system-event`, `last-heartbeat`, `set-heartbeats`
See Health and Status section.

## Hidden or Not Advertised in `features.methods`

The following methods are implemented but not in the `features.methods` list returned by `HelloOk`:
- `poll`
- `chat.inject`

Clients should primarily rely on `features.methods` to discover capabilities, but these methods exist in the current implementation.
