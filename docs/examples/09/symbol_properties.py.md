# Symbol Properties

Source file: `symbol_properties.py`

```python
from __future__ import annotations

import asyncio

from abb_rws_client_python_rw6 import load_env
from abb_rws_client_python_rw6.core.client import RWSClient
from abb_rws_client_python_rw6.core.logger import configure_logging
from abb_rws_client_python_rw6.highlevel.symbol import (
    get_array_length,
    get_symbol_properties,
)


async def main() -> None:
    """Run a real-controller validation of RAPID symbol properties.

    Route: ``GET /rw/rapid/symbol/properties/{symbolurl}``

    ABB constraints:
        - The RAPID module ``SymbolPropertiesTest`` must be loaded.
        - Reads do not require mastership.
        - The endpoint is not supported in bootserver mode.

    Args:
        None.

    Returns:
        None.

    Raises:
        RWSAuthenticationError: If authentication fails.
        RWSNotFoundError: If a symbol does not exist.
        RWSHTTPError: On any other HTTP error.
        ValueError: If ABB's response cannot be parsed.

    Example:
        ```powershell
        pixi run -e examples python examples/09/symbol_properties.py
        ```
    """
    configure_logging("INFO")
    load_env()

    scalar_symbolurl = "RAPID/T_ROB1/SymbolPropertiesTest/ScalarValue"
    array_symbolurl = "RAPID/T_ROB1/SymbolPropertiesTest/Array1D"

    async with RWSClient() as client:
        print(f"[main] Connected to {client.host}:{client.port}")

        scalar_props = await get_symbol_properties(
            client,
            symbolurl=scalar_symbolurl,
        )
        print("[scalar]", scalar_props)

        array_props = await get_symbol_properties(
            client,
            symbolurl=array_symbolurl,
        )
        print("[array]", array_props)

        length = await get_array_length(
            client,
            symbolurl=array_symbolurl,
        )
        print(f"[array] length = {length}")


if __name__ == "__main__":
    asyncio.run(main())
```
