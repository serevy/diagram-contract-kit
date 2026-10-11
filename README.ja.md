# diagram-contract-kit

描画の前に「図解仕様」を作り、決定論的に検証する最小限のAgent Skillです。
Python 3.10以上の標準ライブラリだけで動作します。
[English README](README.md) / [Skill](skills/diagram-contract/SKILL.md)

構成図・データフロー・状態・ポリシー図は、事実に基づくラベル付きの箱・矢印・境界を既定とします。
物理的な機械の比喩は、利用者が明示的に選んだ別の説明図として扱います。
Semantic Decision Labで起きた「構成図なのに物理的な卓上装置を要求する仕様」を、
独立して書き直した失敗fixtureで描画前に検出します。研究コードやEvidenceはコピーしていません。

## 実行

```sh
git clone https://github.com/serevy/diagram-contract-kit.git
cd diagram-contract-kit
python3 scripts/validate_contract.py examples/fictional/diagram-contract.json
python3 -m unittest discover -s tests -v
python3 scripts/render_example.py --check
```

正常な契約はexit 0、物理装置を要求する
`tests/fixtures/bad-physical-instrument.json`と認可の根拠が曖昧な
`tests/fixtures/ambiguous-authority.json`はexit 1、読めないJSONはexit 2です。
正常でも意味・見た目・公開の承認はpendingのままです。

## Codex / Astra Low

対象プロジェクトからSkillをコピーします。キット全体のチェックアウトも保持してください。

```sh
mkdir -p .agents/skills
cp -R /path/to/kit/skills/diagram-contract .agents/skills/
```

Codexを更新・起動し、ホストでGPT-6 Astra / Lowを選択して、例えば次を依頼します。

```text
$diagram-contract を /path/to/kit から使用してください。
README・設計文書・ADR/PDDRを確認して、描画前にソフトウェア構成図の契約を作成してください。
出典とリビジョン・SHA-256、事実と仮定、ノードと辺、独立したポリシー／認可境界、
英日ラベル、SVG出力、未承認の人間レビューゲートを記録してください。
このプロジェクトを --root にしてキットのCLIで検証し、失敗時は描画を止めてください。
契約と検証結果を返してください。公開・マージはしないでください。
```

モデルの選択・提供はホスト側の設定です。有料推論や外部APIは不要です。
自動テストはSkill形式と検証基盤を確認します。Astra生成の性能実測は含みません。
他のAgent Skills対応エージェントでも、同じSkillを各ホストの方法で読み込めます。

## 出力と制約

架空の「入力→分類→型付き結果→独立した決定論的ポリシー→保留／レビュー／候補」を使います。
候補は模擬結果で、実際の処理を認可・実行しません。
[英語SVG](examples/fictional/architecture.en.svg)と
[日本語SVG](examples/fictional/architecture.ja.svg)をローカルで開いて確認できます。
`render_example.py`はこの例だけを再生成し、`--check`は欠落・変更された出力を失敗として検出します。

出典ハッシュ・ID・辺・英日ラベルのキー・認可の迂回・レビューゲートを検証します。
過去の出典と現在の統合リビジョンは別々に保存し、過去のEvidenceを上書きしません。
構造チェックのPASSは、概念の正しさや見やすさの保証ではありません。
公開には独立した人間の意味・視覚レビューと承認が必要です。
詳細は[契約ガイド](skills/diagram-contract/references/contract-guide.md)と[CI方針](docs/ci.md)にあります。

独立して作成した貢献者のファイルは[MIT](LICENSE)です。
Anatomy・Yomiyasuは[任意連携](THIRD_PARTY_NOTICES.md)で、コードやSkill本文は同梱していません。
