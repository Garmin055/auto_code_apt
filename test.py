import os
import json
import openai
import subprocess
import re

# OpenAI API setup
api_key_file = "data/api_key.txt"

with open(api_key_file, 'r', encoding='utf-8') as file:
    openai.api_key = file.read()
# Target directory
target_dir = 'test'
# ChatGPT API call function
exeute_gpt_system = f"""
If you need a terminal, write '[ter]ifconfig' like this by writing [ter] at the beginning.
If possible, use the terminal when it can be done via terminal.
When inserting content into a file, use the format '
[edit]filename
File content to be modified

For example

[edit]main.py
import random

print(random.randint(1,10))

Like this.

If modifying a file, write the entire code of the file. For example, if you need to modify the '+' in main.py's 'print(1+1)' to a '-',
[edit]main.py
print(1-1)

Like this.

Also, you can execute multiple tasks simultaneously.
For example, to create folder 'a', then create a file 'example.txt' inside it and print it out:
[ter]mkdir a

[edit]a/example.txt
test

[ter]cat a/example.txt

Write only commands. 
Also, never run code directly.
Also, proceed step by step, only one at a time."""

bool_gpt_system = """
Answer all questions only with True or False."""

try:
    messages_file = "data/message_history.json"

    with open(messages_file, 'r', encoding='utf-8') as file:
        messages = json.load(file)

except:
    print(12345)
    messages = []
    messages.append({"role": "system", "content": exeute_gpt_system})


def gpt(system, prompt):
    print(f"\n[Command]: {prompt}")
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
    print(f"\n[Verification]: {prompt}")
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
    print(f"\n[Verification]: {prompt}")
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"""After analyzing the entire folder and file contents, summarize and write usage instructions.
                   Always create [edit]README.txt and write from the next line. For example:
                   [edit]README.txt
                   This code does ~~~
                   Usage instructions are ~~~

                   Only perform the commands, do not say anything.
                   Also, keep the same tone as my instructions."""},
                  {"role": "user", "content": prompt}]
    )
    answer = response['choices'][0]['message']['content']
    print(f"[AI]: {answer}\n")
    save_messages()
    cmd_exeute(answer)
    return answer

def cmd_exeute(input_string):
    # Split string by [edit] and [ter] using regex
    sections = re.split(r'(\[edit\]|\[ter\])', input_string)

    current_command = None

    for section in sections:
        section = section.strip()
        if section == "[edit]":
            current_command = "edit"
        elif section == "[ter]":
            current_command = "ter"
        elif current_command == "edit" and section:
            # Handle [edit] part: create and write to a file
            lines = section.split("\n", 1)  # Split into filename and content
            file_name = target_dir + "/" + lines[0].strip()  # Extract filename
            content = lines[1] if len(lines) > 1 else ""  # Extract content

            # Write to the file (utf-8 encoding)
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(content)
            print(f"{file_name} has been created.")
            current_command = None  # Reset command after completion
        elif current_command == "ter" and section:
            # Handle [ter] part: execute terminal command
            cmd = section.strip()
            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"The terminal command '{cmd}' has been executed.")
            except subprocess.CalledProcessError as e:
                print(f"Command execution failed: {e}")
            current_command = None  # Reset command after completion

def get_files_content(directory):
    files_content = {}
    
    # Recursively explore folder and subfolders using os.walk
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            
            # Read the file and store in dictionary (use path as key)
            with open(file_path, 'r', encoding='utf-8') as file:
                relative_path = os.path.relpath(file_path, directory)  # Store as relative path
                files_content[relative_path] = file.read()
    files_content.pop('step.txt', None)

    return files_content

def save_messages():
    with open("data/message_history.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)


goal = input("Final Goal: ")
# goal = "GUI Lotto Program"

messages.append({"role": "user", "content": goal})

while True:
    exeute_gpt(f"You are a developer. To achieve the final goal '{goal}', create the procedure based on your capabilities and save it in step.txt. I'll handle the testing, so just write the steps for production.")

    step_file = f"{target_dir}/step.txt"
    with open(step_file, 'r', encoding='utf-8') as file:
        step = file.read()

    con = f"The project is '{goal}', and the steps to perform are '{step}'. Are they appropriate?"
    if bool_gpt(con) == "True":
        print("[System]: Steps are appropriate, starting the project.")
        break
    print("[System]: Steps are inappropriate.")


while True:
    con = f"The steps are '{step}', and the current project folder is '{get_files_content(target_dir)}'."
    if bool_gpt(f"{con} Have all the steps been completed?") == "True":
        print("[System]: Goal achieved, project completed.")
        break
    exeute_gpt(f"{con} Follow the steps needed now."+" If only {} exists, it means 0% progress has been made.")

finish_gpt(f"File information: '{get_files_content(target_dir)}'")
