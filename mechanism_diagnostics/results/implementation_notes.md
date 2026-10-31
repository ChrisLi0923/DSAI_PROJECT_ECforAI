# Analysis implementation notes

These notes concern only the new post-hoc diagnostic reader.

- The initial CPU attempt stopped when it expected every syntactic descendant path to have an explicit visit mask. Historical `repair/replay.py` stops descending once no rows reach a node, and historical `repair/search.py` explicitly assigns absent paths zero visits. The reader was corrected to use that same zero default. No candidate, policy, historical result or original algorithm was altered. The initial exception receipt remains under `results/attempts/`.
- Both complete runs used the same prewritten analysis specification and bootstrap seeds. Historical scores, parent choices and validation selections reproduced exactly. The corrected run completed all 15 ledger analyses and reproduced all final ordered populations/scores.
- Input availability is different from missing measurements: a nonexistent mask for an unvisited descendant is defined as zero by the historical code; missing discarded trial bodies and unqueried candidate validation scores remain unavailable and are never filled in.
- Normal G2 trial construction excludes the unchanged base. A separate audit of recorded trial hashes confirmed that all 57 pools containing the base hash were the recorded random-fallback cases; no unchanged base was offered in the remaining 2,765 pools.
- Final figures were viewed for readability. There were no model calls or new searches during development, checks, replay, plotting or interpretation.
