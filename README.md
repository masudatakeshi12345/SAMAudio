# SAMAudio

SAMAudio は、会議音声から「誰が何を話したか」を記録するための Python 実装です。今回の構成では、次の流れを一通り扱えます。

- 任意の人物の音声サンプルを登録する
- 会議音声を話者ごとに分離する
- 分離された発話を登録済みの人物に照合する
- 各発話を文字起こしする
- 話者名付きのレポートを JSON / Markdown で出力する

## できること

ワークフローは次の通りです。

1. 話者ごとに参照音声を 1 つ以上登録する
2. 会議録音に対して話者分離をかける
3. 各発話区間の話者埋め込みを抽出する
4. 登録済みの声紋と類似度比較して人物を推定する
5. 各区間を文字起こしし、発話ログとして保存する

## 注意点

- 他人の声を録音、分析、記録する前に、必ず本人の同意を取ってください。
- 精度は、マイク品質、学習用音声の長さ、雑音、話者同士の声質の近さ、同時発話の有無に大きく左右されます。
- `pyannote.audio` の利用には Hugging Face トークンが必要です。`HF_TOKEN` に設定してください。
- 初回実行時は diarization / speaker embedding / transcription 用モデルがダウンロードされるため、時間がかかります。

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Hugging Face トークンを設定します。

```bash
set HF_TOKEN=your_token_here
```

## 使い方

### 1. 話者を登録する

同じ人物のクリアな音声を 1 つ以上指定します。

```bash
samaudio enroll --speaker-id sato --name "佐藤" data\sato_1.wav data\sato_2.wav
```

登録情報は `.samaudio\enrollments` に保存されます。

### 2. 登録済み話者を確認する

```bash
samaudio list-speakers
```

### 3. 会議音声を処理する

```bash
samaudio meeting data\meeting.wav --language ja
```

出力先は `.samaudio\exports\<timestamp>` です。

- `meeting_report.json`: 機械処理向けの構造化データ
- `meeting_report.md`: 人が読みやすいサマリ
- `clips\`: 話者照合と文字起こしに使った区間音声

## 出力例

```json
{
  "meeting_audio": "C:\\CodeX\\SAMAudio\\data\\meeting.wav",
  "generated_at": "2026-03-16T12:34:56.789012",
  "segments": [
    {
      "speaker_label": "佐藤",
      "start": 3.21,
      "end": 7.96,
      "text": "それでは会議を始めます。",
      "confidence": 0.88,
      "matched_profile": "sato",
      "similarity": 0.88,
      "start_ts": "00:00:03.210",
      "end_ts": "00:00:07.960"
    }
  ]
}
```

## 今後の改善候補

- 同時発話に強い後処理を追加する
- 人ごとに最適なしきい値を校正できるようにする
- 1人につき複数の声紋を保持してクラスタリング精度を上げる
- Web UI を追加して登録とレポート確認を簡単にする
- VAD ベースで細切れ区間をまとめ、文字起こし品質を改善する
