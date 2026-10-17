# Evidence Adds Up to a Fact

**Article:** [Quest for Entropy #19 — "Evidence Adds Up to a Fact"](https://questforentropy.com/p/evidence-adds-up) · also on [Substack](https://questforentropy.substack.com/p/evidence-adds-up)

Companion code for the episode. The article ships with it as `article.md`. The
bench, the mechanism room by room with every dial, is `bench/index.html`; the
meeting game, where the lines split into equal cells and two touches make the
square, is `meeting-game/index.html`. Open either in a browser, no server needed.

## Run it

Python 3.10+.

    pip install qiskit numpy
    python the_crowd_and_the_chain.py

That builds the witness circuits from standard gates on an exact statevector
simulator and prints every row the article's witness numbers rest on, in a few
seconds: direct witnesses multiply (a factor cos of the look per witness left out
of reach), a chain of retellings sticks at its first link, an undo recovers only
the witnesses it reaches, the reach averages, six wirings, two known negatives,
and the closed box decided inside before the observer's first link. Each row is
printed beside its closed form.

`python run_all.py` runs the same script; `expected_output/run_all.txt` is what a
correct run prints, to diff against. The numbers are exact, so they do not move
between runs.

## What is in here

| file | what it is |
|---|---|
| `the_crowd_and_the_chain.py` | the circuits, the rows, the closed forms |
| `bench/index.html` | the bench: the mechanism in eight rooms, every table, every dial |
| `meeting-game/index.html` | the meeting game: equal cells, two touches, the square |
| `run_all.py` | runs the script |
| `expected_output/run_all.txt` | what a correct run prints, to diff against |

## Scope

The circuits are standard quantum circuits, and quantum mechanics predicts every
number they print. What the episode adds is a picture: meetings, witnesses and
an agreement game, step by step. The article's Confession section says exactly
where that line falls.

## Licence

MIT.
