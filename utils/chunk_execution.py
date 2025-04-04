# %% ../../nbs/chunk_execution.ipynb 2
import asyncio
from typing import List, Coroutine, Any


async def gather_with_concurrency(
    *coros: List[Coroutine[Any, Any, Any]],  # list of coroutines to await
    n=60,  # number of open coroutines
):
  """processes a list of coroutines in parallel"""

  semaphore = asyncio.Semaphore(n)

  async def sem_coro(coro):
    async with semaphore:
      return await coro

  return await asyncio.gather(*(sem_coro(c) for c in coros))
