# OpenTalkBot
### シンプルな読み上げBOT  
単体鯖用  
複数鯖はサポートしていません  


# セットアップ
1. [Python](https://www.python.org/downloads/)のインストール
2. リポジトリのクローン
3. クローンしたリポジトリ内で ```pip install -r requirements.txt``` を実行
4. [ここ](https://discord.com/developers/applications)でNew ApplicationからBotを作りTokenを入手する
5. config.pyをテキストエディタで開きTokenを所定の位置に貼り付ける
6. 4で作ったApplicationのOauth2のURL Generatorで`bot`と`applications.commands`にチェックを入れ、下に出てきたBOT PERMISSIONSで`Administrator`にチェックを入れて一番下のURLからBOTをサーバーに追加
7. BOT起動前にVOICEVOXを起動またはVOICEROID2をインストールしておく
8. ```py main.py``` でBotを起動する