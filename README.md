# apifox-endpoint-sync

> 一个帮助开发者安全更新 Apifox 接口文档的 CLI 工具：单 endpoint 同步、dry-run 预览、本地安全校验，适合 Codex / AI Agent 辅助维护 API 文档。

`apifox-endpoint-sync` 用来解决一个很具体的问题：当你想用 Codex、AI Agent 或脚本更新 Apifox 接口文档时，如何只更新一个接口，而不是误触批量导入、公共参数、环境变量或项目级配置。

它提供一条可审查的 Apifox 文档更新流程：读取一个 `endpoint-update` JSON，本地完成安全校验，先 dry-run 预览更新计划，再交给 Apifox CLI 做 schema 校验，最后只更新一个已存在的 `endpointId`。

English summary:

> A CLI for safely updating one Apifox API endpoint document with Codex or AI agents.

推荐的 GitHub 仓库简介：

```text
Apifox 接口文档更新 CLI：安全同步单个 endpoint，适合 Codex / AI Agent 维护 API 文档，支持 dry-run 和本地安全校验。
```

English GitHub description:

```text
CLI for safely updating one Apifox API endpoint document with Codex or AI agents. Dry-run, local validation, no imports.
```

## 适合谁用

- 想用 Codex 或 AI Agent 自动整理、更新 Apifox 接口文档的开发者。
- 想把代码实现、接口样例、测试用例同步到 Apifox 文档的人。
- 想使用 Apifox CLI，但只希望开放单接口更新权限的团队。
- 想避免 `apifox import`、公共参数、环境变量、项目设置被误改的维护者。
- 想找一个轻量、开源、可审计的 API 文档同步脚本的人。

## 你可能在搜索

如果你在搜索这些问题，这个项目就是为这些场景准备的：

- Apifox 如何用 CLI 更新接口文档
- Apifox endpoint update 使用方式
- Codex 生成 Apifox 接口文档
- AI Agent 自动更新 API 文档
- API 文档同步工具
- 接口文档自动化更新
- OpenAPI / Apifox 单接口文档维护
- 如何安全地让 AI 修改接口文档

## 亮点

- 为 Codex / AI Agent 文档生成场景设计，但用生产工具的方式约束写入范围。
- 一次只更新一个 endpoint，每次改动都能被清楚 review。
- 推荐流程默认先 dry-run，先看计划再写入。
- 在调用 Apifox CLI 之前拦截常见的项目级写入风险。
- 只使用 Python 标准库，依赖少，容易审计，适合开源项目直接采用。

## 背景

维护 API 文档最麻烦的地方，往往不是写一段描述，而是持续把代码里的请求参数、响应结构、接口示例同步到文档平台。AI coding agent 很擅长把代码实现、接口样例和评审意见整理成结构化 API 文档。真正危险的地方通常不在于“生成 JSON”，而在于让自动化工具拥有过大的写入范围。

`apifox-endpoint-sync` 选择把能力边界收窄：

- Codex 只生成一个 `endpoint-update` JSON 文件。
- 本工具先做本地安全校验。
- Apifox CLI 再做 `endpoint-update` schema 校验。
- 最终只更新一个指定的 endpoint ID。

不做批量导入，不改公共参数，不碰环境、变量、安全配置或项目设置。

## 前置条件

- Python 3.10+
- 官方 Apifox CLI，且本地可以直接运行 `apifox`
- 一个已有的 Apifox project
- 一个已有的 Apifox endpoint ID
- 一个可以登录 Apifox CLI 的 token

本工具只负责安全更新已有 endpoint 的文档，不负责创建 endpoint、批量导入接口或初始化 Apifox 项目。

## 快速开始

```bash
git clone https://github.com/sunny-kobe/apifox-endpoint-sync.git
cd apifox-endpoint-sync

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp examples/.env.example .env
```

编辑 `.env`，填入你的 Apifox token、project ID、project name 和 branch。然后先运行 dry-run：

```bash
apifox-endpoint-sync \
  --endpoint-id endpoint_id_placeholder \
  --update-file examples/endpoint-update.example.json \
  --expected-method GET \
  --expected-path /api/admin/users \
  --dry-run
```

如果 dry-run 输出的 endpoint ID、method、path 和命令计划都正确，再去掉 `--dry-run` 执行真实更新。

## 安装方式

推荐用可编辑安装：

```bash
pip install -e .
```

也可以不安装，直接运行 checkout 内的脚本：

```bash
./scripts/apifox-endpoint-sync --help
```

你还需要安装官方 Apifox CLI，并确保 `apifox` 在 `PATH` 中可用。

## 配置

复制示例环境变量文件：

```bash
cp examples/.env.example .env
```

支持的变量：

```dotenv
APIFOX_TOKEN=apifox_token_placeholder
APIFOX_PROJECT_ID=project_id_placeholder
APIFOX_PROJECT_NAME=Project Name Placeholder
APIFOX_BRANCH=main
```

`.env` 只放在本地，不要提交真实 token、project ID、endpoint ID、私有 URL 或私有接口样例。

## 准备更新信息

一次更新通常需要准备四类信息：

- `endpointId`：目标 Apifox 接口的 endpoint ID。可以从 Apifox 页面、已有脚本、团队文档或接口管理流程中获取。
- `method` 和 `path`：建议用 `--expected-method` 和 `--expected-path` 显式传入，避免把 JSON 写到错误接口。
- `endpoint-update` JSON：可以参考 [examples/endpoint-update.example.json](examples/endpoint-update.example.json)，也可以让 Codex 根据代码生成。
- Apifox project 信息：通过 `.env` 或命令参数传入 `APIFOX_PROJECT_ID`、`APIFOX_PROJECT_NAME`、`APIFOX_BRANCH`。

## 一行命令

先 dry-run：

```bash
apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file examples/endpoint-update.example.json --expected-method GET --expected-path /api/admin/users --dry-run
```

确认计划无误后再真实写入：

```bash
apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file examples/endpoint-update.example.json --expected-method GET --expected-path /api/admin/users
```

更新 JSON 会通过标准输入传给 `apifox endpoint update <id>`。Token 会通过标准输入传给 `apifox login --with-token`，避免把敏感值拼进命令行。

## 命令参数

| 参数 | 是否必填 | 说明 |
| --- | --- | --- |
| `--endpoint-id` | 是 | 要更新的 Apifox endpoint ID。 |
| `--update-file` | 是 | `endpoint-update` JSON 文件路径。 |
| `--expected-method` | 否 | 期望的 HTTP method，例如 `GET`。传入后会和 JSON 中的 `method` 对比。 |
| `--expected-path` | 否 | 期望的接口 path，例如 `/api/admin/users`。传入后会和 JSON 中的 `path` 对比。 |
| `--env-file` | 否 | `.env` 文件路径，默认读取当前目录的 `.env`。 |
| `--token` | 否 | Apifox token。更推荐使用 `.env` 或环境变量 `APIFOX_TOKEN`。 |
| `--project-id` | 否 | Apifox project ID，会覆盖 `.env` 里的 `APIFOX_PROJECT_ID`。 |
| `--project-name` | 否 | 期望的 project name，会覆盖 `.env` 里的 `APIFOX_PROJECT_NAME`。 |
| `--branch` | 否 | Apifox branch，会覆盖 `.env` 里的 `APIFOX_BRANCH`。 |
| `--dry-run` | 否 | 只打印更新计划和将执行的命令，不真实写入。 |
| `--skip-login` | 否 | 跳过 `apifox login --with-token`。一般只在你已经登录过 CLI 时使用。 |
| `--skip-project-list` | 否 | 跳过更新前的 `apifox project list`。 |
| `--skip-fetch-current` | 否 | 跳过更新前的 `apifox endpoint get`。 |
| `--skip-schema-validate` | 否 | 跳过 Apifox CLI 的 `endpoint-update` schema 校验。普通使用不建议跳过。 |
| `--verbose` | 否 | 输出更详细的命令执行信息。 |

## endpoint-update JSON 要求

最小 JSON 必须包含：

```json
{
  "method": "GET",
  "path": "/api/admin/users",
  "name": "List users"
}
```

实际使用时可以继续补充 endpoint-local 的参数、请求体、响应、示例和描述。不要在单接口 JSON 中写入公共参数、认证配置、环境变量或项目级配置。

## Codex 使用方式

1. 让 Codex 阅读本地接口实现、测试或你提供的接口说明。
2. 要求 Codex 只生成一个 endpoint 的 `endpoint-update` JSON。
3. 要求 Codex 只写 endpoint-local 的参数、请求体、响应、示例和描述。
4. 先运行本工具的 `--dry-run`。
5. Review method、path、endpoint ID 和命令计划。
6. 只有计划正确时，才去掉 `--dry-run` 执行真实更新。

可以从 [examples/codex-prompt.example.md](examples/codex-prompt.example.md) 里的提示词开始改。

## 安全边界

写入前，本工具会先校验：

- 必须存在 `method`，且必须是支持的 HTTP method。
- 必须存在 `path`，且必须以 `/` 开头。
- 如果传入 `--expected-method` 和 `--expected-path`，必须和 JSON 内容一致。
- 禁止出现 endpoint 级的共享配置字段：`commonParameters`、`auth`、`security`、`preProcessors`、`postProcessors`、`commonResponseStatus`。
- 禁止把公共参数写进单接口：`Authorization`、`uid`、`did`、`lang`、`ctry`、`app`、`vsn`、`ch`、`pf`、`br`、`os`、`mod`、`us`、`seq`、`adid`、`gaid`、`idfa`、`nw`、`ts`。

本工具只允许调用以下 Apifox CLI 命令：

```text
apifox login --with-token
apifox project list
apifox endpoint get
apifox cli-schema validate endpoint-update
apifox endpoint update <id>
```

## 不会修改的 Apifox 资源

本工具会拒绝任何会更新或导入以下资源的命令：

- 批量导入项目
- 公共参数
- 环境
- 变量
- 项目设置
- Security 或 auth scheme
- Pre-processor
- Post-processor

它是一个单 endpoint 文档同步助手，不是项目迁移工具。

## 常见问题

**会创建新的 Apifox endpoint 吗？**  
不会。它只更新你传入的已有 `endpointId`。

**可以批量同步整个项目吗？**  
不可以。这个项目刻意只支持单 endpoint 更新，避免 AI 或脚本误改大量接口。

**为什么要传 `--expected-method` 和 `--expected-path`？**  
它们是防呆护栏。即使 Codex 生成了错误 JSON，本地校验也会在写入前拦住 method/path 不一致的问题。

**为什么不直接调用 `apifox import`？**  
因为 import 适合项目级迁移或批量导入，不适合“让 AI 更新一个接口文档”的低风险流程。

**可以在 CI 里用吗？**  
可以，但建议 CI 默认只跑 `--dry-run` 和 schema 校验。真实写入应当放在受控 job 中，并使用最小权限 token。

## 排错

- `apifox CLI was not found in PATH.`：确认已经安装 Apifox CLI，并且 `apifox` 可以在当前 shell 中直接运行。
- `APIFOX_TOKEN is required unless --skip-login is used.`：在 `.env`、环境变量或 `--token` 中提供 token。
- `method mismatch` 或 `path mismatch`：检查 `--expected-method`、`--expected-path` 和 JSON 内容是否一致。
- `Forbidden endpoint field found`：JSON 中包含了公共参数、认证、安全配置或处理器字段，需要删除。
- `Public parameters must not be written into a single endpoint`：不要把 `Authorization`、`uid`、`did` 等公共参数写进单接口。

## 本地校验

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m json.tool examples/endpoint-update.example.json >/dev/null
./scripts/apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file examples/endpoint-update.example.json --expected-method GET --expected-path /api/admin/users --dry-run
```

## License

MIT
