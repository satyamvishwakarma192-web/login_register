import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_KEY = os.getenv("OPENMOUTHED_API_KEY")
BASE_URL = os.getenv("OPENMOUTHED_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENMOUTHED_API_KEY is not set")

    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": "anthropic/claude-haiku-4.5",
        "messages": [{"role": "user", "content": args.p}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "Read",
                "description": "Read and return the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }],
        "tools_call": [
            {
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "Read",
              "arguments": "{\"file_path\": \"/path/to/file.txt\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}

        ]

        }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8")
        raise RuntimeError(f"API request failed: {exc.code} {exc.reason}: {error_text}") from exc

    chat = json.loads(response_text)
    choices = chat.get("choices")
    if not choices:
        raise RuntimeError("no choices in response")

    print("Logs from your program will appear here!", file=sys.stderr)

    message = choices[0].get("message") or {}
    content = message.get("content")
    if content is None:
        content = choices[0].get("text", "")

    print(content)

    for tc in chat.choices[0].message.tool_calls or []:
        args = json.loads(tc.function.arguments)
        if tc.function.name == "Read":
            with open(args["file_path"]) as f:
                print(f.read())


if __name__ == "__main__":
    main()
