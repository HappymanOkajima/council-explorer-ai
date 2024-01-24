# 一般質問がある場合はこちらを実行
# 前のバージョンは特定用途（R5_1_2専用）のため、今後は一般化したこちらを使う
import csv

def process_summary(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile, quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)
        rows = [row for row in reader]

    agenda_numbers_index = rows[0].index('agenda_numbers')
    
    skipped_rows = []
    agenda_number = 1
    for i in range(1, len(rows)):
        if "質問終了" in rows[i][5] or "質問が終了" in rows[i][5]:
            for j in skipped_rows:
                rows[j][agenda_numbers_index] = f'"一般質問その{agenda_number}"'
            print(f'一般質問その{agenda_number}')

            skipped_rows = []
            agenda_number += 1
        else:
            skipped_rows.append(i)

    # Remaining skipped rows after the last break
    for j in skipped_rows:
        rows[j][agenda_numbers_index] = f'"一般質問その{agenda_number}"'

    print(f'一般質問その{agenda_number}')

    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)
        writer.writerows(rows)
        
        
process_summary('summary.csv', 'edited_summary.csv')