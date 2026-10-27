# diagram-contract-kit

描画の前に「図解仕様」を作り、決定論的に検証する最小限のAgent Skillです。
Python 3.10以上の標準ライブラリだけで動作します。
[English README](README.md) / [Skill](skills/diagram-contract/SKILL.md)

構成図・データフロー・状態・ポリシー図は、事実に基づくラベル付きの箱・矢印・境界を既定とします。
物理的な機械の比喩は、利用者が明示的に選んだ別の説明図として扱います。
「ソフトウェア構成図なのに物理的な卓上装置を要求してしまう」という仕様の不一致を、
架空の失敗fixtureとして再現し、描画前に検出します。非公開の研究コードや実験データは含みません。
図の目的文と型付きの描画指示は分離します。目的文の変更や指示の不一致、未解決の曖昧さは生成前に失敗します。
自由文の矛盾を全て自動理解する検証ではありません。ハッシュの再計算は意味の承認にならず、
意味が残って曖昧な場合は人に確認し、生成側には検証済みの型付き計画だけを渡してください。

## クイックスタート（オフラインのサンプル検証）

必要なのはPython 3.10以上とGitです。チェックアウト後の追加パッケージ、
ネットワーク接続、認証情報は不要です。次のコマンドは**同梱の架空サンプル**を検証し、
テストと固定SVGの再現性を確認します。自分のプロジェクト用の図解仕様を自動生成するものではありません。

```sh
git clone https://github.com/serevy/diagram-contract-kit.git
cd diagram-contract-kit
python3 scripts/validate_contract.py examples/fictional/diagram-contract.json
# 任意：回帰テストとコミット済みSVGの一致確認
python3 -m unittest discover -s tests -v
python3 scripts/render_example.py --check
```

Windowsでは`python3`を`python`に置き換えます。LinuxとWindowsのCIで同じテストを実行します。
改行は`.gitattributes`でLFに統一し、Windowsでシンボリックリンク権限がない場合だけ該当テストをスキップします。

正常な契約はexit 0、物理装置を要求する
`tests/fixtures/bad-physical-instrument.json`と認可の根拠が曖昧な
`tests/fixtures/ambiguous-authority.json`はexit 1、読めないJSONはexit 2です。
正常でも意味・見た目・公開の承認はpendingのままです。

**自分のリポジトリ**では、[契約ガイド](skills/diagram-contract/references/contract-guide.md)と
[架空の完成例](examples/fictional/diagram-contract.json)を参考に
`diagram-contract.json`を作成してください。出典ファイル・リビジョン・ハッシュ・図の事実は
自分のプロジェクトに合わせて記録します。架空のJSONをそのまま使うことはできません。
対象リポジトリのルートから次を実行します。

```sh
python3 /path/to/kit/scripts/validate_contract.py diagram-contract.json --root .
python3 /path/to/kit/scripts/validate_contract.py diagram-contract.json --root . --render-plan
```

`--render-plan`は検証済みの型付き描画データだけを出力します。
構造検証のPASSだけで図の公開が承認されるわけではありません。

## Agent Skills対応エージェントで使う（任意）

AIエージェントがなくても検証CLIは動作します。エージェントを使う場合は、
このキットのチェックアウトを保持し、各ホストの手順に従って
[diagram-contract Skill](skills/diagram-contract/SKILL.md)を読み込んでください。
例えば、プロジェクト単位の`.agents/skills/`を使うホストでは次のように配置できます。

```sh
mkdir -p .agents/skills
cp -R /path/to/kit/skills/diagram-contract .agents/skills/
```

Skillの配置場所と呼び出し方はホストごとに異なります。
Skillに非対応なら、`SKILL.md`を直接参照して手順を実行できます。

エージェントには、対象プロジェクトで次のように依頼できます。

```text
/path/to/kit のdiagram-contract Skillを使ってください。
このプロジェクトのREADME・設計書・関連ADR/PDDRを確認し、
描画前に、出典に裏付けられたdiagram-contract.jsonを作成してください。
実際のリビジョンとSHA-256、事実と仮定、ノードと辺のID、
要求言語と未承認の人間レビューゲートを記録してください。
目的文と型付きrendering.directivesを分離し、意味が不明なら生成を止めてください。
読み取り専用のフローに認可ゲートを創作せず、分類結果を認可と混同しないでください。
このプロジェクトを--rootとして、キットの検証CLIを実行してください。
描画には検証済みの--render-planを使い、結果を出典と独立して照合してください。
契約・検証結果・未完了のレビューを返し、承認なく公開・マージしないでください。
```

特定のAIプロバイダー、モデル、推論設定は必須ではありません。
実際のSkill対応・モデル提供・AI利用料金は利用ホストに依存します。
同梱の自動テストが検証するのはSkill形式と決定論的な処理であり、
特定モデルの生成品質ではありません。

## 出力と制約

架空の「入力→分類→型付き結果→独立した決定論的ポリシー→保留／レビュー／候補」を使います。
候補は模擬結果で、実際の処理を認可・実行しません。
[英語SVG](examples/fictional/architecture.en.svg)と
[日本語SVG](examples/fictional/architecture.ja.svg)をローカルで開いて確認できます。
`render_example.py`はこの例だけを再生成し、`--check`は欠落・変更された出力を失敗として検出します。

出典ハッシュ・ID・辺・英日ラベルのキー・認可の迂回・レビューゲートを検証します。
過去の出典と現在の統合リビジョンは別々に保存し、過去のEvidenceを上書きしません。
構造チェックのPASSは、概念の正しさや見やすさの保証ではありません。
`brief.use`のUTF-8ハッシュを`rendering.purpose_sha256`に記録し、目的文の変更を検出します。
変更後は出典と型付き指示を再確認し、意味が確定してから新しいハッシュを記録してください。
`--render-plan`は検証成功時だけ型付き指示・グラフ・ラベルのJSONを出力し、目的文を指示に含めません。
入力→分類→型付き結果だけの図には認可ゲートを要求しません。
`outcome`は保護された処理・実行候補を表し、それを含む図では独立した規則と認可ゲートが必要です。
新規プロジェクトは`historical_source_revision: null`とし、過去の出典を作りません。
現在の出典・リビジョン・ハッシュは引き続き必要です。
最初のPR時点の契約には、目的と指示を確認したうえで新しい`rendering`フィールドを追加してください。
公開には独立した人間の意味・視覚レビューと承認が必要です。
詳細は[契約ガイド](skills/diagram-contract/references/contract-guide.md)と[CI方針](docs/ci.md)にあります。

独立して作成した貢献者のファイルは[MIT](LICENSE)です。
Anatomy・Yomiyasuは[任意連携](THIRD_PARTY_NOTICES.md)で、コードやSkill本文は同梱していません。
