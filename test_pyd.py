from pydantic import BaseModel
from typing import Any, Optional

class Ev(BaseModel):
    x: int

class State(BaseModel):
    ledger: Optional[Any] = None

ev = Ev(x=1)
s = State(ledger=ev)
print(type(s.ledger))
if isinstance(s.ledger, dict):
    print("It's a dict!")
else:
    s.ledger.x = 2
    print(ev.x, s.ledger.x)
