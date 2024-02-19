#--web true
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
import re
import requests
import socket

ROLE = """
When requested to write code, pick Python.
When requested to show chess position, always use the FEN notation.
When showing HTML, always include what is in the body tag, 
but exclude the code surrounding the actual content. 
So exclude always BODY, HEAD and HTML .
"""

MODEL = "gpt-35-turbo"
AI = None

def req(msg):
    return [{"role": "system", "content": ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=MODEL, messages=req(input))
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"


"""
import re
from pathlib import Path
text = Path("util/test/chess.txt").read_text()
text = Path("util/test/html.txt").read_text()
text = Path("util/test/code.txt").read_text()
"""
def extract(text):
    res = {}

    # search for a chess position
    pattern = r'(([rnbqkpRNBQKP1-8]{1,8}/){7}[rnbqkpRNBQKP1-8]{1,8} [bw] (-|K?Q?k?q?) (-|[a-h][36]) \d+ \d+)'
    m = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    #print(m)
    if len(m) > 0:
        res['chess'] = m[0][0]
        return res

    # search for code
    pattern = r"```(\w+)\n(.*?)```"
    m = re.findall(pattern, text, re.DOTALL)
    if len(m) > 0:
        if m[0][0] == "html":
            html = m[0][1]
            # extract the body if any
            pattern = r"<body.*?>(.*?)</body>"
            m = re.findall(pattern, html, re.DOTALL)
            if m:
                html = m[0]
            res['html'] = html
            return res
        res['language'] = m[0][0]
        res['code'] = m[0][1]
        return res
    return res

def main(args):
    global AI
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")
    if input == "":
        res = {
            "output": "Welcome to the OpenAI demo chat",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
    else:
        print("----------------- new code - STEP 1 - email address in input check ----------------")
        lst = re.findall('\S+@\S+', input)  

        if len(lst) > 0:
            if len(lst) > 1:
                print("more than 1 email address in the request, picking the first one")
            r = requests.get('https://nuvolaris.dev/api/v1/web/utils/demo/slack/?text=ciao, '+lst[0]+' come va?', auth=('user', 'pass'))
            print(lst[0])
            if (r.status_code != 200):
                print("request failed: status code:" + str(r.status_code) )
        else:
            print("no email addresses were found in user input")

        print("----------------- new code - STEP 2 - domain check and ip resolving ----------------")
        userdomain = re.search("(?P<url>https?://[^\s]+)", input) or re.search("(?P<url>www[^\s]+)", input)
        if(userdomain):
            hostname = userdomain.group('url')
            print("user requested info about domain:" + hostname)
            try:
                data = socket.gethostbyname_ex(hostname)
                ip_addresses = data[2]
                print(f"The IP Addresses of {hostname} are: {', '.join(ip_addresses)}")
            except socket.gaierror:
                print(f"Unable to resolve IP addresses for {hostname}.")
        else:
            print("no user domains were found in user input")

        print("----------------- new code - STEP 3 - CHESS speeches check  ----------------")
        chessflag = False
        pattern = r'\\bchess\\b'
        result = re.search(pattern, input)
        if(result!="none"):
            chessflag = True
        pattern = r'\\bChess\\b'
        result = re.search(pattern, input)
        if(result!="none"):
            chessflag = True
        pattern = r'\\bschacchi\\b'
        result = re.search(pattern, input)
        if(result!="none"):
            chessflag = True
        pattern = r'\\bSchacchi\\b'
        result = re.search(pattern, input)
        if(result!="none"):
            chessflag = True

        GPTchessTask = False
        if(chessflag):
            print('is a chess discussion')
            tmpoutput = ask("is the following a request for a chess puzzle:"+input+" Answer Yes or No.")
            risp = tmpoutput[:2]
            print("risposta GPT:" + risp)
            if( risp == "Ye"):
                #do chess tasks
                GPTchessTask = True
                randompuzzle = requests.get('https://pychess.run.goorm.io/api/puzzle?limit=1')
                rjson = randompuzzle.json()
                FEN = rjson.get('items')[0].get('fen')
                puzzleid = str( rjson.get('items')[0].get('puzzleid') )
                print("puzzleID:"+puzzleid+" | FEN:" + FEN)
                #log slack the puzzleid
                logp = requests.get('https://nuvolaris.dev/api/v1/web/utils/demo/slack/?text=puzzleID: '+puzzleid, auth=('user', 'pass'))

          
        output = ask(input)
        res = extract(output)
        res['output'] = output
        if(GPTchessTask):
            res['chess'] = FEN
        
    return {"body": res }

def validate_email(email):
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    match = pattern.search(email)
    return match
