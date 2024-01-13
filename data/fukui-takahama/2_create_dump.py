import requests
from bs4 import BeautifulSoup
import os
import re
from dotenv import load_dotenv

def extract_agenda_numbers(text):
    pattern = r'議案第(\d+)号'
    matches = re.findall(pattern, text)
    return list(map(int, set(matches)))

def split_speaker_info(speaker):
    match = re.match(r'^(.*)\（(.*?)\）$', speaker)
    if match:
        role, name = match.groups()
        return role, name  # ここで「君」はそのまま残しています
    elif speaker == "議長":
        return speaker, ""
    else:
        return "", speaker

load_dotenv()
post_url = "https://www.kensakusystem.jp/takahama/cgi-bin3/GetText3.exe"
statement_number = 0

with open('code.txt', 'r') as f, open('dump.csv', 'a',encoding="utf-8") as outfile:

    header = '"meeting_name","statement_number","speaker_role","speaker_name","agenda_numbers","content","source"\n'
    print(header)
    outfile.write(header)
    outfile.flush()

    for line in f:
        statement_number += 1
        code_part, original_link = line.strip().split(',')
        fileName, startPos = code_part.split('/')
        data = {
            "Code": "bnp0cuv0jx8u44iels",
            "fileName": fileName,
            "startPos": startPos,
            "keyMode": "10",
            "searchMode": "1",
            "FUNC": ""
        }

        response = requests.post(post_url, data=data)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = '\n'.join([line.strip() for line in soup.get_text().splitlines() if line.strip()])
        first_line = content.split('\n')[0].strip()
        meeting_name, speaker = first_line.rsplit(' ', 1)
        agenda_numbers = extract_agenda_numbers(content)
        speaker_role, speaker_name = split_speaker_info(speaker)

        output_line = f"\"{meeting_name}\", \"{statement_number}\", \"{speaker_role}\", \"{speaker_name}\", \"{','.join(map(str, agenda_numbers))}\", \"{content}\",\"{original_link}\"\n"
        print(output_line)
        outfile.write(output_line)
        outfile.flush()

print("議事録内容がdump.csvに保存されました。")
