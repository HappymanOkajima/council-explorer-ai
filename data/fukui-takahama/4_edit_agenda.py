import csv
import re

def extract_agenda_range(text):
    # 議案第X号から何かの情報を経て議案第Y号までの形式で議案の範囲を取得
    pattern = r"議案第(\d+)号から.*?議案第(\d+)号まで"
    matches = re.findall(pattern, text)
    agendas = []
    for start, end in matches:
        start, end = int(start), int(end)
        agendas.extend(range(start, end + 1))
    return agendas

with open('summary.csv', 'r', encoding='utf-8') as infile, open('edited_summary.csv', 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile, quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    writer = csv.writer(outfile, quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)

    # タイトル行を読み取り、そのまま書き出す
    headers = next(reader)
    writer.writerow(headers)

    for row in reader:
        agenda_numbers_str = row[4]
        summary = row[5]
        speaker_role = row[2]

        # summaryから議案の範囲を取得
        agenda_range = extract_agenda_range(summary)

        if agenda_range:
            agenda_numbers = agenda_range
        else:
            # 文字列からリストに変換
            agenda_numbers = [int(num.strip()) for num in agenda_numbers_str.split(",") if num.strip()]

        # 昇順にソート
        agenda_numbers.sort()

        # 各議案番号をダブルクォートで囲み、カンマ区切りの文字列として格納
        agenda_numbers_quoted = ', '.join(['\"{}\"'.format(num) for num in agenda_numbers])
        
        row[4] = agenda_numbers_quoted

        # speaker_roleが「議会議員」で終わる場合、agenda_numbersを空文字にする
        if speaker_role.endswith("議会議員"):
            row[4] = ""

        writer.writerow(row)

print("CSVの編集が完了しました。")
