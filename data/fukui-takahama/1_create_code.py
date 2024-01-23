import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 指定されたURLからページの内容を取得
# R5_1_1
#url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050307A/0/0//10/1/3:0/49/1//0/0/0"
# R5_1_2
#url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050309A/-1/0//10/1/3:0/50/1//0/0/0"
# R5_1_3
#url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050324A/-1/0//10/1/3:0/51/1//0/0/0"
# R5_2_1
url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050331A/0/0//10/1/2:0/280/1//0/0/0"
# R5_3_1
#url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050509A/0/0//10/1/2:0/281/1//0/0/0"
# R5_4_1
#url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050606A/0/0//10/1/2:0/282/1//0/0/0"
# R5_4_2
#url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050608A/0/0//10/1/2:0/283/1//0/0/0"
# R5_4_3
#url = "https://www.kensakusystem.jp/takahama/cgi-bin3/r_Speakers.exe?bnp0cuv0jx8u44iels/R050620A/0/0//10/1/2:0/284/1//0/0/0"

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# アンカータグのリンクを取得し、絶対パスに変換
links = [urljoin(url, a['href'].replace('r_TextFrame.exe', 'GetText3.exe')) for a in soup.find_all('a', href=True)]

# リンクから必要な部分を抽出し、code.txtに保存
with open('code.txt', 'w') as f:
    for link in links:
        path_parts = link.split('/')
        if len(path_parts) >= 7:  # Ensure there are enough parts in the path
            code_part = f"{path_parts[-11]}/{path_parts[-10]}"
            f.write(f"{code_part},{link}\n")

print("code.txtにリンクのコード部分と元のURLが保存されました。")
