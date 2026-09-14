from pydantic import BaseModel
from typing import List


class ContractChangeOutput(BaseModel):
    sections_changed: List[str]
    topics_touched: List[str]
    summary_of_the_change: str