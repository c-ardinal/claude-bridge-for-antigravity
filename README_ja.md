# Claude Code Bridge for Antigravity

[ [🇺🇸 English](README.md) | [🇯🇵 日本語](README_ja.md) ]

[![Antigravity Compatible](https://img.shields.io/badge/Antigravity-Compatible-blueviolet)](https://github.com/c-ardinal/antigravity)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows | MacOS | Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20MacOS%20%7C%20Linux-lightgrey)](#)

Claude Code のプラグインエコシステムを Antigravity 環境へ橋渡しするための強力なブリッジツールです。
Claude Code のマーケットプレイスからインストールしたグローバルスコープのプラグイン（Skill, Workflow, Script）を Antigravity のグローバルスコープで再利用できるようにします。

---

## 🚀 主な機能

- **⚡ プラグイン同期 (Plugin Sync)**:
  Claude Code のマーケットプレイスからインストールされた全てのプラグインを自動的に検出し、Antigravity のスキルディレクトリへリンクします。
- **📂 グローバルワークフロー連携 (Global Workflows)**:
  Claude Code の `commands/*.md` を Antigravity 向けに自動変換し、グローバルワークフローとして登録します。  
  これにより、`/` スラッシュコマンドからプラグインの機能を直接呼び出せます。
- **🛠️ 環境変数ブリッジ (Env Bridging)**:
  `CLAUDE_PLUGIN_ROOT` や `CLAUDE_PROJECT_DIR` など、Claude プラグインが想定するランタイム環境変数を Antigravity のコンテキストに合わせて自動注入してスクリプトを実行します。
- **🛡️ スマート・リンク方式**:
  Windows では管理者権限を要求しない **Junction / Hardlink** を、POSIX では **Symlink** を採用。環境を選ばず安定して動作します。

---

## 📦 セットアップ

### 前提条件

- **Python 3.6+** がインストールされていること
- **Claude Code** がインストールされ、プラグインが `[HOME]/.claude/plugins/marketplaces` に存在すること

### インストール & 同期

1. このフォルダを Antigravity のスキルディレクトリ（例: `[HOME]/.gemini/antigravity/skills/`）に配置します。
2. 以下のコマンドを実行して同期を開始します。

```bash
python scripts/claude-bridge.py sync
```

---

## 📖 使い方

### スラッシュコマンド (Workflows)

同期後、Antigravity 上で `/` を入力すると、`cb__` プレフィックスが付いたプラグイン由来のコマンドが表示されます。
例: `/cb__claude-plugins-official__feature-dev__feature-dev`

### スキルの参照

各プラグインの `SKILL.md` は、Antigravity から「スキル」として直接参照・学習可能です。
`[SKILLS_DIR]/claude-bridge-for-antigravity/plugins/` 配下にリンクされた実体が存在します。

### CLI ツール

統合スクリプト `claude-bridge.py` を使用して、詳細情報の確認やスクリプトの実行が可能です。

| コマンド      | 内容                                             |
| :------------ | :----------------------------------------------- |
| `sync`        | マーケットプレイスとの同期、ワークフローの再生成 |
| `list`        | 同期済みプラグインの一覧表示（リソース種別付き） |
| `info <name>` | プラグインの構造、Hook定義の表示                 |
| `run`         | 環境変数をブリッジした状態でのスクリプト実行     |

---

## 📁 ディレクトリ構造

```text
.gemini/antigravity
├──skills
│   └──claude-bridge-for-antigravity/
│       ├── SKILL.md            # Antigravity 向けスキル定義
│       ├── scripts/
│       │   └── claude-bridge.py # 唯一の統合ブリッジスクリプト
│       ├── plugins/            # sync によりプラグインへのリンクが生成される場所
│       └── README.md           # このファイル
└──global_workflows             # sync によりCommandのコピーが配置される場所
```

## ⚖️ 免責事項

Claude Code と Antigravity は異なるランタイム設計を持っています。  
このツールはファイルレベルおよび環境変数レベルの橋渡しを行いますが、Claude Code 内部のイベントループに依存する自動フック（自動発火）などはサポートしていません。  
必要に応じてスクリプトを `run` コマンドで手動実行してください。

---

Produced by Antigravity Agents.
Logic, Evidence, Robustness.
