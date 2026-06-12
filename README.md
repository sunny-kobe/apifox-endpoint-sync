# apifox-endpoint-sync

> 让 Codex 安全更新 Apifox 接口文档，而不是把整个 API 项目的钥匙交给 AI。

`apifox-endpoint-sync` 是一个面向 Codex / AI Agent 工作流的安全型 Apifox 文档同步工具。它只开放一条非常窄、非常可审查的通道：读取一个 `endpoint-update` JSON，本地完成安全校验，先 dry-run 预览计划，再交给 Apifox CLI 做 schema 校验，最后只更新一个已存在的 `endpointId`。

English summary:

> A safety-first single-endpoint Apifox doc sync tool for Codex and AI agents.

推荐的 GitHub 仓库简介：

```text
安全的单 endpoint Apifox 文档同步工具：让 Codex 更新接口文档，但禁止导入、项目级写入和共享资源修改。
```

English GitHub description:

```text
Safe single-endpoint Apifox doc sync for Codex and AI agents. No imports, no project-wide writes, no shared-resource changes.
```

## 亮点

- 为 Codex / AI Agent 文档生成场景设计，但用生产工具的方式约束写入范围。
- 一次只更新一个 endpoint，每次改动都能被清楚 review。
- 推荐流程默认先 dry-run，先看计划再写入。
- 在调用 Apifox CLI 之前拦截常见的项目级写入风险。
- 只使用 Python 标准库，依赖少，容易审计，适合开源项目直接采用。

## 背景

AI coding agent 很擅长把代码实现、接口样例和评审意见整理成结构化 API 文档。真正危险的地方通常不在于“生成 JSON”，而在于让自动化工具拥有过大的写入范围。

`apifox-endpoint-sync` 选择把能力边界收窄：

- Codex 只生成一个 `endpoint-update` JSON 文件。
- 本工具先做本地安全校验。
- Apifox CLI 再做 `endpoint-update` schema 校验。
- 最终只更新一个指定的 endpoint ID。

不做批量导入，不改公共参数，不碰环境、变量、安全配置或项目设置。

## 安装

克隆仓库后直接安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

也可以不安装，直接运行 checkout 内的脚本：

```bash
chmod +x scripts/apifox-endpoint-sync
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

## 本地校验

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m json.tool examples/endpoint-update.example.json >/dev/null
./scripts/apifox-endpoint-sync --endpoint-id endpoint_id_placeholder --update-file examples/endpoint-update.example.json --expected-method GET --expected-path /api/admin/users --dry-run
```

## License

MIT
