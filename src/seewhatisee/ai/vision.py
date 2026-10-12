import base64

class VisionError(RuntimeError):
    pass


class VisionService:
    def __init__(self, api_key: str, model: str, base_url: str = "") -> None:
        from openai import OpenAI

        self.model = model
        client_options = {"api_key": api_key or "ollama", "timeout": 45.0, "max_retries": 1}
        if base_url:
            client_options["base_url"] = base_url
        self.client = OpenAI(**client_options)

    def answer(self, image_bytes: bytes, question: str) -> str:
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are SeeWhatISee, a concise and helpful screen understanding assistant. Describe only what can be inferred from the provided screen. Start with a direct answer, then use short Markdown headings and bullet points when they improve clarity. For extracted text, preserve exact wording and use a code block when useful. Do not invent details that are not visible.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}},
                        ],
                    },
                ],
                max_tokens=700,
            )
        except Exception as error:
            raise VisionError(self._message_for_error(error)) from error

        answer = response.choices[0].message.content if response.choices else None
        if not answer or not answer.strip():
            raise VisionError("The AI returned an empty response. Please try asking again.")
        return answer.strip()

    @staticmethod
    def _message_for_error(error: Exception) -> str:
        text = str(error).lower()
        if "authentication" in text or "api key" in text or "401" in text:
            return "The API key was rejected. Check OPENAI_API_KEY in your .env file."
        if "timeout" in text or "timed out" in text:
            return "The AI request timed out. Check your connection and try again."
        if "rate limit" in text or "429" in text:
            return "The AI service rate limit was reached. Please wait and try again."
        return "The AI request failed. Check your connection and model configuration, then try again."
