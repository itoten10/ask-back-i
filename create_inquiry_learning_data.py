"""探求学習らしいテストデータを作成（非認知能力の個性と一貫したテーマ）
更新内容:
- 探求フェーズ: テーマ設定、課題設定、情報収集、整理・分析、まとめ・表現、発表準備
- 投稿日時: 12/17の2週間以内（12/3以降）に最終投稿がある人を多数に
- 投稿数: 4〜15件のばらつき
- 能力バランス: より論理的な組み合わせに
- 感謝の手紙: 1.5pt
"""
import asyncio
import ssl
import random
from datetime import datetime, timedelta
from decimal import Decimal
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DB_USER = "students"
DB_PASSWORD = "10th-tech0"
DB_HOST = "gen10-mysql-dev-01.mysql.database.azure.com"
DB_PORT = 3306
DB_NAME = "ask"
SSL_CA_PATH = "./DigiCertGlobalRootG2.crt.pem"

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ssl_context = ssl.create_default_context(cafile=SSL_CA_PATH)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False, connect_args={"ssl": ssl_context})
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# 基準日: 12/18（MVPデモ日）- datetime.utcnow() と整合させる
DEMO_DATE = datetime(2025, 12, 18)
# 介入フラグの基準: 14日以上投稿なし
INTERVENTION_DAYS = 14

# 正しい探求フェーズ
PHASES = ["テーマ設定", "課題設定", "情報収集", "整理・分析", "まとめ・表現", "発表準備"]

# 非認知能力ID (1-7)
# 1: 課題設定力, 2: 情報収集力, 3: 巻き込む力, 4: 対話する力, 5: 実行する力, 6: 謙虚である力, 7: 完遂する力
ABILITY_NAMES = {
    1: "課題設定力",
    2: "情報収集力",
    3: "巻き込む力",
    4: "対話する力",
    5: "実行する力",
    6: "謙虚である力",
    7: "完遂する力"
}

# 各生徒の個性（得意な非認知能力を2-3個設定）- バランス調整版
STUDENT_PERSONALITIES = {
    # 既存生徒 (user_id -> info)
    2:  {"name": "新井 太郎", "strong": [1, 2], "theme": "多文化共生", "post_count": 8, "active": True},
    10: {"name": "柳川 健太", "strong": [5, 7], "theme": "再生可能エネルギー", "post_count": 12, "active": True},
    11: {"name": "柳川 優子", "strong": [3, 4], "theme": "空き家問題", "post_count": 15, "active": True},
    14: {"name": "柳川 裕太", "strong": [2, 6], "theme": "フードロス", "post_count": 6, "active": True},
    18: {"name": "伊藤 生徒", "strong": [1, 4, 6], "theme": "高齢者交流", "post_count": 10, "active": True},
    19: {"name": "髙橋 由華", "strong": [3, 5], "theme": "伝統文化継承", "post_count": 4, "active": False},  # 介入フラグ対象
    21: {"name": "江藤 泰平", "strong": [2, 7], "theme": "海洋プラスチック", "post_count": 11, "active": True},
    22: {"name": "田中 美咲", "strong": [1, 3, 5], "theme": "観光まちづくり", "post_count": 9, "active": True},
    23: {"name": "山本 結衣", "strong": [4, 6, 7], "theme": "障がい者共生", "post_count": 7, "active": True},
}

# 新規生徒10人（個性も設定、バランス調整）
NEW_STUDENTS = [
    {"name": "佐藤 一郎", "name_kana": "サトウ イチロウ", "grade": 1, "class": "2", "school_id": "100007", "login": "student10", "email": "student10@test.example.com", "strong": [1, 5], "theme": "地域防災", "post_count": 10, "active": True},
    {"name": "鈴木 花子", "name_kana": "スズキ ハナコ", "grade": 1, "class": "3", "school_id": "100008", "login": "student11", "email": "student11@test.example.com", "strong": [2, 4], "theme": "子どもの居場所", "post_count": 7, "active": True},
    {"name": "田村 健二", "name_kana": "タムラ ケンジ", "grade": 1, "class": "5", "school_id": "100009", "login": "student12", "email": "student12@test.example.com", "strong": [5, 7], "theme": "SNSリテラシー", "post_count": 13, "active": True},
    {"name": "山口 美優", "name_kana": "ヤマグチ ミユ", "grade": 2, "class": "1", "school_id": "200004", "login": "student13", "email": "student13@test.example.com", "strong": [3, 4, 6], "theme": "地域医療", "post_count": 5, "active": True},
    {"name": "中村 翔太", "name_kana": "ナカムラ ショウタ", "grade": 2, "class": "3", "school_id": "200005", "login": "student14", "email": "student14@test.example.com", "strong": [1, 2, 7], "theme": "農業の未来", "post_count": 14, "active": True},
    {"name": "小林 あかり", "name_kana": "コバヤシ アカリ", "grade": 2, "class": "5", "school_id": "200006", "login": "student15", "email": "student15@test.example.com", "strong": [3, 5], "theme": "ジェンダー平等", "post_count": 4, "active": False},  # 介入フラグ対象
    {"name": "加藤 大輝", "name_kana": "カトウ ダイキ", "grade": 3, "class": "2", "school_id": "300001", "login": "student16", "email": "student16@test.example.com", "strong": [2, 6, 7], "theme": "公共交通", "post_count": 11, "active": True},
    {"name": "吉川 理沙", "name_kana": "ヨシカワ リサ", "grade": 3, "class": "4", "school_id": "300002", "login": "student17", "email": "student17@test.example.com", "strong": [1, 4], "theme": "動物福祉", "post_count": 8, "active": True},
    {"name": "松本 陽斗", "name_kana": "マツモト ハルト", "grade": 3, "class": "6", "school_id": "300003", "login": "student18", "email": "student18@test.example.com", "strong": [5, 6, 7], "theme": "地産地消", "post_count": 15, "active": True},
    {"name": "渡辺 さくら", "name_kana": "ワタナベ サクラ", "grade": 1, "class": "6", "school_id": "100010", "login": "student19", "email": "student19@test.example.com", "strong": [2, 3, 4], "theme": "読書文化", "post_count": 6, "active": False},  # 介入フラグ対象
]

# 各テーマの投稿テンプレート（フェーズごと）
def generate_posts_for_theme(theme, post_count):
    """テーマに応じた投稿を生成（フェーズは順番に進む）"""
    posts = []

    # テーマごとの基本コンテンツ
    THEME_CONTENT = {
        "多文化共生": {
            "テーマ設定": [
                {"problem": "外国にルーツを持つ同級生が学校生活で困っていることは何か", "c1": "クラスに外国から転校してきた生徒がいて、言葉や文化の違いで困っているようです。", "c2": "自分に何かできることはないかと考えました。", "c3": "まずは現状を知ることから始めます。"},
                {"problem": "なぜ外国人と日本人の間に壁があるように感じるのか", "c1": "留学生との交流イベントに参加しましたが、なかなか打ち解けられませんでした。", "c2": "言葉の壁だけでなく、文化の違いもあると感じました。", "c3": "どうすれば壁を低くできるか考えたいです。"},
            ],
            "課題設定": [
                {"problem": "外国にルーツを持つ生徒が直面する具体的な課題を明らかにしたい", "c1": "インタビューを通じて課題を整理しました。", "c2": "言語、食事、宗教の3つが大きな課題だとわかりました。", "c3": "それぞれの課題に対する解決策を考えます。"},
            ],
            "情報収集": [
                {"problem": "外国にルーツを持つ生徒へのサポート制度について調べたい", "c1": "国際交流協会を訪問し、サポート制度について聞きました。", "c2": "日本語教室や相談窓口があることを知りました。", "c3": "学校でできる支援も調べてみます。"},
                {"problem": "他校ではどんな多文化共生の取り組みをしているか", "c1": "近隣の高校に問い合わせて、取り組みを教えてもらいました。", "c2": "「世界の料理を給食で出す」「母国語で発表する機会を作る」などの事例がありました。", "c3": "参考にできるものを探します。"},
            ],
            "整理・分析": [
                {"problem": "集めた情報から学校でできる取り組みを整理したい", "c1": "調査結果をまとめ、実現可能性で分類しました。", "c2": "すぐできること、準備が必要なこと、長期的な取り組みに分けました。", "c3": "優先順位をつけて提案します。"},
            ],
            "まとめ・表現": [
                {"problem": "多文化共生の取り組み提案をまとめたい", "c1": "「やさしい日本語プリント」の作成を最初の取り組みとして提案書をまとめました。", "c2": "先生にも見てもらい、フィードバックをもらいました。", "c3": "より分かりやすい資料に改善します。"},
            ],
            "発表準備": [
                {"problem": "提案を効果的に伝えるプレゼンを作りたい", "c1": "スライドを作成し、発表練習を始めました。", "c2": "友達に聞いてもらい、わかりにくい部分を修正しました。", "c3": "本番に向けて最終調整します。"},
            ],
        },
        "再生可能エネルギー": {
            "テーマ設定": [
                {"problem": "私たちの地域でどんな再生可能エネルギーが活用できるか", "c1": "SDGsの授業で再生可能エネルギーについて学びました。", "c2": "自分の地域ではどうなっているか気になりました。", "c3": "地域に合ったエネルギーを調べます。"},
            ],
            "課題設定": [
                {"problem": "地域の再生可能エネルギー導入が進まない理由を明らかにしたい", "c1": "市役所のデータを見ると、導入率が低いことがわかりました。", "c2": "なぜ進まないのか原因を特定したいです。", "c3": "関係者にインタビューを行います。"},
            ],
            "情報収集": [
                {"problem": "再生可能エネルギーの種類と特徴を詳しく知りたい", "c1": "太陽光、風力、水力、地熱について調べました。", "c2": "それぞれメリット・デメリットがあることがわかりました。", "c3": "地域の特性に合うものを検討します。"},
                {"problem": "実際に再生可能エネルギーを導入している家庭の声を聞きたい", "c1": "ソーラーパネルを設置している家庭を訪問しました。", "c2": "電気代の削減効果や設置の苦労を聞けました。", "c3": "メリットをもっと広めたいです。"},
            ],
            "整理・分析": [
                {"problem": "収集した情報から地域に最適なエネルギーを分析したい", "c1": "地域の日照時間、風況、河川のデータを整理しました。", "c2": "太陽光が最も適していることがわかりました。", "c3": "普及のための提案を考えます。"},
            ],
            "まとめ・表現": [
                {"problem": "再生可能エネルギー普及の提案をまとめたい", "c1": "「高校生ができる再エネ普及活動」としてまとめました。", "c2": "SNS発信、小学校への出前授業、文化祭での展示を提案します。", "c3": "実現に向けて動きます。"},
            ],
            "発表準備": [
                {"problem": "提案を地域に届けるプレゼンを準備したい", "c1": "市の環境イベントで発表する機会をもらいました。", "c2": "グラフや写真を使って分かりやすく説明します。", "c3": "練習を重ねています。"},
            ],
        },
        "空き家問題": {
            "テーマ設定": [
                {"problem": "地域の空き家が増えている原因は何か", "c1": "通学路に空き家が増えていて気になっていました。", "c2": "なぜ空き家が増えているのか調べたいです。", "c3": "まずは実態を確認します。"},
            ],
            "課題設定": [
                {"problem": "空き家が放置される理由を明らかにしたい", "c1": "市役所で空き家対策について聞きました。", "c2": "「遠方に住んでいる」「解体費用が高い」という理由が多いそうです。", "c3": "所有者の事情を詳しく調べます。"},
            ],
            "情報収集": [
                {"problem": "空き家活用の成功事例を集めたい", "c1": "インターネットや本で事例を調べました。", "c2": "コミュニティカフェ、シェアオフィス、学生向けシェアハウスなどの例がありました。", "c3": "地域に合う活用法を考えます。"},
                {"problem": "地域住民のニーズを把握したい", "c1": "アンケートを実施しました。", "c2": "「子どもの遊び場」「高齢者の憩いの場」へのニーズが高かったです。", "c3": "ニーズに合った提案を考えます。"},
            ],
            "整理・分析": [
                {"problem": "空き家活用の可能性を分析したい", "c1": "空き家の状態、所有者の意向、地域ニーズを整理しました。", "c2": "マッチングの仕組みが必要だと考えました。", "c3": "提案書を作成します。"},
            ],
            "まとめ・表現": [
                {"problem": "空き家活用の提案をまとめたい", "c1": "「空き家と地域をつなぐマッチングプロジェクト」として提案をまとめました。", "c2": "自治会と市役所に提案します。", "c3": "フィードバックをもらいます。"},
            ],
            "発表準備": [
                {"problem": "自治会で発表する準備をしたい", "c1": "自治会の会合で発表させてもらうことになりました。", "c2": "地図や写真を使って説明します。", "c3": "質問への回答も準備します。"},
            ],
        },
        "フードロス": {
            "テーマ設定": [
                {"problem": "身の回りでどれくらいの食品が捨てられているか", "c1": "家で賞味期限切れの食品を捨てることがあり、もったいないと感じました。", "c2": "日本のフードロスが年間約600万トンと知りました。", "c3": "自分にできることを考えたいです。"},
            ],
            "課題設定": [
                {"problem": "フードロスの主な原因を特定したい", "c1": "フードロスの原因を「買いすぎ」「作りすぎ」「食べ残し」に分類しました。", "c2": "それぞれの対策を考えます。", "c3": "データを集めて分析します。"},
            ],
            "情報収集": [
                {"problem": "学校給食の残食状況を調べたい", "c1": "栄養士さんにお願いして残食データを見せてもらいました。", "c2": "野菜を使った料理の残食が多いことがわかりました。", "c3": "原因を深掘りします。"},
            ],
            "整理・分析": [
                {"problem": "残食データを分析して傾向を見つけたい", "c1": "曜日別、メニュー別に残食率を分析しました。", "c2": "月曜日と苦手な野菜の日に残食が多いことがわかりました。", "c3": "改善策を考えます。"},
            ],
            "まとめ・表現": [
                {"problem": "フードロス削減の提案をまとめたい", "c1": "給食委員会と協力して「残さず食べようキャンペーン」を企画しました。", "c2": "啓発ポスターも作成します。", "c3": "効果を測定する方法も考えます。"},
            ],
            "発表準備": [
                {"problem": "全校集会で発表する準備をしたい", "c1": "全校集会でフードロスについて発表することになりました。", "c2": "クイズ形式で関心を引く内容にします。", "c3": "リハーサルを重ねています。"},
            ],
        },
        "高齢者交流": {
            "テーマ設定": [
                {"problem": "一人暮らしの高齢者が孤立しないためにできることは何か", "c1": "祖父母と話す機会が減り、一人暮らしの高齢者の孤立が気になりました。", "c2": "若者と高齢者がもっと交流できる方法を考えたいです。", "c3": "地域の高齢者施設を訪問します。"},
            ],
            "課題設定": [
                {"problem": "高齢者と若者の交流が少ない原因を明らかにしたい", "c1": "デイサービスセンターでスタッフにお話を聞きました。", "c2": "機会がないことが一番の原因だとわかりました。", "c3": "交流の機会を作る方法を考えます。"},
            ],
            "情報収集": [
                {"problem": "他校の高齢者交流の事例を調べたい", "c1": "インターネットで事例を調べました。", "c2": "定期的な訪問交流、スマホ教室、昔遊び体験などがありました。", "c3": "自分たちにできることを選びます。"},
                {"problem": "高齢者の方のニーズを聞きたい", "c1": "施設でアンケートを取りました。", "c2": "「昔の話を聞いてほしい」という声が多かったです。", "c3": "それに応える企画を考えます。"},
            ],
            "整理・分析": [
                {"problem": "交流会の内容を具体的に決めたい", "c1": "高齢者のニーズと高校生ができることを照らし合わせました。", "c2": "月1回の「むかし話を聞く会」を企画します。", "c3": "施設に提案します。"},
            ],
            "まとめ・表現": [
                {"problem": "交流会の報告をまとめたい", "c1": "第1回の交流会を開催し、報告書をまとめました。", "c2": "高齢者8名、高校生5名が参加しました。", "c3": "継続のための改善点も記載します。"},
            ],
            "発表準備": [
                {"problem": "活動報告のプレゼンを準備したい", "c1": "学年発表会で活動を報告します。", "c2": "写真や動画を使って臨場感を伝えます。", "c3": "後輩への引き継ぎも意識します。"},
            ],
        },
        "伝統文化継承": {
            "テーマ設定": [
                {"problem": "地域の祭りの参加者が減っている原因は何か", "c1": "地元の祭りに参加する人が年々減っています。", "c2": "伝統文化が失われていくことに危機感を感じました。", "c3": "関係者に話を聞きます。"},
            ],
            "課題設定": [
                {"problem": "若者が祭りに参加しない理由を明らかにしたい", "c1": "保存会の方にインタビューしました。", "c2": "「祭りの意味を知らない」「練習時間が取れない」という声がありました。", "c3": "解決策を考えます。"},
            ],
            "情報収集": [
                {"problem": "若者を集めている祭りの事例を調べたい", "c1": "SNSで祭りを発信して若者を集めている地域を見つけました。", "c2": "動画投稿が効果的だそうです。", "c3": "参考にします。"},
            ],
            "整理・分析": [
                {"problem": "祭りの魅力を伝える方法を整理したい", "c1": "伝える方法として、動画、体験ワークショップ、学校授業を考えました。", "c2": "まずは動画から始めることにしました。", "c3": "撮影計画を立てます。"},
            ],
        },
        "海洋プラスチック": {
            "テーマ設定": [
                {"problem": "海洋プラスチック問題が身近な海にどう影響しているか", "c1": "海洋プラスチック問題のニュースを見て、地域の海が気になりました。", "c2": "マイクロプラスチックが魚に蓄積されると知りました。", "c3": "近くの海岸で調査します。"},
            ],
            "課題設定": [
                {"problem": "海岸ごみの発生源を特定したい", "c1": "海岸清掃ボランティアに参加し、ごみを分類しました。", "c2": "ペットボトル、レジ袋、漁具が多かったです。", "c3": "発生源ごとの対策を考えます。"},
            ],
            "情報収集": [
                {"problem": "プラスチックごみ削減の先進事例を調べたい", "c1": "環境団体のレポートを読みました。", "c2": "レジ袋有料化の効果や、代替素材の開発が進んでいることを知りました。", "c3": "学校でできることを探します。"},
                {"problem": "マイクロプラスチックの調査方法を学びたい", "c1": "海洋ごみの専門家にお話を聞きました。", "c2": "砂浜からマイクロプラスチックを分離する方法を教わりました。", "c3": "実際に調査してみます。"},
            ],
            "整理・分析": [
                {"problem": "調査結果を分析してまとめたい", "c1": "海岸ごみの種類と量をグラフにまとめました。", "c2": "季節や天候による変化も分析しました。", "c3": "報告書を作成します。"},
            ],
            "まとめ・表現": [
                {"problem": "プラスチック削減の提案をまとめたい", "c1": "学校でできる取り組みとして「マイボトルウィーク」を提案しました。", "c2": "生徒会に承認をもらいました。", "c3": "実施に向けて準備します。"},
            ],
            "発表準備": [
                {"problem": "環境発表会の準備をしたい", "c1": "市の環境発表会に参加します。", "c2": "調査データとマイボトルウィークの成果を報告します。", "c3": "ポスターも作成中です。"},
            ],
        },
        "観光まちづくり": {
            "テーマ設定": [
                {"problem": "地域の観光スポットが知られていない原因は何か", "c1": "私の町には古い神社や自然豊かな山がありますが、観光客が少ないです。", "c2": "もっと多くの人に魅力を知ってほしいです。", "c3": "観光協会を訪問します。"},
            ],
            "課題設定": [
                {"problem": "観光客を増やすための課題を明確にしたい", "c1": "観光協会で年間観光客数と取り組みを聞きました。", "c2": "SNS発信が弱いこと、若者向けコンテンツが少ないことが課題だそうです。", "c3": "改善策を考えます。"},
            ],
            "情報収集": [
                {"problem": "SNSで観光PRに成功している事例を調べたい", "c1": "インスタグラムで人気の観光地を調べました。", "c2": "「映える」スポットの紹介が効果的だとわかりました。", "c3": "地元の映えスポットを探します。"},
            ],
            "整理・分析": [
                {"problem": "地元の観光資源を整理したい", "c1": "地元を歩いて観光スポットをリストアップしました。", "c2": "神社、山、グルメ、イベントの4カテゴリーに分けました。", "c3": "マップにまとめます。"},
            ],
            "まとめ・表現": [
                {"problem": "観光マップを完成させたい", "c1": "デザインソフトで観光マップを作成しました。", "c2": "写真と店主さんのコメントを入れました。", "c3": "観光協会に見てもらいます。"},
            ],
            "発表準備": [
                {"problem": "観光マップの発表準備をしたい", "c1": "観光協会のイベントで配布することになりました。", "c2": "説明用のミニプレゼンも準備します。", "c3": "印刷の最終確認をします。"},
            ],
        },
        "障がい者共生": {
            "テーマ設定": [
                {"problem": "障がいのある人が日常生活で困っていることは何か", "c1": "パラリンピックを見て、障がいがあっても活躍できることを知りました。", "c2": "でも日常生活ではどうなんだろうと思いました。", "c3": "障がいのある方の話を聞きたいです。"},
            ],
            "課題設定": [
                {"problem": "学校のバリアフリー状況を調べたい", "c1": "障がい者支援センターを訪問しました。", "c2": "「特別扱いではなく、普通に接してほしい」という言葉が印象的でした。", "c3": "学校のバリアフリーも調査します。"},
            ],
            "情報収集": [
                {"problem": "車椅子体験をして困りごとを実感したい", "c1": "車椅子を借りて校内を移動してみました。", "c2": "普段気づかない段差や狭い場所があることを実感しました。", "c3": "改善点をまとめます。"},
            ],
            "整理・分析": [
                {"problem": "バリアフリーの改善点を整理したい", "c1": "校内を細かく調査し、改善点をリストにしました。", "c2": "優先度をつけて学校に提案します。", "c3": "マップも作成します。"},
            ],
            "まとめ・表現": [
                {"problem": "バリアフリーマップを完成させたい", "c1": "校内のバリアフリーマップを作成しました。", "c2": "車椅子で通れる経路やエレベーターの位置を記載しました。", "c3": "学校に提出します。"},
            ],
            "発表準備": [
                {"problem": "新入生に向けた説明の準備をしたい", "c1": "バリアフリーマップが新入生オリエンテーションで配布されることになりました。", "c2": "説明資料も作成します。", "c3": "障がいのある方にも確認してもらいます。"},
            ],
        },
        "地域防災": {
            "テーマ設定": [
                {"problem": "自分の住む地域はどんな災害リスクがあるか", "c1": "大きな地震のニュースを見て、防災について考えるようになりました。", "c2": "家族で避難場所を確認したことがありません。", "c3": "ハザードマップを確認します。"},
            ],
            "課題設定": [
                {"problem": "若い世代の防災意識が低い原因を明らかにしたい", "c1": "市役所の防災課を訪問しました。", "c2": "若い世代の防災訓練参加率が低いことが課題だそうです。", "c3": "意識を高める方法を考えます。"},
            ],
            "情報収集": [
                {"problem": "過去の災害から学べることを調べたい", "c1": "過去の災害で実際に役立ったものを調べました。", "c2": "防災グッズリストを作成しました。", "c3": "みんなに共有します。"},
                {"problem": "防災アプリや訓練の事例を集めたい", "c1": "他の地域の防災アプリを調べました。", "c2": "ゲーム感覚で学べるものが効果的だとわかりました。", "c3": "参考にします。"},
            ],
            "整理・分析": [
                {"problem": "高校生に響く防災啓発の方法を分析したい", "c1": "防災意識を高める方法をリストアップしました。", "c2": "防災クイズアプリが効果的だと考えました。", "c3": "プロトタイプを作ります。"},
            ],
            "まとめ・表現": [
                {"problem": "防災クイズアプリを完成させたい", "c1": "プログラミングを学びながらアプリを作りました。", "c2": "クラスメイトに試してもらいました。", "c3": "フィードバックを反映します。"},
            ],
            "発表準備": [
                {"problem": "防災訓練でアプリを使ってもらう準備をしたい", "c1": "学校の防災訓練でアプリを使ってもらえることになりました。", "c2": "操作説明の資料を作ります。", "c3": "当日のサポート体制も準備します。"},
            ],
        },
        "子どもの居場所": {
            "テーマ設定": [
                {"problem": "放課後に一人で過ごす子どもはどれくらいいるか", "c1": "共働き家庭が増え、放課後に一人で過ごす子どもが多いと聞きました。", "c2": "子ども食堂やフリースペースの活動に興味を持ちました。", "c3": "地域の状況を調べます。"},
            ],
            "課題設定": [
                {"problem": "子どもの居場所づくりの課題を明らかにしたい", "c1": "地域の子ども食堂を訪問しました。", "c2": "ボランティアスタッフの確保が課題だとわかりました。", "c3": "高校生が関わる方法を考えます。"},
            ],
            "情報収集": [
                {"problem": "高校生が関わっている事例を調べたい", "c1": "インターネットで事例を調べました。", "c2": "学習支援、遊び相手、イベント企画などがありました。", "c3": "自分にできることを選びます。"},
            ],
            "整理・分析": [
                {"problem": "高校生が関われる活動を整理したい", "c1": "子ども食堂のスタッフと相談しました。", "c2": "月2回の学習支援ボランティアをすることにしました。", "c3": "仲間を集めます。"},
            ],
            "まとめ・表現": [
                {"problem": "ボランティア活動の報告をまとめたい", "c1": "3回の活動を終え、報告書をまとめました。", "c2": "子どもたちの笑顔が印象的でした。", "c3": "継続のための計画も記載します。"},
            ],
        },
        "SNSリテラシー": {
            "テーマ設定": [
                {"problem": "SNSでトラブルに巻き込まれないためには何が必要か", "c1": "友達がSNSでのトラブルに巻き込まれました。", "c2": "SNSの使い方について考えるようになりました。", "c3": "同世代の実態を調べます。"},
            ],
            "課題設定": [
                {"problem": "高校生のSNS利用の課題を明らかにしたい", "c1": "クラスメイトにアンケートを取りました。", "c2": "1日3時間以上使う人が40%もいて驚きました。", "c3": "問題点を整理します。"},
            ],
            "情報収集": [
                {"problem": "SNS依存やトラブルの事例を集めたい", "c1": "情報モラル教育の論文を読みました。", "c2": "SNS依存のチェックリストを見つけました。", "c3": "みんなに共有したいです。"},
                {"problem": "健全なSNS利用の方法を調べたい", "c1": "専門家の記事を読みました。", "c2": "時間制限やデトックスの効果について学びました。", "c3": "自分でも試してみます。"},
            ],
            "整理・分析": [
                {"problem": "SNS利用の改善策を分析したい", "c1": "自分で1週間のSNS制限チャレンジをしました。", "c2": "時間が増えて充実感がありました。", "c3": "体験をまとめます。"},
            ],
            "まとめ・表現": [
                {"problem": "SNSリテラシーの啓発資料を作りたい", "c1": "自分の体験をまとめた発表資料を作りました。", "c2": "クラスで発表しました。", "c3": "反応が良かったので広げたいです。"},
            ],
            "発表準備": [
                {"problem": "全校向けの啓発活動を準備したい", "c1": "情報委員会と協力してポスターを作成しました。", "c2": "校内に掲示しています。", "c3": "効果を測定します。"},
            ],
        },
        "地域医療": {
            "テーマ設定": [
                {"problem": "地域の病院が減っているのはなぜか", "c1": "祖父母の家の近くの病院が閉院しました。", "c2": "地方の医療問題に興味を持ちました。", "c3": "地域の現状を調べます。"},
            ],
            "課題設定": [
                {"problem": "地域医療の課題を明らかにしたい", "c1": "市の保健センターを訪問しました。", "c2": "医師不足、高齢化、経営難が課題だとわかりました。", "c3": "住民ができることを考えます。"},
            ],
            "情報収集": [
                {"problem": "地域医療を守る取り組みを調べたい", "c1": "オンライン診療や訪問医療について調べました。", "c2": "新しい取り組みが始まっていることを知りました。", "c3": "もっと詳しく調べます。"},
            ],
            "整理・分析": [
                {"problem": "住民ができることを整理したい", "c1": "かかりつけ医を持つこと、予防医療の意識、医療への理解を整理しました。", "c2": "若い世代への啓発が必要だと思いました。", "c3": "啓発方法を考えます。"},
            ],
            "まとめ・表現": [
                {"problem": "地域医療に関する啓発資料を作りたい", "c1": "地域医療の大切さを伝えるリーフレットを作成しました。", "c2": "保健センターに置いてもらえることになりました。", "c3": "反応を見ます。"},
            ],
        },
        "農業の未来": {
            "テーマ設定": [
                {"problem": "なぜ若い人は農業をやりたがらないのか", "c1": "祖父母が農業をしていますが、後継者がいないと言っていました。", "c2": "農業の担い手が減っている原因を考えたいです。", "c3": "農家さんに話を聞きます。"},
            ],
            "課題設定": [
                {"problem": "若者が就農しない理由を明らかにしたい", "c1": "JAを訪問しました。", "c2": "「収入が不安定」「体力的にきつい」が避ける理由だそうです。", "c3": "魅力を高める方法を考えます。"},
            ],
            "情報収集": [
                {"problem": "スマート農業の事例を調べたい", "c1": "ドローンを使った農業をしている農家を訪問しました。", "c2": "最新技術で効率化できることを知りました。", "c3": "もっと事例を集めます。"},
                {"problem": "6次産業化の成功事例を調べたい", "c1": "加工・販売まで手がける農家を取材しました。", "c2": "収入が安定し、やりがいも増えたそうです。", "c3": "参考にします。"},
            ],
            "整理・分析": [
                {"problem": "農業の魅力を整理したい", "c1": "スマート農業、6次産業化、地産地消をキーワードに整理しました。", "c2": "「農業も IT を使えばカッコいい仕事になる」と思いました。", "c3": "同世代に伝えたいです。"},
            ],
            "まとめ・表現": [
                {"problem": "農業の魅力を伝える資料を作りたい", "c1": "農業体験イベントを企画しました。", "c2": "クラスメイトを誘って参加しました。", "c3": "体験レポートをSNSで発信します。"},
            ],
            "発表準備": [
                {"problem": "農業イベントの報告発表を準備したい", "c1": "体験イベントの報告を学年集会で行います。", "c2": "参加者の感想や写真を使います。", "c3": "次回イベントの告知もします。"},
            ],
        },
        "ジェンダー平等": {
            "テーマ設定": [
                {"problem": "学校生活の中にあるジェンダーバイアスとは何か", "c1": "「女子だから」「男子だから」という言葉に違和感を感じていました。", "c2": "無意識の偏見について調べたいです。", "c3": "学校生活の中で探してみます。"},
            ],
            "課題設定": [
                {"problem": "学校にあるジェンダーに関する問題を特定したい", "c1": "クラスメイトにアンケートを取りました。", "c2": "「体育の授業で男女で分けられる」「生徒会長は男子が多い」という声がありました。", "c3": "解決策を考えます。"},
            ],
            "情報収集": [
                {"problem": "他校のジェンダー教育の事例を調べたい", "c1": "他校の取り組みを調べました。", "c2": "制服選択制を導入している学校がありました。", "c3": "参考にします。"},
            ],
            "整理・分析": [
                {"problem": "学校でできる取り組みを整理したい", "c1": "意識啓発ポスター、LHRでの議論、制服選択制を考えました。", "c2": "まずはLHRから始めます。", "c3": "生徒会に相談します。"},
            ],
        },
        "公共交通": {
            "テーマ設定": [
                {"problem": "バスや電車が減って困っている人はどれくらいいるか", "c1": "おばあちゃんの家の近くのバス路線が廃止になりました。", "c2": "地方の公共交通問題を考えたいです。", "c3": "地域の現状を調べます。"},
            ],
            "課題設定": [
                {"problem": "公共交通が衰退している原因を明らかにしたい", "c1": "市役所の交通政策課を訪問しました。", "c2": "利用者減少、運転手不足、採算性が原因だそうです。", "c3": "対策を調べます。"},
            ],
            "情報収集": [
                {"problem": "公共交通を維持している先進事例を調べたい", "c1": "住民がNPOを作って運営しているバスの事例を見つけました。", "c2": "デマンドタクシーの導入事例もありました。", "c3": "詳しく調べます。"},
                {"problem": "高校生の公共交通利用実態を調べたい", "c1": "クラスメイトにアンケートを取りました。", "c2": "バスの乗り方がわからない人が多いことがわかりました。", "c3": "利用促進策を考えます。"},
            ],
            "整理・分析": [
                {"problem": "利用促進策を整理したい", "c1": "高校生向けのバス利用ガイドを作ることにしました。", "c2": "路線図と乗り方を分かりやすく説明します。", "c3": "デザインを考えます。"},
            ],
            "まとめ・表現": [
                {"problem": "バス利用ガイドを完成させたい", "c1": "ガイドを作成し、学校で配布しました。", "c2": "「わかりやすい」という声をもらいました。", "c3": "市にも提供します。"},
            ],
            "発表準備": [
                {"problem": "市のイベントで発表する準備をしたい", "c1": "市のイベントで発表する機会をもらいました。", "c2": "高校生の視点を伝えます。", "c3": "スライドを最終確認します。"},
            ],
        },
        "動物福祉": {
            "テーマ設定": [
                {"problem": "ペットの殺処分をなくすには何が必要か", "c1": "殺処分される犬猫が年間数万頭いることを知り、ショックを受けました。", "c2": "最後まで責任を持って飼うことの大切さを伝えたいです。", "c3": "動物愛護センターを訪問します。"},
            ],
            "課題設定": [
                {"problem": "ペットが捨てられる理由を明らかにしたい", "c1": "動物愛護センターで話を聞きました。", "c2": "「引っ越し」「飼い主の高齢化」「想像と違った」が理由だそうです。", "c3": "予防策を考えます。"},
            ],
            "情報収集": [
                {"problem": "保護団体の活動を調べたい", "c1": "保護団体のボランティアに参加しました。", "c2": "里親探しの大変さを実感しました。", "c3": "自分にできることを探します。"},
            ],
            "整理・分析": [
                {"problem": "高校生ができる活動を整理したい", "c1": "啓発活動、ボランティア、里親募集の拡散を考えました。", "c2": "まずは写真展を企画します。", "c3": "保護犬・保護猫のストーリーを紹介します。"},
            ],
            "まとめ・表現": [
                {"problem": "写真展を開催したい", "c1": "文化祭で写真展を開催しました。", "c2": "多くの人が見に来てくれました。", "c3": "アンケートで反応を確認します。"},
            ],
        },
        "地産地消": {
            "テーマ設定": [
                {"problem": "地元の食材はどれくらい使われているか", "c1": "給食の食材がどこから来ているか気になりました。", "c2": "地産地消が環境にも経済にも良いと知りました。", "c3": "地域の農産物を調べます。"},
            ],
            "課題設定": [
                {"problem": "地産地消が進まない理由を明らかにしたい", "c1": "JAや直売所を訪問しました。", "c2": "「量が安定しない」「規格が揃わない」が課題だそうです。", "c3": "解決策を考えます。"},
            ],
            "情報収集": [
                {"problem": "地産地消を進めている事例を調べたい", "c1": "地産地消に成功している学校給食を調べました。", "c2": "農家との直接契約が効果的だとわかりました。", "c3": "参考にします。"},
                {"problem": "地元農家の声を聞きたい", "c1": "農家を訪問しました。", "c2": "「もっと知ってもらいたい」という声がありました。", "c3": "PRの方法を考えます。"},
            ],
            "整理・分析": [
                {"problem": "地産地消を広める方法を整理したい", "c1": "地元食材フェア、レシピ開発、SNS発信を考えました。", "c2": "料理コンテストを企画します。", "c3": "家庭科の先生に相談します。"},
            ],
            "まとめ・表現": [
                {"problem": "料理コンテストを開催したい", "c1": "クラス対抗の料理コンテストを開催しました。", "c2": "優秀レシピは給食に採用されることになりました。", "c3": "報告書をまとめます。"},
            ],
            "発表準備": [
                {"problem": "活動報告の発表を準備したい", "c1": "学年発表会で報告します。", "c2": "写真と優秀レシピを紹介します。", "c3": "継続の呼びかけもします。"},
            ],
        },
        "読書文化": {
            "テーマ設定": [
                {"problem": "若い世代の読書離れはなぜ起きているか", "c1": "図書館の利用者が減っていると司書さんから聞きました。", "c2": "本を読むことの楽しさを伝えたいです。", "c3": "同世代の読書習慣を調べます。"},
            ],
            "課題設定": [
                {"problem": "高校生が本を読まない理由を明らかにしたい", "c1": "アンケートを実施しました。", "c2": "「時間がない」「何を読めばいいかわからない」が多かったです。", "c3": "解決策を考えます。"},
            ],
            "情報収集": [
                {"problem": "読書を促進する取り組みを調べたい", "c1": "図書館の取り組みを調べました。", "c2": "ビブリオバトルやおすすめ本コーナーが効果的だそうです。", "c3": "参考にします。"},
            ],
            "整理・分析": [
                {"problem": "高校生に読書を勧める方法を整理したい", "c1": "ビブリオバトル、おすすめ本リスト、読書会を考えました。", "c2": "まずはおすすめ本リストを作ります。", "c3": "図書委員会と協力します。"},
            ],
        },
    }

    # テーマに対応するコンテンツを取得
    if theme not in THEME_CONTENT:
        # 汎用コンテンツを生成
        return generate_generic_posts(theme, post_count)

    theme_data = THEME_CONTENT[theme]

    # フェーズ順に投稿を生成
    phase_index = 0
    for i in range(post_count):
        # 投稿が進むにつれてフェーズを進める
        current_phase = PHASES[min(phase_index, len(PHASES) - 1)]

        if current_phase in theme_data and theme_data[current_phase]:
            # ランダムに内容を選択
            content = random.choice(theme_data[current_phase])
            posts.append({
                "phase": current_phase,
                "problem": content["problem"],
                "content_1": content["c1"],
                "content_2": content["c2"],
                "content_3": content["c3"]
            })
        else:
            # フェーズのコンテンツがない場合は前のフェーズのものを使う
            for prev_phase in reversed(PHASES[:phase_index]):
                if prev_phase in theme_data and theme_data[prev_phase]:
                    content = random.choice(theme_data[prev_phase])
                    posts.append({
                        "phase": current_phase,
                        "problem": content["problem"] + "（続き）",
                        "content_1": "前回の調査を踏まえて、さらに深掘りしました。",
                        "content_2": content["c2"],
                        "content_3": "次のステップに向けて準備を進めています。"
                    })
                    break

        # 投稿数に応じてフェーズを進める
        if i > 0 and i % max(1, post_count // len(PHASES)) == 0:
            phase_index = min(phase_index + 1, len(PHASES) - 1)

    return posts


def generate_generic_posts(theme, post_count):
    """汎用的な投稿を生成"""
    posts = []
    phase_index = 0

    for i in range(post_count):
        current_phase = PHASES[min(phase_index, len(PHASES) - 1)]

        posts.append({
            "phase": current_phase,
            "problem": f"{theme}について{current_phase}段階の問いを立てています",
            "content_1": f"{theme}に関する{current_phase}の活動をしています。",
            "content_2": f"様々な情報を集め、分析を進めています。",
            "content_3": f"次のステップに向けて準備中です。"
        })

        if i > 0 and i % max(1, post_count // len(PHASES)) == 0:
            phase_index = min(phase_index + 1, len(PHASES) - 1)

    return posts


# 感謝の手紙テンプレート
THANKS_TEMPLATES = [
    {"content_1": "探求学習のインタビューに協力してくれて",
     "content_2": "お忙しい中、時間を作って私の質問に丁寧に答えてくれてありがとう。おかげで調査がとても進みました。"},
    {"content_1": "フィールドワークに一緒に行ってくれて",
     "content_2": "一人では行きづらかった場所に一緒に来てくれてありがとう。あなたがいてくれたおかげで、緊張せずに取材ができました。"},
    {"content_1": "発表の練習に付き合ってくれて",
     "content_2": "何度も発表を聞いてくれてありがとう。的確なアドバイスのおかげで、自信を持って本番に臨めました。"},
    {"content_1": "資料作りを手伝ってくれて",
     "content_2": "見やすいポスターを作ってくれてありがとう。おかげでとても分かりやすい資料になりました。"},
    {"content_1": "探求テーマについて相談に乗ってくれて",
     "content_2": "行き詰まっていた時に、一緒に考えてくれてありがとう。新しい方向性が見えました。"},
    {"content_1": "アンケート調査に協力してくれて",
     "content_2": "クラスのみんなにアンケートをお願いするのを手伝ってくれてありがとう。たくさんの回答を集められました。"},
    {"content_1": "グループワークをまとめてくれて",
     "content_2": "みんなの意見をまとめて、チームを引っ張ってくれてありがとう。スムーズに進みました。"},
    {"content_1": "参考資料を教えてくれて",
     "content_2": "自分では見つけられなかった本や論文を教えてくれてありがとう。とても参考になりました。"},
    {"content_1": "プレゼンのデザインを手伝ってくれて",
     "content_2": "スライドのデザインを一緒に考えてくれてありがとう。見やすく伝わりやすい資料になりました。"},
    {"content_1": "励ましの言葉をかけてくれて",
     "content_2": "探求が上手くいかなくて落ち込んでいた時、声をかけてくれてありがとう。前向きになれました。"},
]


async def main():
    async with AsyncSessionLocal() as db:
        print("=== 探求学習テストデータ作成開始 ===\n")

        # 1. 既存の投稿・手紙を削除
        print("1. 既存データを削除...")
        await db.execute(text("DELETE FROM post_ability_points"))
        await db.execute(text("DELETE FROM thanks_letter_ability_points"))
        await db.execute(text("DELETE FROM thanks_letters"))
        await db.execute(text("DELETE FROM posts"))
        await db.commit()
        print("   完了")

        # 2. 新規生徒を作成（既存の場合はスキップ）
        print("\n2. 新規生徒アカウント作成...")
        password_hash = pwd_context.hash("test1234")
        new_student_info = {}

        for student in NEW_STUDENTS:
            # 既存チェック
            result = await db.execute(text(
                "SELECT user_id FROM user_local_accounts WHERE login_id = :login_id"
            ), {"login_id": student["login"]})
            existing = result.fetchone()

            if existing:
                user_id = existing[0]
                print(f"   {student['name']} (ID:{user_id}, login:{student['login']}) 既存")
            else:
                await db.execute(text("""
                    INSERT INTO users (school_person_id, role, full_name, full_name_kana, email, grade, class_name, gender, is_active, is_deleted, created_at, updated_at)
                    VALUES (:school_id, 'student', :name, :name_kana, :email, :grade, :class_name, 'unknown', TRUE, FALSE, NOW(), NOW())
                """), {"school_id": student["school_id"], "name": student["name"], "name_kana": student["name_kana"],
                       "email": student["email"], "grade": student["grade"], "class_name": student["class"]})

                result = await db.execute(text("SELECT LAST_INSERT_ID()"))
                user_id = result.scalar()

                await db.execute(text("""
                    INSERT INTO user_local_accounts (user_id, login_id, password_hash, created_at, updated_at)
                    VALUES (:user_id, :login_id, :password_hash, NOW(), NOW())
                """), {"user_id": user_id, "login_id": student["login"], "password_hash": password_hash})
                print(f"   {student['name']} (ID:{user_id}, login:{student['login']}) 作成完了")

            new_student_info[user_id] = {
                "name": student["name"],
                "strong": student["strong"],
                "theme": student["theme"],
                "post_count": student["post_count"],
                "active": student["active"]
            }

        await db.commit()

        # 全生徒情報をまとめる
        all_students = {}
        for user_id, info in STUDENT_PERSONALITIES.items():
            all_students[user_id] = info
        for user_id, info in new_student_info.items():
            all_students[user_id] = info

        # 3. 投稿を作成
        print("\n3. 探求学習の投稿を作成...")
        post_info = []
        total_posts = 0

        for user_id, info in all_students.items():
            theme = info["theme"]
            post_count = info.get("post_count", 6)
            is_active = info.get("active", True)

            # 投稿を生成
            posts = generate_posts_for_theme(theme, post_count)

            # 日付を計算
            # アクティブな生徒: 最終投稿が12/3〜12/17の間
            # 非アクティブな生徒: 最終投稿が11/1〜11/25の間（介入フラグ対象）
            if is_active:
                last_post_date = DEMO_DATE - timedelta(days=random.randint(0, 13))  # 12/4〜12/17
            else:
                last_post_date = DEMO_DATE - timedelta(days=random.randint(22, 46))  # 11/1〜11/25（14日以上経過）

            # 投稿日を逆算（古い投稿から新しい投稿へ）
            post_dates = []
            for i in range(len(posts)):
                # 最新から過去に向かって日付を計算
                days_ago = (len(posts) - 1 - i) * random.randint(3, 10)
                post_date = last_post_date - timedelta(days=days_ago)
                post_dates.append(post_date)

            for i, post in enumerate(posts):
                # 問いの変更回数を設定（後半の投稿ほど変化の可能性が高い）
                if i == 0:
                    change_type = "none"
                elif random.random() < 0.4 + (i / len(posts)) * 0.3:
                    change_type = random.choice(["deepened", "changed"])
                else:
                    change_type = "none"

                await db.execute(text("""
                    INSERT INTO posts (user_id, problem, content_1, content_2, content_3, phase_label, question_state_change_type, created_at, updated_at)
                    VALUES (:user_id, :problem, :c1, :c2, :c3, :phase, :change_type, :created_at, :created_at)
                """), {
                    "user_id": user_id, "problem": post["problem"],
                    "c1": post["content_1"], "c2": post["content_2"], "c3": post["content_3"],
                    "phase": post["phase"], "change_type": change_type,
                    "created_at": post_dates[i]
                })
                result = await db.execute(text("SELECT LAST_INSERT_ID()"))
                post_id = result.scalar()
                post_info.append((post_id, user_id))
                total_posts += 1

        await db.commit()
        print(f"   {total_posts}件の投稿を作成完了")

        # 4. 投稿に非認知能力ポイントを付与
        print("\n4. 投稿に非認知能力ポイントを付与...")
        all_abilities = [1, 2, 3, 4, 5, 6, 7]

        for post_id, user_id in post_info:
            strong_abilities = all_students[user_id]["strong"]

            # 得意な能力は必ず含める
            selected = list(strong_abilities)
            # 追加で1-2個の能力を選ぶ
            others = [a for a in all_abilities if a not in strong_abilities]
            selected.extend(random.sample(others, random.randint(1, 2)))

            for ability_id in selected:
                if ability_id in strong_abilities:
                    # 得意な能力: 高評価（3.5〜5.0）
                    point = Decimal(str(random.choice([3.5, 4.0, 4.5, 5.0])))
                    quality = random.randint(4, 5)
                else:
                    # その他: 普通（1.0〜3.0）
                    point = Decimal(str(random.choice([1.0, 1.5, 2.0, 2.5, 3.0])))
                    quality = random.randint(1, 3)

                await db.execute(text("""
                    INSERT INTO post_ability_points (post_id, ability_id, action_index, quality_level, point, created_at)
                    VALUES (:post_id, :ability_id, :action_idx, :quality, :point, NOW())
                """), {"post_id": post_id, "ability_id": ability_id, "action_idx": random.randint(1, 3), "quality": quality, "point": float(point)})

        await db.commit()
        print("   完了")

        # 5. 感謝の手紙を作成
        print("\n5. 感謝の手紙を作成...")
        letter_count = 0
        all_user_ids = list(all_students.keys())

        for sender_id in all_user_ids:
            others = [u for u in all_user_ids if u != sender_id]
            # 送る手紙の数は2〜5通でばらつき
            num_letters = random.randint(2, 5)
            receivers = random.sample(others, min(num_letters, len(others)))

            for receiver_id in receivers:
                template = random.choice(THANKS_TEMPLATES)
                # 手紙の日付も最近のものを多めに
                letter_date = DEMO_DATE - timedelta(days=random.randint(5, 60))

                await db.execute(text("""
                    INSERT INTO thanks_letters (sender_user_id, receiver_user_id, content_1, content_2, created_at)
                    VALUES (:sender, :receiver, :c1, :c2, :created_at)
                """), {"sender": sender_id, "receiver": receiver_id,
                       "c1": template["content_1"], "c2": template["content_2"], "created_at": letter_date})

                result = await db.execute(text("SELECT LAST_INSERT_ID()"))
                letter_id = result.scalar()

                # 手紙の能力ポイント: 1.5pt
                receiver_strong = all_students[receiver_id]["strong"]
                selected_abilities = list(receiver_strong)[:2]
                if len(selected_abilities) < 2:
                    others = [a for a in all_abilities if a not in selected_abilities]
                    selected_abilities.append(random.choice(others))

                for ability_id in selected_abilities:
                    # 全て1.5ptに統一
                    await db.execute(text("""
                        INSERT INTO thanks_letter_ability_points (thanks_letter_id, ability_id, points)
                        VALUES (:letter_id, :ability_id, :points)
                    """), {"letter_id": letter_id, "ability_id": ability_id, "points": 1.5})

                letter_count += 1

        await db.commit()
        print(f"   {letter_count}件の感謝の手紙を作成完了")

        # 6. サマリー表示
        print("\n=== 完了 ===")
        print(f"\n【作成データサマリー】")
        print(f"  投稿数: {total_posts}件")
        print(f"  感謝の手紙: {letter_count}件")

        print(f"\n【介入フラグ対象の生徒】（最終投稿から14日以上経過）")
        for user_id, info in all_students.items():
            if not info.get("active", True):
                print(f"  {info['name']} - テーマ: {info['theme']}")

        print(f"\n【新規生徒アカウント一覧】（パスワード: test1234）")
        for student in NEW_STUDENTS:
            abilities_str = ", ".join([ABILITY_NAMES[a] for a in student["strong"]])
            active_str = "✓" if student["active"] else "×介入対象"
            print(f"  {student['name']} | {student['grade']}年{student['class']}組 | {student['login']} | 得意: {abilities_str} | {active_str}")


asyncio.run(main())
