# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from functools import wraps

# Knihovny třetích stran (nainstalované přes pip)
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from flask_mysqldb import MySQL

from openai import OpenAI
from socketio_instance import socketio  # Importujeme socketio

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from utils.utils import *
from utils.decorators import *
from db.sql_query import *

# Definice blueprintu pro uživatele
gpt_bp = Blueprint('gpt', __name__)
#api_key = os.getenv("OPENAI_API_KEY")  # Načtení klíče z proměnné prostředí
client = OpenAI()   # ← načte OPENAI_API_KEY z prostředí


@gpt_bp.route('/gpt', methods=['GET', 'POST'])
@login_required
@project_required
def gpt():
    try:
        data = request.get_json(force=True) or {}
        configGPT  = data.get('configGPT', '')
        textForGPT = data.get('textForGPT', '')
        gptModel   = data.get('gptModel') or 'gpt-4o-mini'

        prompt = f"{configGPT}\n{textForGPT}"

        # --- Rozlišení API podle modelu ---
        if gptModel.startswith("o1"):
            # Responses API
            resp = client.responses.create(
                model=gptModel,
                input=[{"role": "user", "content": prompt}]
            )

            parts = []
            for item in getattr(resp, "output", []) or []:
                if getattr(item, "type", "") == "message":
                    for ct in item.content:
                        if getattr(ct, "type", "") == "output_text":
                            parts.append(ct.text)
            result = "\n".join(parts).strip()

            model_used   = resp.model
            input_tokens = getattr(getattr(resp, "usage", None), "input_tokens", None)
            output_tokens= getattr(getattr(resp, "usage", None), "output_tokens", None)

        else:
            # Chat Completions API
            resp = client.chat.completions.create(
                model=gptModel,
                messages=[{"role": "user", "content": prompt}]
            )

            result       = resp.choices[0].message.content
            model_used   = resp.model
            input_tokens = getattr(resp.usage, "prompt_tokens", None)
            output_tokens= getattr(resp.usage, "completion_tokens", None)

        return jsonify({
            "generatedText": result,
            "model_used": model_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }), 200

    except Exception as e:
        traceback.print_exc()
        current_app.logger.exception("GPT route failed")
        return jsonify({"error": str(e)}), 500


def gpts():
    print("GPT")
    data = request.get_json()
    configGPT = data.get('configGPT')
    textForGPT = data.get('textForGPT')
    gptModel = data.get('gptModel') or 'gpt-4o-mini'   # default
    prompt = f"{configGPT}\n{textForGPT}"

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="o1-preview",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    print(response.choices[0].message.content)




    model_used = response.model
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    result = response.choices[0].message.content
    
    # Vrácení generovaného textu jako odpověď
    return jsonify({'generatedText': result, 'model_used': model_used, 'input_tokens':input_tokens, 'output_tokens': output_tokens})



@gpt_bp.route('/gpt', methods=['GET', 'POST'])
@login_required
@project_required
def gpt_backup():

    client = OpenAI(api_key=api_key)  # Předání klíče při inicializaci klienta

    available_models = client.models.list()
    print([model.id for model in available_models])  # Vypsat všechny dostupné modely

    data = request.get_json()
    configGPT = data.get('configGPT')
    textForGPT = data.get('textForGPT')
    gptModel = data.get('gptModel')
    prompt = f"{configGPT}\n{textForGPT}"

    
    completion = client.chat.completions.create(
        model=gptModel,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": prompt
                    }
                ]
            }
        ]
    )

    model_used = completion.model
    input_tokens = completion.usage.prompt_tokens
    output_tokens = completion.usage.completion_tokens
    result = completion.choices[0].message.content
    
    # Vrácení generovaného textu jako odpověď
    return jsonify({'generatedText': result, 'model_used': model_used, 'input_tokens':input_tokens, 'output_tokens': output_tokens})

def getGPTModels():
    client = OpenAI(api_key=api_key)  # Předání klíče při inicializaci klienta
    return [model.id for model in client.models.list().data]
