import openai
import json
from secret_key import openai_api_key
import db_helper

openai.api_key = openai_api_key

#定義外部函數(get_marks, get_fees)
def get_answer(question):
    messages = [{'role': 'user', 'content': question}]
    functions = [
        {
            "name": "get_marks",
            "description": """Get the GPA for a college student or aggregate GPA (such as average, min, max) 
            for a given semester. If function returns -1 then it means we could not find the record in a database for given input. 
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "First and last Name of the student. e.g John Smith",
                    },
                    "semester": {
                        "type": "integer",
                        "description": "A number between 1 to 4 indicating the semester of a student",
                    },
                    "operation": {
                        "type": "string",
                        "description": """If student is blank that means aggregate number such as max, min or average is being
                            requested for an entire semester. semester must be passed in this case. If student field is blank and say 
                            they are passing 1 as a value in semester. Then operation parameter will tell if they need a maximum, minimum
                            or an average GPA of all students in semester 1.
                            """,
                        "enum": ["max", "min", "avg"]
                    },
                },
                "required": ["semester"],
            },
        },
        {
            "name": "get_fees",
            "description": """Get the fees for an individual student or total fees for an entire 
            semester. If function returns -1 then it means we could not find the record in a database for given input.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "First and last Name of the student. e.g John Smith",
                    },
                    "semester": {
                        "type": "integer",
                        "description": "A number between 1 to 4 indicating the semester of a student",
                    },
                    "fees_type": {
                        "type": "string",
                        "description": "fee type such as 'paid', 'pending' or 'total'",
                        "enum": ["paid", "pending", "total"]
                    },
                },
                "required": ["semester"],
            },
        }
    ]

    # 第一次與OpenAI模型互動(將問題、外部函數資訊傳給ChatGPT)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call="auto",  
    )
    response_message = response["choices"][0]["message"]

    # 檢查是否有function_call(ChatGPT分析問題，若本身知識庫無法回答，會配到對應外部函數。 )
    if response_message.get("function_call"):
        available_functions = {
            "get_marks": db_helper.get_marks,
            "get_fees": db_helper.get_fees
        }
        # 取得函數名稱與參數(ChatGPT從問題中提取關鍵資訊作為函數參數，例如學費。)
        function_name = response_message["function_call"]["name"]
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = fuction_to_call(function_args)

        # 更新聊天訊息
        messages.append(response_message)
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": str(function_response),
            }
        )

        # 第二次與OpenAI模型互動(ChatGPT將結果轉換為易讀的回答)
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )  # get a new response from GPT where it can see the function response
        return second_response["choices"][0]["message"]["content"]
    else:
        return response_message["content"]

if __name__ == '__main__':
    # 使用者的問題
    # print(get_answer("What was Peter Pandey's GPA in semester 1?"))
    # print(get_answer("average gpa in third semester?"))
    # print(get_answer("how much is peter pandey's pending fees in the first semester?"))
    print(get_answer("how much was peter pandey's due fees in the first semester?"))
    # print(get_answer("what is the purpose of a balance sheet?"))




