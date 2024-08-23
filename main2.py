import os
import json
import openai
import subprocess
import re

# OpenAI API 설정
api_key_file = "data/api_key.txt"

with open(api_key_file, 'r', encoding='utf-8') as file:
    openai.api_key = file.read()
# 타겟 디렉토리
target_dir = 'test'
# ChatGPT API 호출 함수
exeute_gpt_system = f"""
터미널이 필요할 경우 '[ter]ifconfig' 이런식으로 맨 앞에[ter] 을 작성하여라.
터미널로 가능할 경우 되도록 터미널을 사용할 것.
파일에 내용을 삽입할 경우 '
[edit]파일이름
수정할 파일내용

으로 작성할 것. 
예를들어

[edit]main.py
import random

print(random.randint(1,10))

이런식으로.

파일을 수정할 경우 파일의 모든 결과 코드를 작성할 것. 예를들어서 main.py의 print(1+1) 의 +를 -로 수정해야 할 경우,
[edit]main.py
print(1-1)

이런식으로.

또한 파이썬 str 에 사용하듯이 특수한 문자는 앞에 '를 붙여

또한 작업은 여러 개 동시에 실행 가능
예를들어 a 폴더를 만들고 그 안에 example.txt 파일을 만든 후 출력할 경우
[ter]mkdir a

[edit]a/example.txt
test

[ter]cat a/example.txt 

이런식으로
아무 말도 하지 말고 명령어만 작성할 것.
또한 코드를 절대 직접 실행하지 말 것.
또한 절차를 진행할 때 한번에 하지 말고 현재 필요한 절차를 하나만 차근차근 진행할 것"""

bool_gpt_system = """
모든 질문에는 오직 True 와 False 로만 대답"""

try:
    messages_file = "data/message_history.json"

    with open(messages_file, 'r', encoding='utf-8') as file:
        messages = json.load(file)

except:
    print(12345)
    messages = []
    messages.append({"role": "system", "content": exeute_gpt_system})


def gpt(system, prompt):
    print(f"\n[명령]: {prompt}")
    #messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages
    )
    answer = response['choices'][0]['message']['content']
    print(f"[AI]: {answer}\n")
    messages.append({"role": "assistant", "content": answer})
    save_messages()

    return answer

def exeute_gpt(prompt):
    a = gpt(exeute_gpt_system, prompt)
    cmd_exeute(a)
    return a

def bool_gpt(prompt):
    print(f"\n[검토]: {prompt}")
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": bool_gpt_system},
                  {"role": "user", "content": prompt}]
    )
    answer = response['choices'][0]['message']['content']
    print(f"[AI]: {answer}\n")
    save_messages()

    return answer

def finish_gpt(prompt):
    print(f"\n[검토]: {prompt}")
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"""모든 폴더, 파일 내용을 분석한 후 정리, 요약본, 사용 방법을 작성할 것.
                   내용은 무조건 [edit]README.txt 를 작성 후 다음줄 부터 작성. 예를들어서
                   [edit]README.txt
                   이 코드는 ~~~
                   사용 방법은 ~~~

                   아무 말도 하지 말고 오직 명령만 수행할 것.
                   말투는 내 말투와 동일하게 할 것.
                   """},
                  {"role": "user", "content": prompt}]
    )
    answer = response['choices'][0]['message']['content']
    print(f"[AI]: {answer}\n")
    save_messages()
    cmd_exeute(answer)
    return answer

def cmd_exeute(input_string):
    # [edit]와 [ter]를 구분자로 문자열 분리 (정규 표현식)
    sections = re.split(r'(\[edit\]|\[ter\])', input_string)

    current_command = None

    for section in sections:
        section = section.strip()
        if section == "[edit]":
            current_command = "edit"
        elif section == "[ter]":
            current_command = "ter"
        elif current_command == "edit" and section:
            # [edit] 부분 처리: 파일을 생성하고 내용을 작성
            lines = section.split("\n", 1)  # 첫 줄과 나머지 내용으로 분리
            file_name = target_dir+ "/" + lines[0].strip()  # 파일 이름 추출
            content = lines[1] if len(lines) > 1 else ""  # 나머지 내용

            # 파일에 내용을 쓰기 (utf-8 인코딩)
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(content)
            print(f"{file_name} 파일이 생성되었습니다.")
            current_command = None  # 완료 후 명령 초기화
        elif current_command == "ter" and section:
            # [ter] 부분 처리: 터미널 명령어 실행
            cmd = section.strip()
            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"터미널 명령 '{cmd}'가 실행되었습니다.")
            except subprocess.CalledProcessError as e:
                print(f"명령어 실행 실패: {e}")
            current_command = None  # 완료 후 명령 초기화

def get_files_content(directory):
    files_content = {}
    
    # os.walk를 사용하여 폴더와 하위 폴더를 재귀적으로 탐색
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            
            # 파일을 읽어서 딕셔너리에 저장 (경로를 키로 사용)
            with open(file_path, 'r', encoding='utf-8') as file:
                relative_path = os.path.relpath(file_path, directory)  # 상대 경로로 저장
                files_content[relative_path] = file.read()
    files_content.pop('step.txt', None)

    return files_content

def save_messages():
    with open("data/message_history.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)


goal = input("최종 목표: ")
# goal = "gui 로또 프로그램"

messages.append({"role": "user", "content": goal})

while True:
    exeute_gpt(f"넌 개발자야. 최종 목표 '{goal}' 를 수행하기 위해 네 능력으로 할 수 있는 선에서 절차를 한글로 짠 후 step.txt 에 저장. 테스트는 내가 할테니 제작 절차만 짜")

    step_file = f"{target_dir}/step.txt"
    with open(step_file, 'r', encoding='utf-8') as file:
        step = file.read()

    con = f"프로젝트는 '{goal}' 이며, 수행을 위한 절차는 '{step}' 이야. 적합해?"
    if bool_gpt(con) == "True":
        print("[System]: 절차 적합, 프로젝트 시작.")
        break
    print("[System]: 절차 부적합.")


while True:
    con = f"절차는 '{step}' 이며, 현재 프로젝트 폴더는 '{get_files_content(target_dir)}' 이런 상태야."
    if bool_gpt(f"{con} 모든 절차가 완료됐어?") == "True":
        print("[System]: 목표 완수, 프로젝트 종료.")
        break
    exeute_gpt(f"{con} 절차대로 지금 필요한 단계를 진행해 " + "{} 만 있다면 진행상황은 0%라는 뜻이야")

finish_gpt(f"파일 정보는: '{get_files_content(target_dir)}'")