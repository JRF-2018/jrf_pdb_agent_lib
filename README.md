# jrf_pdb_agent_lib

<!-- Time-stamp: "2025-05-31T09:51:49Z" -->

`jrf_pdb_agent_lib` is a conceptual Python module designed to facilitate advanced interaction between an AI agent and a running Python program. It primarily envisions a future where an AI agent can dynamically inspect, modify, and resume program execution via the Python debugger (`pdb`) and shared memory, treating the debugger as the primary interface for complex decision-making and code injection.

This project is a concept implementation aimed at demonstrating the core idea.

The brainstorming process for this concept is saved here:

《AI エージェントはデバッガを好むのではないか？ AI 専用デバッガ、またはデバッガを使うことが前提の agent ライブラリ(Python モジュール)の登場が待たれる。… pdb_agent_lib 構想。 - JRF のひとこと》  
http://jrf.cocolog-nifty.com/statuses/2025/05/post-617bf0.html

The conversation with Gemini 2.5 Flash (with Canvas) when I created this is also publicly available here. (Note: The Canvas content is not currently viewable.)

https://g.co/gemini/share/0251fcc144d8


## Vision

Traditionally, debuggers have been used by humans to fix errors. `jrf_pdb_agent_lib` proposes a paradigm shift: it envisions using the debugger as a controlled entry point for an AI agent to interact with a program during its normal execution flow.

When an AI-driven program needs to consult its originating AI (e.g., for complex reasoning, image generation, or dynamic code generation), it can "break" into a debugger session. At this point, the AI agent takes control, inspects the program's state, performs necessary operations (potentially calling external models or generating new code), and then instructs the program to resume with modified data or new code execution.

Key aspects of this vision:

* **AI-Native Debugging**: The debugger becomes a first-class interface for AI agents.
* **Context-Aware Operations**: The AI has access to the complete runtime context (local and global variables) of the paused program.
* **Dynamic Code Injection**: The AI can provide new code to be executed within the program's context.
* **Efficient Data Exchange (Shared Memory)**: Leveraging shared memory to achieve fast data transfer between the program and the AI agent, eliminating the need for a separate IPC server process for send/receive.
* **Learning from Debugger Logs**: Detailed interaction logs from debugger sessions could become valuable training data for future AI models.

While other forms of Inter-Process Communication (IPC) are possible, this version focuses on direct `pdb` interaction and shared memory for simplicity and to eliminate the need for explicit separate server processes for `send`/`receive`.


## Features

The `jrf_pdb_agent_lib` module (shortened to `pal`) provides the following core functionalities:

* `pal.login(address_hint=None)`: Initializes the library. In this version, it primarily serves as a conceptual initialization point, as `send/receive` directly use shared memory. `address_hint` is not directly used for socket binding but can be used for logging or future complex setup.
* `pal.do(order, current_code=None)`: The central function. When called, it pauses the program and enters the Python debugger (`pdb.set_trace()`). During this pause, the AI agent is expected to interact directly via `pdb` commands or shared memory. After the debugger session, if the AI has set the module's `EXEC`, `RESULT` or `EXCEPTION` global variables (e.g., by typing directly into the `pdb` prompt or via shared memory), `pal.do` will execute the provided code, return the specified result in the caller's context or raise the exception.
* `pal.consult_human(order=None, current_code=None)`: This is a pseudo-function for the AI to request a in execution and interact with a human while the debugger is running. It enters the debugger at this point. It's also possible that the AI might explicitly insert calls to this this function into its generated code when it determines that human interaction is necessary. Similar to `pal.do`, it interprets `EXEC`, `RESULT`, or `EXCEPTION` to support the consultation, however, unlike pal.do, it re-enters the debugger even after EXEC completes, allowing for continued human interaction.

**Please note**: Due to its design, directly calling `pal.do` or `pal.consult_human` (or functions that utilize them) from within a debugger session is not possible.

* `pal.AiException(arg)`: A custom exception intended to be raised explicitly by the AI agent or within AI-provided code. This exception is designed to be caught by the AI's logic or the program's error handling. If not explicitly caught, it will propagate up the call stack through `pal.do`, similar to standard Python exceptions.
* `pal.LoopRequestException(arg)`: A custom exception used by the AI agent within an `EXEC` block to explicitly request another iteration of the `EXEC` loop in `pal.do`. This is useful for managing multi-step operations within a single `pal.do`.
* `pal.reload_module(module_name)`: Allows dynamic reloading of a Python module. This is useful for an AI agent to apply code changes to `.py` or `_a.py` (AI Python) files without restarting the entire application.
* `pal.share_memory(data_identifier, data)`: Provides a mechanism to share arbitrary Python objects using `multiprocessing.shared_memory`. Data is pickled for transfer.
* `pal.retrieve_shared_memory(data_identifier)`: Retrieves data previously shared via `pal.share_memory`.
* `pal.send(data_identifier, data)`: Sends data using shared memory. This function is an alias for `pal.share_memory()`. It writes data to a shared memory segment, which can then be read by another process (e.g., the AI agent) that knows the `data_identifier`. In the future, this should be implemented with socket-based communication.
* `pal.receive(data_identifier)`: Receives data using shared memory. This function is an alias for `pal.retrieve_shared_memory()`. It reads data from a shared memory segment identified by `data_identifier`. In the future, this should be implemented with socket-based communication.
* `pal.preserve_full_context(filename="context_snapshot.pkl")`: A conceptual function that attempts to save the caller's context to a file. This feature is prepared to be useful when you want to execute and test by modifying `.py` (or `_a.py`) files called from `pal.EXEC` while maintaining that context. (**WARNING: This is highly experimental and limited. Python's runtime context is complex, and full serialization for callcc-like behavior is generally not feasible.**)
* `pal.restore_full_context(filename="context_snapshot.pkl")`: A conceptual function that attempts to restore a previously saved context from a file. (**WARNING: Highly experimental and limited. See above.**)


## Installation

This is a conceptual implementation.  While not yet published on PyPI, `jrf_pdb_agent_lib` can be installed directly from its Git repository using pip.

Example 1: Installing with pip from the repository

```sh
pip install git+https://github.com/JRF-2018/jrf_pdb_agent_lib
```

Alternatively, simply place the `jrf_pdb_agent_lib.py` file you obtained into your project directory or a location accessible from your Python environment.

Example 2: Cloning the repository

```sh
git clone https://github.com/JRF-2018/jrf_pdb_agent_lib.git
cp -p jrf_pdb_agent_lib/jrf_pdb_agent_lib.py .
```

You can then import it in your Python script:

```python
import jrf_pdb_agent_lib as pal
```

## Usage Example

Save the following file as `example_1.py` and run it with Python:

```python
import jrf_pdb_agent_lib as pal

pal.login()

x = 42

r = pal.do("Do something good.")

print(r)
```

The following is an example of what the AI would execute:

```sh
$ python example_1.py
PDB Agent Lib: Initialized. Shared memory is used for IPC.

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Do something good.'
AI should interact directly via PDB commands or shared memory.
--- PDB Agent Lib: Entering Debugger ---
> /some/where/jrf_pdb_agent_lib.py(133)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> /some/where/example_1.py(10)<module>()
-> r = pal.do("Do something good.")
(Pdb) print(x)
42
(Pdb) pal.EXEC = "pal.do('Multiply 2'); pal.do('Minus 1'); pal.RESULT = x"
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
PDB Agent Lib: Executing code from AI: "pal.do('Multiply 2'); pal.do('Minus 1'); pal.RESULT = x"

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Multiply 2'
AI should interact directly via PDB commands or shared memory.
--- PDB Agent Lib: Entering Debugger ---
> /some/where/jrf_pdb_agent_lib.py(133)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> <string>(1)<module>()
(Pdb) x = x * 2
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
--- PDB Agent Lib: Exiting AI Interaction ---
PDB Agent Lib: No result returned from AI.

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Minus 1'
AI should interact directly via PDB commands or shared memory.
--- PDB Agent Lib: Entering Debugger ---
> /some/where/jrf_pdb_agent_lib.py(133)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> <string>(1)<module>()
(Pdb) x = x - 1
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
--- PDB Agent Lib: Exiting AI Interaction ---
PDB Agent Lib: No result returned from AI.
PDB Agent Lib: AI-provided code execution successful.
--- PDB Agent Lib: Exiting AI Interaction ---
PDB Agent Lib: Returning result from AI.
83
```

To explain this flow: when the AI executes the program, it enters the debugger and, following the instruction "Do something good.", the AI decides to multiply `x` by 2 and then subtract 1. Finally, 83 is returned. In this way, you can even "recursively" use `pal.do` within the returned `pal.EXEC` to break down problems.


## Future Enhancements

  * **Robust Shared Memory Coordination**: More complex scenarios may require a signaling mechanism (e.g., using shared memory with `threading.Event` or `multiprocessing.Event`) to notify processes when new data is available in shared memory, rather than relying on polling or implicit timing.
  
  * **Context Serialization**: Improve `preserve_full_context` for more reliable serialization of Python objects. This could be achieved by using specialized libraries or by limiting the scope of what can be saved.
  
  * **AI-Driven Debugger Commands**: Develop wrappers for pdb commands that can be directly issued by the AI via shared memory or other means.

  * **Security**: Implement authentication and authorization for shared memory access if multiple untrusted processes are involved.

  * **AI-Specific Debugger**: If debugger state push/pop functionality were available, it should be possible to directly call `pal.do` or `pal.consult_human` even from a debugger session. The development of such an AI-specific debugger with these capabilities is highly anticipated. Should that happen, a dedicated `pdb_agent_lib` for it would likely be necessary.


## License

This project is licensed under the MIT License. See the LICENSE file for details.


## Author

JRF ( http://jrf.cocolog-nifty.com/statuses , Twitter (X): @jion_rockford )

This project was largely generated by Gemini 2.5 Flash.




# jrf_pdb_agent_lib

`jrf_pdb_agent_lib` は、AI エージェントと実行中の Python プログラム間の高度なインタラクションを促進するために設計された、概念的な Python モジュールです。主に Python デバッガ (`pdb`) と共有メモリを介して、AI エージェントがプログラムの実行を動的に検査、変更、再開できる未来を構想しており、デバッガを複雑な意思決定とコード注入のための主要なインターフェースとして扱います。

このプロジェクトは、コアとなるアイデアを実証することを目的としたコンセプト実装です。

このコンセプトの私のブレインストーミングの経緯は↓に保存しておきました。

《AI エージェントはデバッガを好むのではないか？ AI 専用デバッガ、またはデバッガを使うことが前提の agent ライブラリ(Python モジュール)の登場が待たれる。… pdb_agent_lib 構想。 - JRF のひとこと》  
http://jrf.cocolog-nifty.com/statuses/2025/05/post-617bf0.html

これを作ったときの Gemini 2.5 Flash (with Canvas) さんとの会話も公開しておきます↓。Canvas の内容は今現在は見れないようですが…。

https://g.co/gemini/share/0251fcc144d8


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

  * `pal.do(order, current_code=None)`: 中心となる関数です。呼び出されると、プログラムを一時停止し、Python デバッガ (`pdb.set_trace()`) に入ります。この一時停止中に、AI エージェントは直接 `pdb` コマンドまたは共有メモリを介して対話することが期待されます。デバッガセッション後、AI がモジュールの `EXEC` または `RESULT` または `EXCEPTION` グローバル変数（例：`pdb` プロンプトに直接入力するか、共有メモリを介して）を設定した場合、`pal.do` は提供されたコードを実行するか、指定された結果を呼び出し元のコンテキストで返すか、例外を発生させます。

  * `pal.consult_human(order=None, current_code=None)`: AI がデバッガを実行中に AI に対し、そこでいったん止まって人間と対話することを求めるための疑似関数で、このときデバッガに入ります。もしかすると AI が人間と対話が必要と判断するとき生成するソースにこの関数を明示するという使い方もあるかもしれません。consultation のサポートのため `pal.do` と同じく `EXEC` または `RESULT` または `EXCEPTION` を解しますが、こちらは人との対話のために `EXEC` 終了時にもデバッガに戻るという違いがあります。

**注意**: 設計上、デバッガから直接 `pal.do` や `pal.consult_human` (を使った関数)を呼ぶことはできません。

  * `pal.AiException(arg)`: AI エージェント、または AI が提供するコード内で意図的に発生させるカスタム例外です。この例外は、AI のロジックやプログラムのエラーハンドリングによって明示的にキャッチされることを想定しています。明示的にキャッチされない限り、通常の Python 例外と同様に `pal.do` を素通りし、呼び出しスタックを上位に伝播します。

  * `pal.LoopRequestException(arg)`: `pal.do` 内の `EXEC` ブロックにおいて、AI エージェントが明示的に `EXEC` ループの次のイテレーションを要求するために使用するカスタム例外です。単一の `pal.do` 呼び出し内で多段階の操作を管理するのに役立ちます。
  
  * `pal.reload_module(module_name)`: Python モジュールの動的な再読み込みを可能にします。これは、AI エージェントがアプリケーション全体を再起動することなく、`.py` または `_a.py` (AI Python) ファイルへのコード変更を適用するのに役立ちます。

  * `pal.share_memory(data_identifier, data)`: `multiprocessing.shared_memory` を使用して任意の Python オブジェクトを共有するメカニズムを提供します。データは転送のために pickle 化されます。

  * `pal.retrieve_shared_memory(data_identifier)`: `pal.share_memory` を介して以前に共有されたデータを取得します。

  * `pal.send(data_identifier, data)`: 共有メモリを使用してデータを送信します。この関数は pal.share_memory() のエイリアスです。データを共有メモリセグメントに書き込み、そのセグメントは data_identifier を知っている別のプロセス（例：AI エージェント）によって読み取ることができます。将来的にはソケットを使った通信に対応した実装にすべきでしょう。

  * `pal.receive(data_identifier)`: 共有メモリを使用してデータを受信します。この関数は `pal.retrieve_shared_memory()` のエイリアスです。data_identifier で識別される共有メモリセグメントからデータを読み取ります。将来的にはソケットを使った通信に対応した実装にすべきでしょう。

  * `pal.preserve_full_context(filename="context_snapshot.pkl")`: 呼び出し元のコンテキストをファイルに保存しようとする概念的な関数です。そのコンテクストのまま `pal.EXEC` から呼び出される `.py` (または `_a.py`)ファイルを修正しながら実行して試してたいというときに便利なためにこのような機能を準備しています。(**警告: これは非常に実験的かつ限定的です。Python のランタイムコンテキストは複雑であり、callcc のような動作のための完全なシリアル化は一般的に実現不可能です。**)

  * `pal.restore_full_context(filename="context_snapshot.pkl")`: 以前に保存されたコンテキストを復元しようとする概念的な関数です。(**警告: 非常に実験的かつ限定的です。上記を参照してください。**)

## インストール

これはコンセプト実装であり、PyPI には登録されていませんが、`jrf_pdb_agent_lib` は Git リポジトリから直接インストールできます。

例1: リポジトリから pip でインストールする場合

```sh
pip install git+https://github.com/JRF-2018/jrf_pdb_agent_lib
```

または、取ってきた `jrf_pdb_agent_lib.py` ファイルをプロジェクトディレクトリ、または Python 環境からアクセス可能な場所に配置するだけです。

例2: リポジトリをクローンする場合

```sh
git clone https://github.com/JRF-2018/jrf_pdb_agent_lib.git
cp -p jrf_pdb_agent_lib/jrf_pdb_agent_lib.py .
```

その後、Python スクリプトでインポートできます：

```python
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
AI should interact directly via PDB commands or shared memory.
--- PDB Agent Lib: Entering Debugger ---
> /some/where/jrf_pdb_agent_lib.py(133)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> /some/where/example_1.py(10)<module>()
-> r = pal.do("Do something good.")
(Pdb) print(x)
42
(Pdb) pal.EXEC = "pal.do('Multiply 2'); pal.do('Minus 1'); pal.RESULT = x"
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
PDB Agent Lib: Executing code from AI: "pal.do('Multiply 2'); pal.do('Minus 1'); pal.RESULT = x"

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Multiply 2'
AI should interact directly via PDB commands or shared memory.
--- PDB Agent Lib: Entering Debugger ---
> /some/where/jrf_pdb_agent_lib.py(133)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> <string>(1)<module>()
(Pdb) x = x * 2
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
--- PDB Agent Lib: Exiting AI Interaction ---
PDB Agent Lib: No result returned from AI.

--- PDB Agent Lib: AI Interaction Point ---
Order for AI: 'Minus 1'
AI should interact directly via PDB commands or shared memory.
--- PDB Agent Lib: Entering Debugger ---
> /some/where/jrf_pdb_agent_lib.py(133)do()
-> print(f"--- PDB Agent Lib: Exiting Debugger ---")
(Pdb) u
> <string>(1)<module>()
(Pdb) x = x - 1
(Pdb) c
--- PDB Agent Lib: Exiting Debugger ---
--- PDB Agent Lib: Exiting AI Interaction ---
PDB Agent Lib: No result returned from AI.
PDB Agent Lib: AI-provided code execution successful.
--- PDB Agent Lib: Exiting AI Interaction ---
PDB Agent Lib: Returning result from AI.
83
```

この流れを説明すると、AI がプログラムを実行するとデバッガに入って "Do something good." という命令に従い、AI は x に 2 をかけ 1 を引く操作をすることにしました。最終的に 83 が帰ってきます。このように、返す pal.EXEC の中で、pal.do を「再帰的」に使って問題を分割していっても良いのです。


## 将来の拡張

  * **堅牢な共有メモリ協調**: より複雑なシナリオでは、ポーリングや暗黙のタイミングに依存するのではなく、新しいデータが共有メモリで利用可能になったときにプロセスに通知するためのシグナリングメカニズム（例: 共有メモリと `threading.Event` または `multiprocessing.Event` の使用）が必要になる場合があります。

  * **コンテキストのシリアル化**: `preserve_full_context` を改善し、Python オブジェクトのより信頼性の高いシリアル化を実現します。これは、特殊なライブラリを使用するか、保存できる範囲を制限することによって達成できる可能性があります。

  * **AI 駆動型デバッガコマンド**: 共有メモリまたは他の手段を介して AI が直接発行できる pdb コマンドのラッパーを開発します。

  * **セキュリティ**: 複数の信頼できないプロセスが関与する場合、共有メモリへのアクセスに対する認証と認可を実装します。

  * **AI 専用デバッガ**: デバッガの状態のプッシュ／ポップができれば、デバッガに止まったところからも直接 `pal.do` や `pal.consult_human` が呼び出せるようになるはずです。そのような機能もある AI 専用デバッガの開発が待たれます。そうなればそれ用の `pdb_agent_lib` が必要となるでしょう。
  

## ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています。詳細は LICENSE ファイルを参照してください。


## 著者

JRF ( http://jrf.cocolog-nifty.com/statuses , Twitter (X): @jion_rockford )

このプロジェクトは、大部分が Gemini 2.5 Flash によって生成されました。



----
(This document is mainly written in Japanese/UTF8.)
