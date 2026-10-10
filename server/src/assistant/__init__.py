"""The assistant: a fourth way in, beside the routers, the tools and the clock.

The routers answer a request, the MCP server a terminal client, the clock a
time of day. This answers a question typed in the ⌘J panel, by handing it to
a model that reads the tools on behalf of whoever asked.

**It is a client of the application, not part of a module.** The model, not a
use case, decides which tools to read and in what order, and every tool
reaches a use case. Kept inside a use case, that loop would be a use case
calling others — the one thing the modules may never do. Out here it is what
the MCP server already is: a way in that orchestrates, held by the same two
`import-linter` contracts — nothing imports it but the entry point, and it
names no repository of its own.

The module `assistant` keeps what is business: the conversation and its five
exchanges, the exchanges kept, the verdicts. This package keeps the model,
the prompt, the shelf of tools, and the one route that asks.
"""
