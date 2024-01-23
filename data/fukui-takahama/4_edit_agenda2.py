# R5_1_2 限定
# 他の一般質問の場合は、determine_statement を適宜修正すること
import csv

def determine_statement(number):
    if 1 <= number <= 55:
        return '"一般質問その1"'
    elif 56 <= number <= 138:
        return '"一般質問その2"'
    elif 139 <= number <= 167:
        return '"一般質問その3"'
    elif 168 <= number <= 181:
        return '"一般質問その4"'
    elif 182 <= number <= 215:
        return '"一般質問その5"'
    elif 216 <= number <= 231:
        return '"一般質問その6"'
    elif 232 <= number <= 269:
        return '"一般質問その7"'
    else:
        return ""

with open('summary.csv', 'r', encoding='utf-8') as infile, open('edited_summary.csv', 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile, quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    writer = csv.writer(outfile, quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)

    # タイトル行を読み取り、そのまま書き出す
    headers = next(reader)
    writer.writerow(headers)

    for row in reader:
        try:
            statement_number = int(row[1])
            row[4] = determine_statement(statement_number)
        except ValueError:
            # row[4]が数値に変換できない場合、値をそのままにしておく
            pass
        
        writer.writerow(row)

print("CSVの編集が完了しました。")
