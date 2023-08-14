from flask import Flask, jsonify, Response, request

import requests
import openai, time, json
import flow_1

API_KEY_1 = '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'
API_KEY_2 = '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'
API_KEY_3 = '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'
GPT_API_URL = "https://api.openai.com/v1/chat/completions"
local_file_name = "test_1.mp3"

app = Flask(__name__)

DB_ANS = {}
calls = 0


@app.route("/vivr/app/health", methods=['GET'])
def health_check():
    return jsonify({'Message': "OK", 'StatusCode': 200})


@app.route("/vivr/api/v1/send_query", methods=['GET'])
def return_response():
    global calls
    api_key = API_KEY_1
    calls += 1
    if calls % 3 == 0:
        api_key = API_KEY_1
    elif calls % 3 == 1:
        api_key = API_KEY_2
    elif calls % 3 == 2:
        api_key = API_KEY_3

    url = request.args.get('RecordingUrl')
    ans_id = request.args.get('CallSid')
    print(ans_id)
    print("----------")
    mobile_no = request.args.get('From')

    download_query(url)
    response = speech_to_txt(local_file_name, api_key)
    solution = get_solution('KT1.json', response, api_key)
    print(solution)
    json_data = {
        "response": 'Unable to find resolution for the given query,transferring the call to the agent.'
    }

    if solution is None:
        DB_ANS[ans_id] = json_data['response']
        json_response = json.dumps(json_data)
        response = Response(json_response, status=404, mimetype='application/json')
    else:
        if solution == "flow_1":
            partReleaseAmt = flow_1.getMessage(mobile_no)
            json_data[response] = f"Your part release amount status is 'Not Completed' and the amount for release is {partReleaseAmt}"
            DB_ANS[ans_id] = json_data[response]
        else:
            DB_ANS[ans_id] = solution
            json_data[response] = solution
        json_response = json.dumps(json_data)
        response = Response(json_response, status=200, mimetype='application/json')

    return response


@app.route("/vivr/api/v1/get_answer", methods=['GET'])
def get_msg():
    time.sleep(2)
    ans_id = request.args.get('CallSid')
    print(ans_id)
    print(DB_ANS)
    print(DB_ANS[ans_id])
    answer = DB_ANS[ans_id]
    print("***********")
    # json_response = json.dumps(json_data)
    return Response(answer, status=200, mimetype='text/plain')


def speech_to_txt(file, api_key):
    audio = open(file, "rb")
    transcript = openai.Audio.translate("whisper-1", audio, api_key=api_key)
    print(transcript.text)
    return transcript.text


def download_query(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            with open(local_file_name, "wb") as file:
                file.write(response.content)
            print("File downloaded successfully.")
        else:
            print(f"Error: Failed to download the file. HTTP status code: {response.status_code}")

    except Exception as e:
        print("Error:", str(e))


def get_solution(file_name, query, api_key):
    # Open the JSON file
    with open(file_name, 'r') as file:
        file_data = json.load(file)
        print(file_data)

        file_dict = {}
        intent_arr = []

        for key, value in file_data.items():
            file_dict[key] = value
            intent_arr.append(key)
        intent_index = get_max_confidence(intent_arr, query, api_key)
        if intent_index == -1:
            return None
        else:
            return file_dict[intent_arr[intent_index]]


def get_max_confidence(intents, query, api_key):
    confidence_array = None
    confidence_score = -1
    retry_count = 1
    # messages = [
    #     {"role": "system",
    #      "content": "You are an AI language model trained to match and give only the confidence value in integer "
    #                 "between 0-100 for an provided intent and a caller's query"},
    #     {"role": "user",
    #      "content": f"Match and give a confidence in integer between 0-100 for the provided intent:{intent} strictly "
    #                 f"and provided caller's query:{query}"}
    # ]
    messages = [
        {
            "role": "system",
            "content": "You are an AI language model trained to match and give only the confidence value strictly as "
                       "integer between 0-100 for an each intent from intent array  and a caller's query "
        },
        {
            "role": "user",
            "content": f"Match and give a confidence strictly as integer array with each element between 0-100 for "
                       f"the provided intent array:{intents} "
                       f"and provided caller's query: {query}"
        }
    ]
    while retry_count > 0:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.8,
            api_key=api_key
        )

        response_text = response.choices[0].message.content
        if response_text:
            print(response_text)
            confidence_array = json.loads(response_text)
            break
        else:
            retry_count -= 1
            time.sleep(30)

    if confidence_array:
        for i in range(len(confidence_array)):
            print(i)
            print(confidence_array[i])
            if confidence_array[i] >= 50:
                if confidence_score != -1 and confidence_array[i] > confidence_array[confidence_score]:
                    confidence_score = i
                elif confidence_score == -1:
                    confidence_score = i
    print(confidence_score)
    return confidence_score


if __name__ == "__main__":
    app.run(host="localhost", port=8080)
