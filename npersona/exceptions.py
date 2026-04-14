"""Custom exceptions for NPersona."""


class NPersonaError(Exception):
    """Base exception for all NPersona errors."""


class DocumentParseError(NPersonaError):
    """Raised when a document cannot be parsed."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to parse document '{path}': {reason}")


class UnsupportedFormatError(NPersonaError):
    """Raised when a document format is not supported."""

    def __init__(self, extension: str) -> None:
        self.extension = extension
        super().__init__(
            f"Unsupported document format: '{extension}'. "
            "Supported: .pdf, .docx, .md, .txt. "
            "Install optional deps: pip install npersona[pdf] or npersona[docx]"
        )


class LLMError(NPersonaError):
    """Raised when an LLM call fails after all retries."""

    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(f"LLM call failed [{provider}]: {reason}")


class LLMParseError(NPersonaError):
    """Raised when LLM response cannot be parsed as expected JSON."""

    def __init__(self, raw_response: str) -> None:
        self.raw_response = raw_response
        super().__init__("LLM returned output that could not be parsed as valid JSON.")


class ProfileExtractionError(NPersonaError):
    """Raised when system profile extraction produces unusable output."""


class ExecutorError(NPersonaError):
    """Raised when sending a test case to the target system fails."""

    def __init__(self, test_case_id: str, reason: str) -> None:
        self.test_case_id = test_case_id
        self.reason = reason
        super().__init__(f"Executor failed for test case '{test_case_id}': {reason}")


class RCAError(NPersonaError):
    """Raised when RCA analysis fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"RCA analysis failed: {reason}. Ensure architecture_doc is provided.")
