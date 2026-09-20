"""The tools themselves. One tool is a question somebody asks.

Never a route: sixty routes turned into sixty tools is a model chaining six
calls to answer one question, and getting three of them wrong.

Three rules every tool here holds to:

- **Facts already worded.** « en retard de 12 jours », never `slippage_days`.
  A model handed a number writes the sentence itself, and writes it wrong.
- **What is unknown is said.** An absent field is a field a model fills in.
- **No identifier a human would not use**, beyond the ones `find_project`
  hands over for the other tools to consume.
"""
