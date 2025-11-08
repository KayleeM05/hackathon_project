

import os
import FreeSimpleGUI as sg
from pathlib import Path
from openai import OpenAI, OpenAIError

image_file = "aichemi.png"
USE_MODAL = False  # set False to use the local OpenRouter client path
MODAL_URL = "https://kayleemckinney345--hackathon-aichemi-project-router.modal.run"  # from `modal deploy`

# for MODAL
import requests


def call_llm_via_modal(prompt: str,
                       model: str = "openrouter/auto",
                       max_tokens: int = 512,
                       temperature: float = 0.2) -> str:
    params = {
        "prompt": prompt,
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    r = requests.get(MODAL_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["response"]


def load_openrouter_key() -> str:
    key_path = Path("secret") / "OPEN_ROUTER_API_KEY.txt"
    if not key_path.exists():
        raise RuntimeError(f"Missing {key_path}. Create it and place key in designated area.")
    raw = key_path.read_text(encoding="utf-8").strip()

    if "=" in raw:
        parts = raw.split("=", 1)[1].strip()
        if parts.startswith(("'", '"')) and parts.endswith(("'", '"')):
            parts = parts[1:-1]
        return parts.strip()
    return raw

def make_openrouter_client(api_key: str) -> OpenAI:
    return OpenAI(
    base_url = "https://openrouter.ai/api/v1",
    api_key = api_key
    )

# function to call the chat completion
def call_llm(client: OpenAI, prompt: str, model: str = "openrouter/auto", max_tokens: int = 512) -> str: 
    response = client.chat.completions.create(
        model=model,   
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

# tiny ui

def main():
    # laods keys and configures the client
    client = None
    if not USE_MODAL:
        api_key = load_openrouter_key()
        client = make_openrouter_client(api_key)

    sg.theme("Green")

    img_row = []
    if os.path.exists(image_file):
        img_row = [sg.Image(filename=image_file, subsample=6)]

    layout = [
        [sg.Column([[sg.Image(filename = image_file, subsample=6)]], justification='center')],
        [sg.Text("What separation method do you need help with?:")],
        [sg.Multiline(key="-PROMPT-", size=(60,8))],
        [sg.Button("Send"), sg.Button("Clear"), sg.Button("Quit")],
        [sg.Text("Information:")],
        [sg.Multiline(key="-RESP-", size=(60, 12), disabled=True)],
    ]

    window = sg.Window("AICHEMI mini ENGINE", layout, size = (800, 600))

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Quit", None):
            break

        if event == "Clear":
            if not window.was_closed():
                window["-PROMPT-"].update("")
                window["-RESP-"].update("")

        if event == "Send":
            prompt = (values.get("-PROMPT-") or "").strip()
            if not prompt:
                if not window.was_closed():
                    window["-RESP-"].update(disabled=False)
                    window["-RESP-"].update("Please write your seperation method before continuing.")
                    window["-RESP-"].update(disabled=True)
                continue

            # status update before network call
            if not window.was_closed():
                window["-RESP-"].update(disabled=False)
                window["-RESP-"].update("Finding your best method... (Calling OpenRouter)")
                window["-RESP-"].update(disabled=True)
            


            try:
                answer = call_llm(client, prompt) # calls locally
                # answer = call_llm_via_modal(prompt) # calls for Modal
                if not window.was_closed():
                    window["-RESP-"].update(disabled=False)
                    window["-RESP-"].update(answer)
                    window["-RESP-"].update(disabled=True)

            except OpenAIError as e:
                if not window.was_closed():
                    window["-RESP-"].update(disabled=False)
                    window["-RESP-"].update(f"OpenAIError: {e}")
                    window["-RESP-"].update(disabled=True)

            except Exception as e:
                if not window.was_closed():
                    window["-RESP-"].update(disabled=False)
                    window["-RESP-"].update(f"Error getting results:\n{type(e).__name__}: {e}")
                    window["-RESP-"].update(disabled=True)

    window.close()


if __name__ =="__main__":
    main()