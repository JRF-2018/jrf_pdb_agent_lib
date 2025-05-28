# jrf_pdb_agent_lib

<!-- Time-stamp: "2025-05-28T14:12:06Z" -->

`jrf_pdb_agent_lib` は、AI エージェントと実行中の Python プログラム間の高度なインタラクションを促進するために設計された、概念的な Python モジュールです。主に Python デバッガ (`pdb`) と共有メモリを介して、AI エージェントがプログラムの実行を動的に検査、変更、再開できる未来を構想しており、デバッガを複雑な意思決定とコード注入のための主要なインターフェースとして扱います。

このプロジェクトは、コアとなるアイデアを実証することを目的としたコンセプト実装です。


## ビジョン

従来、デバッガは人間がエラーを修正するために使用されてきました。`jrf_pdb_agent_lib` は、デバッガを AI エージェントが通常の実行フロー中にプログラムと対話するための制御されたエントリーポイントとして使用するというパラダイムシフトを提案します。

AI 駆動型プログラムが元の AI に相談する必要がある場合（例：複雑な推論、画像生成、動的なコード生成のため）、デバッガセッションに「ブレイク」することができます。この時点で、AI エージェントが制御を引き継ぎ、プログラムの状態を検査し、必要な操作を実行し（外部モデルを呼び出したり、新しいコードを生成したりする可能性があります）、その後、変更されたデータや新しいコードの実行を伴ってプログラムを再開するように指示します。

このビジョンの主要な側面：

  * **AI ネイティブデバッグ**: デバッガは AI エージェントのための第一級のインターフェースとなります。

  * **コンテキスト認識操作**: AI は、一時停止したプログラムの完全なランタイムコンテキスト（ローカル変数とグローバル変数）にアクセスできます。

  * **動的なコード注入**: AI は、プログラムのコンテキスト内で実行される新しいコードを提供できます。

  * **効率的なデータ交換（共有メモリ）**: 共有メモリを活用して、プログラムと AI エージェント間の高速なデータ転送を実現し、send/receive のための個別の IPC サーバープロセスを不要にします。

  * **デバッガログからの学習**: デバッガセッションからの詳細なインタラクションログは、将来の AI モデルにとって貴重なトレーニングデータとなる可能性があります。

他の形式のプロセス間通信も可能ですが、このバージョンでは、シンプルさのため、また `send/receive` のための明示的な個別のサーバープロセスを不要にするために、直接的な `pdb` インタラクションと共有メモリに焦点を当てています。


## 機能

`jrf_pdb_agent_lib` モジュール（短縮名 `pal`）は、以下のコア機能を提供します：

  * `pal.login(address_hint=None)`: ライブラリを初期化します。このバージョンでは、send/receive が直接共有メモリを使用するため、主に概念的な初期化ポイントとして機能します。address_hint はソケットバインディングには直接使用されませんが、ロギングや将来の複雑なセットアップに使用できます。

  * `pal.do(order, current_code=None)`: 中心となる関数です。呼び出されると、プログラムを一時停止し、Python デバッガ (`pdb.set_trace()`) に入ります。この一時停止中に、AI エージェントは直接 `pdb` コマンドまたは共有メモリを介して対話することが期待されます。デバッガセッション後、AI がモジュールの `EXEC` または `RESULT` グローバル変数（例：`pdb` プロンプトに直接入力するか、共有メモリを介して）を設定した場合、`pal.do` は提供されたコードを実行するか、指定された結果を呼び出し元のコンテキストで返します。

  * `pal.reload_module(module_name)`: Python モジュールの動的な再読み込みを可能にします。これは、AI エージェントがアプリケーション全体を再起動することなく、`.py` または `.apy` (AI Python) ファイルへのコード変更を適用するのに役立ちます。

  * `pal.share_memory(data_identifier, data)`: `multiprocessing.shared_memory` を使用して任意の Python オブジェクトを共有するメカニズムを提供します。データは転送のために pickle 化されます。

  * `pal.retrieve_shared_memory(data_identifier)`: `pal.share_memory` を介して以前に共有されたデータを取得します。

  * `pal.send(data_identifier, data)`: 共有メモリを使用してデータを送信します。この関数は pal.share_memory() のエイリアスです。データを共有メモリセグメントに書き込み、そのセグメントは data_identifier を知っている別のプロセス（例：AI エージェント）によって読み取ることができます。将来的にはソケットを使った通信に対応した実装にすべきでしょう。

  * `pal.receive(data_identifier)`: 共有メモリを使用してデータを受信します。この関数は `pal.retrieve_shared_memory()` のエイリアスです。data_identifier で識別される共有メモリセグメントからデータを読み取ります。将来的にはソケットを使った通信に対応した実装にすべきでしょう。

  * `pal.preserve_full_context(filename="context_snapshot.pkl")`: 呼び出し元のコンテキストをファイルに保存しようとする概念的な関数です。そのコンテクストのまま `pal.EXEC` から呼び出される `.py` (または `.apy`)ファイルを修正しながら実行して試してたいというときに便利なためにこのような機能を準備しています。(**警告: これは非常に実験的かつ限定的です。Python のランタイムコンテキストは複雑であり、callcc のような動作のための完全なシリアル化は一般的に実現不可能です。**)

  * `pal.restore_full_context(filename="context_snapshot.pkl")`: 以前に保存されたコンテキストを復元しようとする概念的な関数です。(**警告: 非常に実験的かつ限定的です。上記を参照してください。**)


## インストール

これはコンセプト実装であるため、一般的な pip インストールはまだ利用できません。
使用するには、`jrf_pdb_agent_lib.py` ファイルをプロジェクトディレクトリ、または Python 環境からアクセス可能な場所に配置するだけです。

# 例: リポジトリをクローンする場合

```sh
git clone https://github.com/JRF-2018/jrf_pdb_agent_lib.git
cp -p jrf_pdb_agent_lib/jrf_pdb_agent_lib.py .
```

その後、Python スクリプトでインポートできます：

```
import jrf_pdb_agent_lib as pal
```

## 使用例

次のようなファイルを example_1.py と名付け python から実行します。

```python
import jrf_pdb_agent_lib as pal

pal.login()

x = 42

r = pal.do("Do something good.")

print(r)
```

以下は AI が実行するという想定です。

```sh
$ python example_1.py
PDB Agent Lib: Initialized. Shared memory is used for IPC.

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Do something good.'
Entering PDB. AI should interact directly via PDB commands or shared memory.
> /some/where/jrf_pdb_agent_lib.py(102)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> /some/where/example_1.py(10)<module>()
-> r = pal.do("Do something good.")
(Pdb) print(x)
42
(Pdb) pal.EXEC = "pal.do('Multiply 2'); pal.do('Minus 1'); pal.RESULT = x"
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
PDB Agent Lib: Executing code from AI:
pal.do('Multiply 2'); pal.do('Minus 1'); pal.RESULT = x

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Multiply 2'
Entering PDB. AI should interact directly via PDB commands or shared memory.
> /some/where/jrf_pdb_agent_lib.py(102)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> <string>(1)<module>()
(Pdb) x = x * 2
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
PDB Agent Lib: No result returned from AI.

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Minus 1'
Entering PDB. AI should interact directly via PDB commands or shared memory.
> /some/where/jrf_pdb_agent_lib.py(102)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> <string>(1)<module>()
(Pdb) x = x - 1
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
PDB Agent Lib: No result returned from AI.
PDB Agent Lib: AI-provided code execution successful.
PDB Agent Lib: Returning result from AI.
83
```

この流れを説明すると、AI がプログラムを実行するとデバッガに入って "Do something good." という命令に従い、AI は x に 2 をかけ 1 を引く操作をすることにしました。最終的に 83 が帰ってきます。このように、返す pal.EXEC の中で、pal.do を「再帰的」に使って問題を分割していっても良いのです。


## 将来の拡張

  * **堅牢な共有メモリ協調**: より複雑なシナリオでは、ポーリングや暗黙のタイミングに依存するのではなく、新しいデータが共有メモリで利用可能になったときにプロセスに通知するためのシグナリングメカニズム（例: 共有メモリと `threading.Event` または `multiprocessing.Event` の使用）が必要になる場合があります。

  * **コンテキストのシリアル化**: `preserve_full_context` を改善し、Python オブジェクトのより信頼性の高いシリアル化を実現します。これは、特殊なライブラリを使用するか、保存できる範囲を制限することによって達成できる可能性があります。

  * **AI 駆動型デバッガコマンド**: 共有メモリまたは他の手段を介して AI が直接発行できる pdb コマンドのラッパーを開発します。

  * **セキュリティ**: 複数の信頼できないプロセスが関与する場合、共有メモリへのアクセスに対する認証と認可を実装します。


## ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています。詳細は LICENSE ファイルを参照してください。


## 著者

JRF ( http://jrf.cocolog-nifty.com/statuses , Twitter (X): @jion_rockford )

このプロジェクトは、大部分が Gemini 2.5 Flash によって生成されました。



----
(This document is mainly written in Japanese/UTF8.)
