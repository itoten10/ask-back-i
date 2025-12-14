"""ルーブリックデータをデータベースに登録するスクリプト"""
import asyncio
from datetime import datetime
import asyncmy
from app.core.config import settings


async def insert_rubrics():
    """7つの能力×5レベルのルーブリックを登録"""
    ssl_config = {"ssl_ca": settings.ssl_ca_path} if settings.ssl_ca_path else None
    conn = await asyncmy.connect(
        host=settings.db_host,
        port=int(settings.db_port),
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        ssl=ssl_config,
    )

    try:
        cursor = conn.cursor()

        # 能力IDを取得
        await cursor.execute("SELECT id, code FROM non_cog_abilities ORDER BY id")
        abilities = await cursor.fetchall()
        ability_map = {row[1]: row[0] for row in abilities}
        print(f"能力マスター: {ability_map}")

        # ルーブリックデータ
        rubrics = {
            "problem_setting": {
                "name": "課題設定力",
                "subtitle": "探究に耐える'良い問い'をつくり、検証可能な形に整えられる",
                "levels": [
                    {
                        "level": 1,
                        "title": "未達",
                        "description": "テーマが「好き・面白そう」で止まり、問いになっていない。何を明らかにしたいかが説明できず、活動が散らかる。"
                    },
                    {
                        "level": 2,
                        "title": "初歩",
                        "description": "問いはあるが広すぎる／曖昧で、調べても答えが定まらない。目的（誰の何の役に立つか）が弱く、方向転換が多い。"
                    },
                    {
                        "level": 3,
                        "title": "基準到達",
                        "description": "「何を」「なぜ」「どう確かめるか」が揃った問いを置ける。調べる範囲や対象を絞り、探究の筋道を立てられる。"
                    },
                    {
                        "level": 4,
                        "title": "優良",
                        "description": "サブクエスチョンや仮説を立て、検証の方法（データ／観察／比較）を設計できる。探究の価値（新規性・意義・広がり）を言語化できる。"
                    },
                    {
                        "level": 5,
                        "title": "卓越",
                        "description": "調査の途中で問いを磨き直し、より本質的で意味のある問いへ再設計できる。周囲の問いづくりにも影響を与え、問いの質を引き上げる関わりができる。"
                    },
                ]
            },
            "information_gathering": {
                "name": "情報収集力",
                "subtitle": "問いに答えるために、必要な情報を集め・確かめ・整理できる",
                "levels": [
                    {
                        "level": 1,
                        "title": "未達",
                        "description": "何を調べるべきかが曖昧で、調べずに思い込みで進めることが多い。情報源（誰が言った／どこに書いてある）を残さない。根拠と意見の区別がつかず、主張がふわっとしている。"
                    },
                    {
                        "level": 2,
                        "title": "初歩",
                        "description": "検索で情報を集めるが、単発で終わりやすい（メモや引用が不十分）。似た情報ばかり集め、比較・検証が少ない。「使えそう」で選ぶが、信頼性の確認はあまりしない。"
                    },
                    {
                        "level": 3,
                        "title": "基準到達",
                        "description": "問いに必要なキーワードを考えて調べ、メモに残せる。複数の情報源（本・記事・統計・インタビュー等）を使い分けられる。出典を記録し、根拠に基づいて説明できる。"
                    },
                    {
                        "level": 4,
                        "title": "優良",
                        "description": "情報の信頼性（発信者・一次/二次・データの条件）を確認しながら収集できる。異なる立場の情報を並べ、共通点・相違点から仮説を更新できる。調べた内容を整理して「次に何を調べるべきか」まで繋げられる。"
                    },
                    {
                        "level": 5,
                        "title": "卓越",
                        "description": "一次情報（観察・実験・アンケート・聞き取り等）を設計し、情報の質を自分で高められる。情報の整理が体系化され、他者が追跡できる形（引用・ログ・図解）で共有できる。周囲の探究にも良い影響を与え、情報収集のやり方を支援できる。"
                    },
                ]
            },
            "involvement": {
                "name": "巻き込む力",
                "subtitle": "探究を深めるために、適切な人・資源・協力を得られる",
                "levels": [
                    {
                        "level": 1,
                        "title": "未達",
                        "description": "困っても相談せず、抱え込んで停滞する。協力が必要な場面でも、声をかけられない。"
                    },
                    {
                        "level": 2,
                        "title": "初歩",
                        "description": "近い友人や先生には相談できるが、目的や依頼が曖昧。協力を得ても、役割や進め方が定まらず続かない。"
                    },
                    {
                        "level": 3,
                        "title": "基準到達",
                        "description": "探究を進めるために、必要な相手に相談・依頼ができる。チームなら役割分担を行い、情報共有を回せる。"
                    },
                    {
                        "level": 4,
                        "title": "優良",
                        "description": "インタビュー先・協力者・現場などを自分で開拓し、関係を継続できる。相手にとってのメリットも考え、協働が成立する提案ができる。"
                    },
                    {
                        "level": 5,
                        "title": "卓越",
                        "description": "人と人をつなぎ、探究が広がる場（共同調査・発表会・連携）をつくれる。周囲が自発的に協力したくなる状態を生み出せる。"
                    },
                ]
            },
            "communication": {
                "name": "対話する力",
                "subtitle": "聞き取り・議論・発表を通じて、相手の本音や示唆を引き出し探究に活かす",
                "levels": [
                    {
                        "level": 1,
                        "title": "未達",
                        "description": "相手の話を十分に聞けず、必要な情報が取れない。質問が誘導的／浅く、探究に繋がる材料が得られない。"
                    },
                    {
                        "level": 2,
                        "title": "初歩",
                        "description": "質問はできるが、深掘りや要約が弱い。メモが不十分で、あとで活用しにくい。"
                    },
                    {
                        "level": 3,
                        "title": "基準到達",
                        "description": "オープンクエスチョンで聞き、要点を要約して確認できる。相手の立場や背景を尊重し、安心して話せる雰囲気をつくれる。"
                    },
                    {
                        "level": 4,
                        "title": "優良",
                        "description": "インタビュー設計（目的・質問順・仮説）をして、本質に近づく対話ができる。得た示唆を探究の仮説・検証に反映できる。"
                    },
                    {
                        "level": 5,
                        "title": "卓越",
                        "description": "対話を通じて相手の気づきも生み、協力関係を強めながら探究を前進させられる。議論のファシリテーションでチームの思考を深められる。"
                    },
                ]
            },
            "humility": {
                "name": "謙虚である力",
                "subtitle": "フィードバックを歓迎し、他者の知見を取り入れて探究の精度を上げる",
                "levels": [
                    {
                        "level": 1,
                        "title": "未達",
                        "description": "指摘を拒んだり、言い訳が先に出て改善が起きない。根拠が弱くても自説に固執しがち。"
                    },
                    {
                        "level": 2,
                        "title": "初歩",
                        "description": "指摘は聞くが、行動や成果物に反映されにくい。間違いを認めるのが苦手で、学びに変換しづらい。"
                    },
                    {
                        "level": 3,
                        "title": "基準到達",
                        "description": "指摘を受け止め、必要な修正を行える。自分の限界を認め、助けを借りながら進められる。"
                    },
                    {
                        "level": 4,
                        "title": "優良",
                        "description": "自分から批評を取りに行き、反証・弱点を歓迎して精度を上げられる。意見が割れたときに、相手を尊重しつつ合意形成できる。"
                    },
                    {
                        "level": 5,
                        "title": "卓越",
                        "description": "学び合いの文化をつくり、周囲の探究姿勢まで良くしていける。自分の成果も仮説として扱い、常に更新できる。"
                    },
                ]
            },
            "execution": {
                "name": "実行する力",
                "subtitle": "仮説検証を'まずやってみる'形で進め、改善しながら前に進める",
                "levels": [
                    {
                        "level": 1,
                        "title": "未達",
                        "description": "計画やアイデアで止まり、検証行動（調査・実験・試作）に移れない。うまくいかないと止まってしまう。"
                    },
                    {
                        "level": 2,
                        "title": "初歩",
                        "description": "一度は動くが、記録や振り返りが弱く、学びが積み上がらない。目標が大きすぎて、手が止まりやすい。"
                    },
                    {
                        "level": 3,
                        "title": "基準到達",
                        "description": "小さな検証（試作・観察・簡易アンケート等）を回し、結果を記録できる。失敗を改善点として捉え、次の一手を出せる。"
                    },
                    {
                        "level": 4,
                        "title": "優良",
                        "description": "検証計画（期間・指標・必要データ）を立て、継続的に改善できる。状況に合わせて手段を切り替え、成果に近づけられる。"
                    },
                    {
                        "level": 5,
                        "title": "卓越",
                        "description": "周囲も巻き込みながら検証サイクルを高速で回し、探究の質を引き上げられる。実行のプロセス自体を他者が再現できる形で共有できる。"
                    },
                ]
            },
            "completion": {
                "name": "完遂する力",
                "subtitle": "期限までに成果物を仕上げ、学びを言語化して次へつなげる",
                "levels": [
                    {
                        "level": 1,
                        "title": "未達",
                        "description": "途中で止まり、成果物が完成しない／提出できない。何ができたかが言語化できない。"
                    },
                    {
                        "level": 2,
                        "title": "初歩",
                        "description": "最低限は形にするが、根拠・構成・検証が弱い。振り返りが浅く、次に活きない。"
                    },
                    {
                        "level": 3,
                        "title": "基準到達",
                        "description": "期限までに成果物（発表・レポート等）を完成できる。目的→方法→結果→考察の流れで説明でき、学びを整理できる。"
                    },
                    {
                        "level": 4,
                        "title": "優良",
                        "description": "根拠の提示（引用・データ・手順）が明確で、第三者が理解できる品質になっている。限界や課題も含めて振り返り、次の改善案を示せる。"
                    },
                    {
                        "level": 5,
                        "title": "卓越",
                        "description": "発表や共有によって周囲に影響を与え、探究が継続・発展する形をつくれる。成果を資産化（ポートフォリオ化）し、次の探究や他者の探究に再利用できる。"
                    },
                ]
            },
        }

        now = datetime.utcnow()
        inserted_count = 0

        for code, data in rubrics.items():
            ability_id = ability_map.get(code)
            if not ability_id:
                print(f"⚠️ 能力 {code} が見つかりません。スキップします。")
                continue

            for level_data in data["levels"]:
                # 既に存在するかチェック
                await cursor.execute(
                    "SELECT id FROM ability_rubrics WHERE ability_id = %s AND level = %s",
                    (ability_id, level_data["level"])
                )
                existing = await cursor.fetchone()

                if existing:
                    # 更新
                    await cursor.execute(
                        """
                        UPDATE ability_rubrics
                        SET title = %s, description = %s, updated_at = %s
                        WHERE ability_id = %s AND level = %s
                        """,
                        (level_data["title"], level_data["description"], now, ability_id, level_data["level"])
                    )
                    print(f"  ✓ {data['name']} レベル{level_data['level']} を更新")
                else:
                    # 挿入
                    coefficient = level_data["level"] * 0.2  # レベル1=0.2, レベル5=1.0
                    await cursor.execute(
                        """
                        INSERT INTO ability_rubrics (ability_id, level, title, description, coefficient, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (ability_id, level_data["level"], level_data["title"], level_data["description"], coefficient, now, now)
                    )
                    inserted_count += 1
                    print(f"  ✅ {data['name']} レベル{level_data['level']} を登録")

        await conn.commit()
        print(f"\n✅ ルーブリックの登録が完了しました！（{inserted_count} 件追加）")

        # 確認
        await cursor.execute("SELECT COUNT(*) FROM ability_rubrics")
        total = (await cursor.fetchone())[0]
        print(f"   合計: {total} 件のルーブリックが登録されています")

    except Exception as e:
        print(f"❌ エラー: {e}")
        await conn.rollback()
        raise
    finally:
        await cursor.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(insert_rubrics())
