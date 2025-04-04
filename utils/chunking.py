from typing import Union, List, Callable, Union


def calc_end_codeblock(chunk, chunk_size, start) -> Union[int, bool]:
    code_block = chunk.rfind("```")
    if code_block == -1 or code_block <= chunk_size * 0.3:
        return False

    return start + code_block


def calc_end_paragraph(chunk, chunk_size, start) -> Union[int, bool]:
    last_break = chunk.rfind("\n\n")

    if last_break == -1 or last_break <= chunk_size * 0.3:
        return False

    return start + last_break


def calc_end_sentence(chunk, chunk_size, start) -> Union[int, bool]:
    last_period = chunk.rfind(". ")

    if last_period == -1 or last_period <= chunk_size * 0.3:
        return False

    return start + last_period + 1


def functions_stop_on_value(functions: List[Callable], **kwargs):
    """iterate over a list of functions and return the first function that returns a value"""

    return next((fn(**kwargs) for fn in functions if fn(**kwargs)), None)


default_calc_end_fns = [
    calc_end_codeblock, calc_end_paragraph, calc_end_sentence
]


def chunk_text(
    text: str,  # text to chunk
    calc_end_fns: Union[
        List[Callable],
        None] = None,  # list of functions to calculate the end of a chunk
    chunk_size: int = 5000,
    debug_prn: bool = False,
) -> List[str]:

    calc_end_fns = calc_end_fns or default_calc_end_fns
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # handle code block
        chunk = text[start:end]

        end = (functions_stop_on_value(functions=calc_end_fns,
                                       chunk=chunk,
                                       chunk_size=chunk_size,
                                       start=start) or end)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = max(start + 1, end)

    if debug_prn:
        print(
            f"Chunked {len(text)} character text into {len(chunks)} chunks of chunk_size {chunk_size}"
        )
    return chunks
