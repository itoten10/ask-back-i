"""OpenAI APIを使った非認知能力判定サービス（強化版）

ルーブリック活用、Few-shot判定例、5段階レベル評価を含む
詳細なロジックは docs/ability_analysis_logic.md を参照
"""
import json
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings


# 5段階レベルの説明（UI表示用）
LEVEL_DESCRIPTIONS = {
    1: "初歩的",
    2: "発展途上",
    3: "標準的",
    4: "発展的",
    5: "卓越"
}


# 7つの非認知能力の定義（ルーブリック付き）
ABILITIES_WITH_RUBRICS = [
    {
        "code": "problem_setting",
        "name": "課題設定力",
        "description": "適切な課題を設定し、明確な問いを立てる力。探究に耐える'良い問い'をつくり、検証可能な形に整えられる。",
        "rubric_levels": {
            1: "テーマが「好き・面白そう」で止まり、問いになっていない",
            2: "問いはあるが広すぎる／曖昧で、調べても答えが定まらない",
            3: "「何を」「なぜ」「どう確かめるか」が揃った問いを置ける",
            4: "サブクエスチョンや仮説を立て、検証の方法を設計できる",
            5: "調査の途中で問いを磨き直し、より本質的な問いへ再設計できる"
        },
        "detection_keywords": ["問い", "課題", "テーマ", "仮説", "検証", "疑問", "なぜ"]
    },
    {
        "code": "information_gathering",
        "name": "情報収集力",
        "description": "必要な情報を効率的に収集し、整理する力。問いに答えるために、必要な情報を集め・確かめ・整理できる。",
        "rubric_levels": {
            1: "何を調べるべきかが曖昧で、調べずに思い込みで進める",
            2: "検索で情報を集めるが、単発で終わりやすい",
            3: "問いに必要なキーワードを考えて調べ、メモに残せる",
            4: "情報の信頼性を確認しながら収集できる",
            5: "一次情報を設計し、情報の質を自分で高められる"
        },
        "detection_keywords": ["調べ", "検索", "収集", "資料", "データ", "情報", "文献", "記事", "インターネット"]
    },
    {
        "code": "involvement",
        "name": "巻き込む力",
        "description": "他者を巻き込み、協力を得る力。探究を深めるために、適切な人・資源・協力を得られる。",
        "rubric_levels": {
            1: "困っても相談せず、抱え込んで停滞する",
            2: "近い友人や先生には相談できるが、目的や依頼が曖昧",
            3: "探究を進めるために、必要な相手に相談・依頼ができる",
            4: "インタビュー先・協力者を自分で開拓し、関係を継続できる",
            5: "人と人をつなぎ、探究が広がる場をつくれる"
        },
        "detection_keywords": ["協力", "チーム", "メンバー", "一緒に", "分担", "役割", "依頼", "お願い", "連携"]
    },
    {
        "code": "communication",
        "name": "対話する力",
        "description": "他者と建設的な対話を行い、理解を深める力。聞き取り・議論・発表を通じて、相手の本音や示唆を引き出し探究に活かす。",
        "rubric_levels": {
            1: "相手の話を十分に聞けず、必要な情報が取れない",
            2: "質問はできるが、深掘りや要約が弱い",
            3: "オープンクエスチョンで聞き、要点を要約して確認できる",
            4: "インタビュー設計をして、本質に近づく対話ができる",
            5: "対話を通じて相手の気づきも生み、協力関係を強められる"
        },
        "detection_keywords": ["インタビュー", "質問", "聞", "話", "対話", "議論", "発表", "伝え", "説明"]
    },
    {
        "code": "humility",
        "name": "謙虚である力",
        "description": "他者の意見を受け入れ、学び続ける姿勢。フィードバックを歓迎し、他者の知見を取り入れて探究の精度を上げる。",
        "rubric_levels": {
            1: "指摘を拒んだり、言い訳が先に出て改善が起きない",
            2: "指摘は聞くが、行動や成果物に反映されにくい",
            3: "指摘を受け止め、必要な修正を行える",
            4: "自分から批評を取りに行き、反証・弱点を歓迎して精度を上げられる",
            5: "学び合いの文化をつくり、周囲の探究姿勢まで良くしていける"
        },
        "detection_keywords": ["フィードバック", "指摘", "修正", "改善", "反省", "学び", "意見", "アドバイス", "見直し"]
    },
    {
        "code": "execution",
        "name": "実行する力",
        "description": "計画を実行に移し、行動する力。仮説検証を'まずやってみる'形で進め、改善しながら前に進める。",
        "rubric_levels": {
            1: "計画やアイデアで止まり、検証行動に移れない",
            2: "一度は動くが、記録や振り返りが弱く、学びが積み上がらない",
            3: "小さな検証を回し、結果を記録できる",
            4: "検証計画を立て、継続的に改善できる",
            5: "周囲も巻き込みながら検証サイクルを高速で回せる"
        },
        "detection_keywords": ["実行", "行動", "実施", "やってみ", "試", "実験", "訪問", "作成", "制作"]
    },
    {
        "code": "completion",
        "name": "完遂する力",
        "description": "最後までやり遂げる力、継続する力。期限までに成果物を仕上げ、学びを言語化して次へつなげる。",
        "rubric_levels": {
            1: "途中で止まり、成果物が完成しない",
            2: "最低限は形にするが、根拠・構成・検証が弱い",
            3: "期限までに成果物を完成できる",
            4: "根拠の提示が明確で、第三者が理解できる品質になっている",
            5: "発表や共有によって周囲に影響を与え、探究が継続・発展する"
        },
        "detection_keywords": ["完成", "まとめ", "発表", "提出", "仕上", "継続", "最後まで", "完了", "達成"]
    },
]

# Few-shot判定例（5段階レベル付き）
FEW_SHOT_EXAMPLES = [
    {
        "input": {
            "problem": "地域の高齢化問題について調べる",
            "content": "図書館で高齢化に関する本を3冊借りて読み、重要なポイントをノートにまとめた。"
        },
        "output": {
            "matched_abilities": [
                {
                    "code": "information_gathering",
                    "name": "情報収集力",
                    "level": 3,
                    "level_reason": "問いに必要なキーワードを考えて調べ、メモに残しているためLv3相当",
                    "reason": "図書館で本を借りて調べ、ノートにまとめるという情報収集と整理の行動が明確に見られる"
                }
            ],
            "analysis_summary": "文献調査による情報収集力の発揮が見られる活動です。Lv3「問いに必要なキーワードを考えて調べ、メモに残せる」に該当します。"
        }
    },
    {
        "input": {
            "problem": "環境問題についての探究",
            "content": "NPOの方にアポを取り、オンラインでインタビューを実施した。質問リストを事前に作成し、話を聞きながらメモを取った。インタビュー後、チームで内容を共有した。"
        },
        "output": {
            "matched_abilities": [
                {
                    "code": "involvement",
                    "name": "巻き込む力",
                    "level": 4,
                    "level_reason": "インタビュー先を自分で開拓しているためLv4相当",
                    "reason": "外部のNPOにアポを取り、協力を得てインタビューを実施した"
                },
                {
                    "code": "communication",
                    "name": "対話する力",
                    "level": 4,
                    "level_reason": "インタビュー設計をして対話しているためLv4相当",
                    "reason": "質問リストを準備し、インタビューで相手から情報を引き出した"
                },
                {
                    "code": "execution",
                    "name": "実行する力",
                    "level": 3,
                    "level_reason": "小さな検証を回し、結果を記録しているためLv3相当",
                    "reason": "計画を立てて実際にインタビューを実行した"
                }
            ],
            "analysis_summary": "外部協力者との対話を通じた探究活動で、巻き込む力(Lv4)・対話する力(Lv4)・実行する力(Lv3)が発揮されています。"
        }
    },
    {
        "input": {
            "problem": "プログラミング学習",
            "content": "今日は疲れていたので何もしなかった。"
        },
        "output": {
            "matched_abilities": [],
            "analysis_summary": "具体的な探究活動が記載されていないため、該当する能力を判定できません。"
        }
    }
]


class AbilityAnalyzerService:
    """非認知能力を分析するサービス（強化版）"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def _build_rubric_text(self) -> str:
        """ルーブリック情報をテキスト化"""
        rubric_text = ""
        for ability in ABILITIES_WITH_RUBRICS:
            rubric_text += f"\n### {ability['name']}（{ability['code']}）\n"
            rubric_text += f"定義: {ability['description']}\n"
            rubric_text += "レベル別基準:\n"
            for level, desc in ability['rubric_levels'].items():
                rubric_text += f"  Lv{level}: {desc}\n"
        return rubric_text

    def _build_few_shot_text(self) -> str:
        """Few-shot例をテキスト化"""
        examples_text = ""
        for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
            examples_text += f"\n【例{i}】\n"
            examples_text += f"入力:\n"
            if example['input'].get('problem'):
                examples_text += f"  課題: {example['input']['problem']}\n"
            examples_text += f"  やってみたこと: {example['input']['content']}\n"
            examples_text += f"出力:\n"
            examples_text += f"  {json.dumps(example['output'], ensure_ascii=False, indent=2)}\n"
        return examples_text

    async def analyze_abilities(
        self,
        content: str,
        problem: Optional[str] = None
    ) -> dict:
        """
        投稿内容から該当する非認知能力を判定する（5段階レベル評価版）

        Args:
            content: 投稿内容（やってみたこと）
            problem: 課題・問い（任意）

        Returns:
            {
                "matched_abilities": [
                    {
                        "code": str,
                        "name": str,
                        "level": int (1-5),
                        "level_reason": str,
                        "reason": str
                    },
                    ...
                ],
                "analysis_summary": str
            }
        """
        # ルーブリックとFew-shot例を構築
        rubric_text = self._build_rubric_text()
        few_shot_text = self._build_few_shot_text()

        # ユーザー入力を構築
        input_text = f"【課題・問い】\n{problem}\n\n" if problem else ""
        input_text += f"【やってみたこと】\n{content}"

        system_prompt = f"""あなたは教育専門家です。
生徒の探究活動の記録を読み、その活動で発揮された「非認知能力」を判定し、5段階のルーブリックでレベル評価してください。

## 7つの非認知能力とルーブリック（5段階）
{rubric_text}

## 判定基準
1. その活動内容に明確に関連する能力のみを選んでください
2. 曖昧な場合や具体的な活動が記載されていない場合は選ばないでください
3. 該当する能力ごとに、ルーブリックを参照して5段階のレベル（1〜5）を判定してください
   - Lv1: 初歩的 - その能力の発揮が弱い、または不十分
   - Lv2: 発展途上 - 基本的な行動は見られるが、深さや継続性が不足
   - Lv3: 標準的 - その能力が適切に発揮されている
   - Lv4: 発展的 - 自発的・計画的に能力を発揮している
   - Lv5: 卓越 - 周囲への波及効果や継続的な成長が見られる
4. レベル判定の理由（level_reason）は、ルーブリックのどの基準に該当するか明記してください
5. 該当理由（reason）は、具体的な活動内容を引用して説明してください

## 判定例
{few_shot_text}

## 出力形式
必ず以下のJSON形式で出力してください：
{{
  "matched_abilities": [
    {{
      "code": "ability_code",
      "name": "能力名",
      "level": 3,
      "level_reason": "ルーブリックLv3「〜」に該当するため",
      "reason": "該当理由（具体的な活動内容を引用して1-2文で）"
    }}
  ],
  "analysis_summary": "全体の分析サマリー（能力名とレベルを含む2-3文）"
}}

該当する能力がない場合は matched_abilities を空配列にしてください。
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.2,  # より一貫性を重視
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # 結果の検証と正規化
            if "matched_abilities" not in result:
                result["matched_abilities"] = []
            if "analysis_summary" not in result:
                result["analysis_summary"] = ""

            # 有効な能力コードのみをフィルタリング & レベルが1-5の範囲のみ
            valid_codes = {a["code"] for a in ABILITIES_WITH_RUBRICS}
            validated_abilities = []
            for ability in result["matched_abilities"]:
                if ability.get("code") not in valid_codes:
                    continue
                # レベルを1-5の範囲に正規化
                level = ability.get("level", 3)
                if not isinstance(level, int) or level < 1:
                    level = 1
                elif level > 5:
                    level = 5
                ability["level"] = level
                # level_reasonがない場合はデフォルト値
                if "level_reason" not in ability:
                    ability["level_reason"] = f"Lv{level}相当と判定"
                validated_abilities.append(ability)

            result["matched_abilities"] = validated_abilities

            # レベルでソート（高い順）
            result["matched_abilities"].sort(
                key=lambda x: x.get("level", 0),
                reverse=True
            )

            return result

        except json.JSONDecodeError:
            return {
                "matched_abilities": [],
                "analysis_summary": "分析結果のパースに失敗しました",
                "error": "JSON parse error"
            }
        except Exception as e:
            return {
                "matched_abilities": [],
                "analysis_summary": f"分析中にエラーが発生しました: {str(e)}",
                "error": str(e)
            }


# シングルトンインスタンス
ability_analyzer_service = AbilityAnalyzerService()

# 外部参照用
ABILITIES = [
    {"code": a["code"], "name": a["name"], "description": a["description"]}
    for a in ABILITIES_WITH_RUBRICS
]
