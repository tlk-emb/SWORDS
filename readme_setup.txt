SWORDSフレームワーク　環境構築

・利用ツールとバージョン

Xilinxツール：
　Vivado 2015.4
　Vivado HLS 2015.4
　Xilix SDK 2015.4
その他：
　clang 3.4以上（3.4, 3.8.1, 4.0.0で動作確認済み）
　python 2.6以上（2.7.13で動作確認済み）
Pythonパッケージソフトウェア：
　jsonschema 2.5.1以上（2.5.1, 2.6.0で動作確認済み）
　clang 3.4以上（3.4, 3.8.1, 4.0.0で動作確認済み）


・動作要件

Windows OS（7, 10で動作確認済み）

Xilinxツールの動作要件は下記文書の2章を参照のこと
https://japan.xilinx.com/support/documentation/sw_manuals_j/xilinx2015_4/ug973-vivado-release-notes-install-license.pdf


・環境構築の手順

1. Vivado/Vivado HLSのインストール
Vivado Design SuiteもしくはSDSoCのどちらでもよい．
https://japan.xilinx.com/support/download/index.html/content/xilinx/ja/downloadNav/vivado-design-tools/archive.html
https://japan.xilinx.com/support/download/index.html/content/xilinx/ja/downloadNav/sdx-development-environments/archive.html

「2015.4」をインストールすること．
System Editionにて動作を確認しているが，WebPACK等のEditionでも問題なく
動作するものと思われる．
Vivado Design Suiteの場合は，インストール時に"Software Development kit"を
選択すること．


2. LLVMのインストール
下記より入手してインストールする．
http://releases.llvm.org/download.html

「32ビット版」でないと動作しない．
インストール時設定でパスを通しておくこと


3. Pythonインストール
下記より入手してインストールする．
https://www.python.org/downloads/

インストール時設定でパスを通しておくこと


4. pythonパッケージソフトウェアのインストール
cmd.exe (Windowsコマンドプロンプト)上から以下を実行して
必要なライブラリをインストールする．

$ pip install jsonschema
$ pip install clang

2.でインストールしたのが最新版で無ければ，
$ pip install clang==3.8
のようにバージョンを明示的に指定すること．


5. SWORDSソースの取得
GitHubより取得する．
$ git clone https://github.com/tlk-emb/SWORDS.git


・サンプルの実行方法

cmd.exe から以下を実行する．
$ cd samples\matrixmul_simple
$ ..\..\swords.bat matrixmul.c matrixmul.json matrixmul

swords.bat のあるディレクトリにパスを通してもよい．
setenv.bat にて各種の設定を行う必要がある．
1行目はSDSoCのインストール先に合わせて変更すること．
2行目はLLVMのインストール時に環境変数を指定していれば不要であるが，
必要に応じて使用すること．


