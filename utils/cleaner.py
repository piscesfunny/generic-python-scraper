import re


def clean_extra_whitespace(text: str) -> str:
    cleaned_text = re.sub(r"[\xa0\n]", " ", text)
    cleaned_text = re.sub(r"([ ]{2,})", " ", cleaned_text)
    return cleaned_text.strip()


def clean_characters_for_folder_name(name):
    """
    Removes characters that are not allowed in folder names.
    Allowed characters are letters, numbers, spaces, and the following: _-.()
    """
    # Regular expression to match any disallowed characters
    disallowed_chars_pattern = r'[<>:"/\\|?*\']+'

    # Replace disallowed characters with an empty string
    cleaned_name = re.sub(disallowed_chars_pattern, '', name)
    return cleaned_name
