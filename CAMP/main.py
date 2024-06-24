from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/teams', methods=['POST'])
def teams():
    print("teams route hit")
    data = request.get_json()
    headers = request.headers
    print(f"Received teams headers: {headers}")
    print(f"Received teams data: {data}")
    
    # Extract user information from the incoming data
    user_id = data.get('from', {}).get('id')
    user_name = data.get('from', {}).get('name')

    # Construct the Adaptive Card with a mention
    response = {
        "text": "Thank you for your message! We will process your request shortly.",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Webhook Received",
                            "weight": "bolder",
                            "size": "medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Hello <at>{user_name}</at>, your data has been received and processed.",
                            "wrap": True
                        },
                        # {
                        #     "type": "FactSet",
                        #     "facts": [
                        #         {
                        #             "title": "Status:",
                        #             "value": "Success"
                        #         },
                        #         {
                        #             "title": "Data:",
                        #             "value": str(data)
                        #         }
                        #     ]
                        # }
                    ],
                    "msteams": {
                        "entities": [
                            {
                                "type": "mention",
                                "text": f"<at>{user_name}</at>",
                                "mentioned": {
                                    "id": user_id,
                                    "name": user_name
                                }
                            }
                        ]
                    },
                    # "actions": [
                    #     {
                    #         "type": "Action.OpenUrl",
                    #         "title": "Learn More",
                    #         "url": "https://example.com"
                    #     }
                    # ]
                }
            }
        ]
    }
    return jsonify(response), 200

@app.route('/verizon', methods=['POST'])
def verizon():
    print("verizon route hit")
    data = request.get_json()
    headers = request.headers
    print(f"Received verizon headers: {headers}")
    print(f"Received verizon data: {data}")

    # Create a response that Microsoft Teams will accept
    response = {
        "text": "Thank you for your message!",
    }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
