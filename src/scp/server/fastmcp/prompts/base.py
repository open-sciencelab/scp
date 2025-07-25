"""Base classes for FastMCP prompts."""

import inspect
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Literal

import pydantic_core
from pydantic import BaseModel, Field, TypeAdapter, validate_call

from scp.types import EmbeddedResource, ImageContent, TextContent

CONTENT_TYPES = TextContent | ImageContent | EmbeddedResource


class Message(BaseModel):
    """Base class for all prompt messages."""

    role: Literal["user", "assistant"]
    content: CONTENT_TYPES

    def __init__(self, content: str | CONTENT_TYPES, **kwargs: Any):
        if isinstance(content, str):
            content = TextContent(type="text", text=content)
        super().__init__(content=content, **kwargs)


class UserMessage(Message):
    """A message from the user."""

    role: Literal["user", "assistant"] = "user"

    def __init__(self, content: str | CONTENT_TYPES, **kwargs: Any):
        super().__init__(content=content, **kwargs)


class AssistantMessage(Message):
    """A message from the assistant."""

    role: Literal["user", "assistant"] = "assistant"

    def __init__(self, content: str | CONTENT_TYPES, **kwargs: Any):
        super().__init__(content=content, **kwargs)


message_validator = TypeAdapter[UserMessage | AssistantMessage](
    UserMessage | AssistantMessage
)

SyncPromptResult = (
    str | Message | dict[str, Any] | Sequence[str | Message | dict[str, Any]]
)
PromptResult = SyncPromptResult | Awaitable[SyncPromptResult]


class PromptArgument(BaseModel):
    """An argument that can be passed to a prompt."""

    name: str = Field(description="Name of the argument")
    description: str | None = Field(
        None, description="Description of what the argument does"
    )
    required: bool = Field(
        default=False, description="Whether the argument is required"
    )


class Prompt(BaseModel):
    """A prompt template that can be rendered with parameters."""

    name: str = Field(description="Name of the prompt")
    description: str | None = Field(
        None, description="Description of what the prompt does"
    )
    arguments: list[PromptArgument] | None = Field(
        None, description="Arguments that can be passed to the prompt"
    )
    fn: Callable[..., PromptResult | Awaitable[PromptResult]] = Field(exclude=True)

    @classmethod
    def from_function(
        cls,
        fn: Callable[..., PromptResult | Awaitable[PromptResult]],
        name: str | None = None,
        description: str | None = None,
    ) -> "Prompt":
        """Create a Prompt from a function.

        The function can return:
        - A string (converted to a message)
        - A Message object
        - A dict (converted to a message)
        - A sequence of any of the above
        """
        func_name = name or fn.__name__

        if func_name == "<lambda>":
            raise ValueError("You must provide a name for lambda functions")

        # Get schema from TypeAdapter - will fail if function isn't properly typed
        parameters = TypeAdapter(fn).json_schema()

        # Convert parameters to PromptArguments
        arguments: list[PromptArgument] = []
        if "properties" in parameters:
            for param_name, param in parameters["properties"].items():
                required = param_name in parameters.get("required", [])
                arguments.append(
                    PromptArgument(
                        name=param_name,
                        description=param.get("description"),
                        required=required,
                    )
                )

        # ensure the arguments are properly cast
        fn = validate_call(fn)

        return cls(
            name=func_name,
            description=description or fn.__doc__ or "",
            arguments=arguments,
            fn=fn,
        )

    async def render(self, arguments: dict[str, Any] | None = None) -> list[Message]:
        """Render the prompt with arguments."""
        # Validate required arguments
        if self.arguments:
            required = {arg.name for arg in self.arguments if arg.required}
            provided = set(arguments or {})
            missing = required - provided
            if missing:
                raise ValueError(f"Missing required arguments: {missing}")

        try:
            # Call function and check if result is a coroutine
            result = self.fn(**(arguments or {}))
            if inspect.iscoroutine(result):
                result = await result

            # Validate messages
            if not isinstance(result, list | tuple):
                result = [result]

            # Convert result to messages
            messages: list[Message] = []
            for msg in result:  # type: ignore[reportUnknownVariableType]
                try:
                    if isinstance(msg, Message):
                        messages.append(msg)
                    elif isinstance(msg, dict):
                        messages.append(message_validator.validate_python(msg))
                    elif isinstance(msg, str):
                        content = TextContent(type="text", text=msg)
                        messages.append(UserMessage(content=content))
                    else:
                        content = pydantic_core.to_json(
                            msg, fallback=str, indent=2
                        ).decode()
                        messages.append(Message(role="user", content=content))
                except Exception:
                    raise ValueError(
                        f"Could not convert prompt result to message: {msg}"
                    )

            return messages
        except Exception as e:
            raise ValueError(f"Error rendering prompt {self.name}: {e}")
