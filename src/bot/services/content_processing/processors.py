import asyncio
import logging
import re
from abc import ABC, abstractmethod

import openai
from psycopg.errors import UniqueViolation

from bot.database.exceptions import AISettingsNotFoundError
from bot.database.models import FlowDTO
from bot.services.aisettings_service import AISettingsService
from bot.utils.notifications import notify_admins


class ContentProcessor(ABC):
    @abstractmethod
    async def process(self, text: str) -> str:
        pass


class DefaultContentProcessor:
    def __init__(self):
        self.patterns = {
            "hidden_chars": re.compile(r"[\u200B-\u200D\uFEFF]"),
            "bold_asterisks": re.compile(r"\*\*([^*]+)\*\*"),
            "markdown_links": re.compile(r"\[([^\]]+)\]\([^)]+\)"),
            "urls": re.compile(r"https?://\S+|www\.\S+"),
        }

    async def process(self, text: str) -> str:
        if not text:
            return ""

        text = self.patterns["hidden_chars"].sub("", text)

        text = self.patterns["urls"].sub("", text)
        text = self.patterns["markdown_links"].sub("", text)

        text = self.patterns["bold_asterisks"].sub(r"<b>\1</b>", text)

        text = " ".join(text.split())
        return text.strip()


class ChatGPTContentProcessor(ContentProcessor):
    def __init__(
        self,
        api_key: str,
        flow: FlowDTO,
        aisettings_service: AISettingsService,
        model: str = "gpt-4o-mini",
        max_retries: int = 5,
        timeout: float = 15.0,
        cache_size_limit: int = 1000,
    ):
        self.cache = {}
        self.flow = flow
        self.model = model
        self.max_batch_size: int = 5
        self.max_retries = max_retries
        self.request_timeout = timeout
        self.cache_size_limit = cache_size_limit
        self.aisettings_service = aisettings_service
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=timeout)

    async def process_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []

        results = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i : i + self.max_batch_size]
            batch_results = await asyncio.gather(
                *[self.process(text) for text in batch]
            )
            results.extend(batch_results)

            if i + self.max_batch_size < len(texts):
                await asyncio.sleep(3)

        return results

    async def _get_or_create_user_prompt(self, text: str, flow: FlowDTO) -> str:
        default_prompt = self._build_system_prompt(text)
        try:
            aisettings = await self.aisettings_service.get_aisettings_by_flow(flow)
            if aisettings.use_custom_prompt and aisettings.prompt:
                return aisettings.prompt
            return default_prompt

        except AISettingsNotFoundError:
            try:
                await self.aisettings_service.create_aisettings(
                    flow=flow, prompt=default_prompt, style=str(flow.theme)
                )
            except UniqueViolation:
                aisettings = await self.aisettings_service.get_aisettings_by_flow(flow)
                return (
                    aisettings.prompt
                    if aisettings.use_custom_prompt
                    else default_prompt
                )
            except Exception as create_error:
                logging.error(f"Error creating AI settings: {create_error!s}")
            return default_prompt

        except Exception as e:
            logging.error(f"Error getting flow prompt: {e!s}")
            return default_prompt

    async def process(self, text: str) -> str:
        try:
            if isinstance(text, list):
                text = " ".join([str(item) for item in text if item])

            if not text.strip():
                return ""

            cache_key = hash(f"{text}_{self.flow.id}")
            if cache_key in self.cache:
                return self.cache[cache_key]

            system_prompt = await self._get_prompt(text, self.flow)
            result = await self._call_ai_with_retry(text, system_prompt)

            if len(self.cache) >= self.cache_size_limit:
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = result

            return result

        except openai.RateLimitError as e:
            logging.error(f"OpenAI quota exceeded: {e!s}")
            error_msg = (
                f"⚠️ <b>OpenAI Quota Exceeded</b>\n\n"
                f"Flow: <code>{self.flow.name}</code> (ID: {self.flow.id})\n"
                f"Model: <code>{self.model}</code>\n\n"
                f"Error: <code>{str(e)[:200]}</code>\n\n"
                f"Повертаємо оригінальний текст без обробки."
            )
            await self._notify_admin(error_msg)
            # Return special marker to indicate processing failed
            return None

        except openai.APIError as e:
            logging.error(f"OpenAI API error: {e!s}")
            error_msg = (
                f"❌ <b>OpenAI API Error</b>\n\n"
                f"Flow: <code>{self.flow.name}</code> (ID: {self.flow.id})\n"
                f"Model: <code>{self.model}</code>\n\n"
                f"Error: <code>{str(e)[:200]}</code>"
            )
            await self._notify_admin(error_msg)
            # Return special marker to indicate processing failed
            return None

        except Exception as e:
            logging.error(f"Unexpected processing error: {e!s}", exc_info=True)
            # Return special marker to indicate processing failed
            return None

    async def _call_ai_with_retry(self, text: str, system_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # aisettings = await self.aisettings_service.get_aisettings_by_flow(flow)

        # if aisettings.role and aisettings.role.strip():
        #     valid_roles = {"system", "assistant", "user", "function", "tool", "developer"}
        #     if aisettings.role.lower() in valid_roles:
        #         messages.append({
        #             "role": aisettings.role.lower(),
        #             "content": aisettings.role_content,
        #         })

        messages.append({"role": "user", "content": text})

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.5,
                    top_p=0.9,
                    max_tokens=2000,
                    timeout=self.request_timeout,
                )
                result = response.choices[0].message.content.strip()
                # Enforce strict length limit
                result = self._enforce_length_limit(result)
                return result

            except openai.RateLimitError as e:
                last_error = e
                if attempt == self.max_retries:
                    raise
                wait_time = min(5, 2 ** attempt)
                logging.info(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}")
                await asyncio.sleep(wait_time)

            except openai.APIError as e:
                last_error = e
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(1)

            except Exception as e:
                last_error = e
                if attempt == self.max_retries:
                    raise openai.APIError(f"Unexpected error: {e!s}") from e
                await asyncio.sleep(1)

        raise (
            last_error if last_error else openai.APIError("Unknown error after retries")
        )

    async def _notify_admin(self, message: str):
        try:
            await notify_admins(message, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Failed to send admin notification: {e!s}")

    async def _get_prompt(self, text: str, flow: FlowDTO) -> str:
        return await self._get_or_create_user_prompt(text, flow)

    def _build_system_prompt(self, text: str) -> str:
        max_chars = self._get_length_instruction()
        rules = [
            "You are a professional post editor.",
            "Translate it to Ukrainian.",
            "Edit the text according to the following rules:",
            "1. Keep the original meaning, but improve readability and clarity.",
            "2. Remove unnecessary links, formatting artifacts, hashtags, and special characters.",
            f"3. IMPORTANT: The final text MUST be {max_chars} or less. This is a strict requirement.",
            f"   If the content is longer, summarize or trim it while preserving key information.",
            f"4. Rewrite the text in the following style: {self.flow.theme}.",
        ]

        rule_num = 5
        if self.flow.use_emojis:
            emoji_type = "premium" if self.flow.use_premium_emojis else "regular"
            rules.append(f"{rule_num}. Use relevant {emoji_type} emojis")
            rule_num += 1

        if self.flow.title_highlight:
            rules.append(
                f"{rule_num}. Format the title using <b> tags, and add an empty line immediately after it."
            )
            rule_num += 1

        if self.flow.cta:
            rules.append(f"{rule_num}. Add CTA: {self.flow.cta}")
            rule_num += 1

        rules.append("Return only the edited content without commentary.")
        return "\n".join(rules)

    def _get_length_instruction(self) -> str:
        length_mapping = {
            "to_100": "100 characters",
            "to_300": "300 characters",
            "to_1000": "1000 characters",
        }
        return length_mapping.get(self.flow.content_length, "300 characters")

    def _get_max_length(self) -> int:
        """Get maximum length in characters for the current flow"""
        length_mapping = {
            "to_100": 100,
            "to_300": 300,
            "to_1000": 1000,
        }
        return length_mapping.get(self.flow.content_length, 300)

    def _enforce_length_limit(self, text: str) -> str:
        """Enforce strict length limit by truncating text if needed"""
        max_length = self._get_max_length()
        original_length = len(text)

        if original_length <= max_length:
            return text

        logging.info(
            f"Truncating content from {original_length} to {max_length} chars "
            f"for flow {self.flow.id} ({self.flow.name})"
        )

        # Truncate at max_length, trying to break at a sentence or word boundary
        truncated = text[:max_length]

        # Try to break at sentence boundary
        last_sentence = max(
            truncated.rfind(". "),
            truncated.rfind("! "),
            truncated.rfind("? "),
            truncated.rfind("\n"),
        )

        if last_sentence > max_length * 0.7:  # If we found a good break point (>70% of max)
            return truncated[: last_sentence + 1].strip()

        # Otherwise, try to break at word boundary
        last_space = truncated.rfind(" ")
        if last_space > max_length * 0.8:  # If we found a word boundary (>80% of max)
            return truncated[:last_space].strip() + "..."

        # Last resort: hard truncate
        return truncated.strip() + "..."
