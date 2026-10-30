# Exploratory error-review examples

Generated rationales are observations, not established internal reasoning or causes.

## all_tested_responses_wrong: obqa/train/11-748

A lizard has young

A. in shells
B. frozen
C. alive
D. in corpses

Canonical correct identity: 0 (A).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=2, valid=True:

> A

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: C. alive
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> Lizards lay eggs or give live birth; eggs are not in shells. FINAL: C

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> The relevant principle is viviparity (live birth) in lizards. FINAL: C

Supporting fact: reptiles lay eggs

Unrelated fact: a disperser disperses

Evidence responses: {"no_evidence": "C", "supporting": "C", "unrelated": "C"}

## all_tested_responses_wrong: obqa/train/9-928

Freezing point refers to:

A. the temperature below which gas turns to liquid
B. the temperature above which liquid stops being liquid
C. the temperature below which solid turns to liquid
D. the temperature below which liquid stops being liquid

Canonical correct identity: 3 (D).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=2, valid=True:

> A

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: the temperature below which solid turns to liquid
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> Freezing point is the temperature below which a substance changes from a solid to a liquid state. FINAL: C

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> Scientific principle: Freezing point is the temperature at which a substance changes from a solid to a liquid state. FINAL: C

Supporting fact: freezing point means temperature below which a liquid freezes

Unrelated fact: usually plants die or become dormant during the winter

Evidence responses: {"no_evidence": "C", "supporting": "C", "unrelated": "C"}

## all_tested_responses_wrong: obqa/train/14-88

Where does August take place during the winter?

A. China
B. Zimbabwe
C. Canada
D. Iceland

Canonical correct identity: 1 (B).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=3, valid=True:

> B

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: C. Canada
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> August in China, Zimbabwe, and Canada can occur year-round; only Iceland experiences distinct seasons. FINAL: C

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> The principle is climate and seasonal changes. Canada experiences cold winters. FINAL: C

## all_tested_responses_wrong: obqa/train/10-984

When warm winds blow across an area from off of the sea,

A. snow is gone
B. beaches are littered
C. storms are imminent
D. clouds are scarce

Canonical correct identity: 2 (C).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=3, valid=True:

> C

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=3, valid=True:

> B

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> SELECTED_TEXT: D. clouds are scarce
> FINAL: D

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=None, valid=False:

> Warm sea breezes typically result in clear skies and less cloud cover. D

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> The relevant principle is advection: the transport of heat and moisture by wind. D. FINAL: D

Supporting fact: a warm front causes cloudy and rainy weather

Unrelated fact: large trees block sunlight from reaching the ground

Evidence responses: {"no_evidence": "D", "supporting": "D", "unrelated": "D"}

## all_tested_responses_wrong: obqa/train/9-836

which of these can be considered a stage in the water cycle?

A. all of these
B. the combination of nails and hammers
C. the presence of H20
D. the combination of chlorine and gas

Canonical correct identity: 2 (C).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=0, valid=True:

> D

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> SELECTED_TEXT: A. all of these
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A. all of these FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> The water cycle involves evaporation, condensation, precipitation, and collection; none of the given options represent stages of this cycle. FINAL: A

## all_tested_responses_wrong: obqa/train/8-311

Thirteen times a year, roughly, the moon

A. crashes into the Earth
B. is orbited by the Earth
C. lights up the Earth
D. completely rotates the Earth

Canonical correct identity: 3 (D).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=1, valid=True:

> A

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=1, valid=True:

> D

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> SELECTED_TEXT: B. is orbited by the Earth
> FINAL: B

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> Option A is incorrect as the moon does not crash into Earth. Option B accurately describes the moon's orbit around Earth. Option C is true but less specific to the frequency mentioned. Option D is false since the Earth does not rotate around itself. FINAL: B

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> Scientific principle: Phases of the Moon occur due to its orbit around the Earth and its rotation. B. is orbited by the Earth FINAL: B

## correct_alternative_but_reference_wrong: obqa/train/11-218

Which of the following would you use to most efficiently transport heat?

A. empty water bottle
B. cotton T-Shirt
C. baseball cap
D. empty soda can

Canonical correct identity: 3 (D).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=0, valid=True:

> D

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> SELECTED_TEXT: empty water bottle
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A. empty water bottle conducts heat better than insulators like cotton or a cap. FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> The relevant principle is thermal conductivity: materials that conduct heat well are good for heat transfer. D. FINAL: D

Supporting fact: a thermal energy conductor transfers heat from hotter objects to cooler objects

Unrelated fact: if an object is kicked then force is exerted on that object

Evidence responses: {"no_evidence": "A", "supporting": "A", "unrelated": "D"}

## correct_alternative_but_reference_wrong: obqa/train/12-641

Amphibians undergo changes in structure of being in that

A. salamanders can regrow their tails
B. salamanders can lose their tails
C. frogs can breathe air and water
D. they begin as a different looking being

Canonical correct identity: 3 (D).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=0, valid=True:

> D

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=3, valid=True:

> B

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> SELECTED_TEXT: D. they begin as a different looking being
> FINAL: D

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A. salamanders can regrow their tails FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> Developmental plasticity allows amphibians to change form; salamanders can regenerate lost tail segments. FINAL: D

## correct_alternative_but_reference_wrong: obqa/train/11-625

A guy is trying to choose a spot to build his house. He chooses a place that will cause the least environmental change in an area, so he builds in

A. a town
B. a jungle
C. a desert
D. a forest

Canonical correct identity: 0 (A).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> SELECTED_TEXT: a town
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A town already has significant environmental changes; jungles, deserts, and forests are natural habitats needing minimal disturbance. FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> The principle is habitat conservation and minimal disruption. D. FINAL: D

## correct_alternative_but_reference_wrong: obqa/train/10-767

December is during the summer in the southern what?

A. states
B. division
C. cities
D. counties

Canonical correct identity: 1 (B).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=1, valid=True:

> A

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=None, valid=False:

> SELECTED_TEXT: December is during the summer in the southern what?
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> December is not considered summer anywhere; it's winter in both hemispheres. FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> The seasons are opposite in the northern and southern hemispheres; December is summer in the southern hemisphere. FINAL: A

## correct_alternative_but_reference_wrong: obqa/train/10-393

If it's been twelve weeks since you put on shorts, and you notice today the hours of light and dark are just about equal, how long will it be until Winter?

A. just over a year
B. around thirteen weeks or so
C. when G.R.R. Martin says it's here
D. when the groundhog sees its shadow

Canonical correct identity: 1 (B).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=1, valid=True:

> A

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: C. when G.R.R. Martin says it's here
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> Equal day and night occur around winter solstice, coming in about 3 months from now; 12 weeks is too short. FINAL: B

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> The principle is Daylight Saving Time (DST): changing clocks by one hour forward in spring and back in autumn. FINAL: B

## correct_alternative_but_reference_wrong: obqa/train/10-894

Steve's ears alerted him to something. It was

A. the taste of his lunch
B. waves in the air
C. the light streaming through the window
D. the feeling of his hair on his neck

Canonical correct identity: 1 (B).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=3, valid=True:

> C

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=3, valid=True:

> B

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> SELECTED_TEXT: B. waves in the air
> FINAL: B

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> Ears detect sound, not taste, airwaves, or hair movement; they hear. FINAL: B

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> The scientific principle is: Eardrum vibrates in response to sound waves (Physics).
> FINAL: B

Supporting fact: matter vibrating can cause sound

Unrelated fact: plant cells can perform photosynthesis

Evidence responses: {"no_evidence": "B", "supporting": "B", "unrelated": "B"}

## supporting_fact_rescues: obqa/train/11-703

Which of the following would be considered nonliving?

A. a hair still on your head
B. a rabbit hopping along
C. a fallen palm leaf
D. a human jogging down a track

Canonical correct identity: 2 (C).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=2, valid=True:

> A

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: a fallen palm leaf
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> A hair is part of a living organism; the others are clearly nonliving. FINAL: D

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> Nonliving entities do not exhibit life processes; they are inanimate objects. D. FINAL: D

Supporting fact: if a leaf falls off of a tree then that leaf is dead

Unrelated fact: the breaking down of food into simple substances occurs in the digestive system

Evidence responses: {"no_evidence": "D", "supporting": "C", "unrelated": "A"}

## supporting_fact_rescues: obqa/train/9-295

A child will only grow if they are provided with

A. a bed
B. education
C. inspiration
D. energy

Canonical correct identity: 3 (D).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=3, valid=True:

> C

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=1, valid=True:

> D

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> SELECTED_TEXT: a bed
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> Growth requires nourishment, not just rest (bed). Education fuels cognitive development (B). Inspiration motivates but doesn't directly support physical growth. Energy is essential but alone isn't sufficient for growth. FINAL: B

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> The scientific principle is growth requires nourishment and conditions for development. D. energy FINAL: D

Supporting fact: an organism requires energy for growth

Unrelated fact: plants are a source of fibers

Evidence responses: {"no_evidence": "B", "supporting": "D", "unrelated": "B"}

## supporting_fact_rescues: obqa/train/7-499

Roads need repaved in spring because

A. they are cold
B. road need it
C. they are lumpy
D. ice ruins them

Canonical correct identity: 3 (D).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=2, valid=True:

> A

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: C. they are lumpy
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> Spring thaw causes roads to become soft and weak, leading to potholes; ice can damage them. FINAL: D

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> The relevant principle is seasonal changes affecting infrastructure (C). FINAL: C

Supporting fact: cycles of freezing and thawing water cause ice wedging

Unrelated fact: transpiration usually happens in the leaves of a plant

Evidence responses: {"no_evidence": "C", "supporting": "D", "unrelated": "D"}

## supporting_fact_rescues: obqa/train/13-520

Slurping down your urine shows you're

A. bed-wetting
B. recycling
C. menstruating
D. preserving wetlands

Canonical correct identity: 1 (B).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=0, valid=True:

> D

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> SELECTED_TEXT: D. preserving wetlands
> FINAL: D

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> Slurping down urine is an unusual behavior; it doesn't relate to bed-wetting, recycling, or preserving wetlands. FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> The scientific principle is related to human physiological functions and waste management. FINAL: A

Supporting fact: An example of conservation is avoiding waste

Unrelated fact: a thermometer is used to measure temperature

Evidence responses: {"no_evidence": "A", "supporting": "B", "unrelated": "A"}

## supporting_fact_rescues: obqa/train/12-758

Which of the following would occur in nature?

A. an osprey catches a fish with claws
B. a fish catches a fish with its claws
C. a dog catches a fish with its claws
D. a worm catches a fish with its claws

Canonical correct identity: 0 (A).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=0, valid=True:

> D

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> SELECTED_TEXT: a fish catches a fish with its claws
> FINAL: B

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=None, valid=False:

> Only birds have claws; fish do not. Final: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> The principle is: Predation and feeding behaviors (A) FINAL: A

Supporting fact: claws are used to catch prey by some predators

Unrelated fact: usually plants die or become dormant during the winter

Evidence responses: {"no_evidence": "B", "supporting": "A", "unrelated": "B"}

## supporting_fact_rescues: obqa/train/14-1041

Which animal interacts most with a peony?

A. human
B. bee
C. elephant
D. worm

Canonical correct identity: 1 (B).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=1, valid=True:

> A

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=1, valid=True:

> D

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> SELECTED_TEXT: A. human
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> Peonies attract bees for pollination, humans for enjoyment, elephants for their size, but worms do not interact significantly with peonies. FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> The scientific principle is pollination by animals. B. FINAL: B

Supporting fact: A bee is a pollinating animal

Unrelated fact: a plane travels through the atmosphere

Evidence responses: {"no_evidence": "A", "supporting": "B", "unrelated": "A"}

## new_strategy_spoils_reference: obqa/train/10-52

A source of heat could be

A. an ice cube
B. a fan
C. holding hands
D. a snowflake

Canonical correct identity: 2 (C).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=2, valid=True:

> A

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> SELECTED_TEXT: an ice cube
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> Ice cube melts, releasing heat; fan blows air, no heat change; holding hands transfers thermal energy; snowflake is cold, releases heat upon melting. FINAL: D

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> Heat is transferred from a warmer object to a cooler one; ice cubes melt when exposed to warmth. FINAL: D

## new_strategy_spoils_reference: obqa/train/7-836

Bats hunt through echolocation because

A. bats can only hear echoes
B. echoes are a form of sound
C. their chirps are sent back after bouncing
D. they enjoy listening to echoes

Canonical correct identity: 2 (C).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=2, valid=True:

> A

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: C. their chirps are sent back after bouncing
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> Echolocation allows bats to navigate and find prey using reflected sound; D is incorrect as enjoying echoes isn't a function. FINAL: D

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> Echolocation is used by bats to navigate and find prey by emitting high-pitched sounds and interpreting the echoes: FINAL: C

## new_strategy_spoils_reference: obqa/train/11-9

Which of these is a side effect of vegetable farming?

A. clowns
B. happy dogs
C. fertilizer sickness
D. cats

Canonical correct identity: 2 (C).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> C

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=2, valid=True:

> B

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=2, valid=True:

> A

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> SELECTED_TEXT: C. fertilizer sickness
> FINAL: C

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> None of the given options are actual side effects of vegetable farming. FINAL: D

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=2, valid=True:

> The relevant principle is crop rotation and soil health (soil fertility). C. FINAL: C

## new_strategy_spoils_reference: obqa/train/10-655

A species' habitat is those places where it can find food, shelter, protection and

A. predators to escape
B. rivers to cross
C. mountains to climb
D. mates for reproduction

Canonical correct identity: 3 (D).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> D

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=3, valid=True:

> C

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=3, valid=True:

> B

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=None, valid=False:

> SELECTED_TEXT: A. predators to escape
> FINAL: D

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> Correct habitat features include food, shelter, protection; predators are potential threats, not sought. FINAL: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=3, valid=True:

> The scientific principle is habitat definition: A species' habitat includes areas providing essential resources like food, shelter, and protection. FINAL: D

## new_strategy_spoils_reference: obqa/train/10-66

It becomes cold enough for heavy clothing in December in the northern hemisphere because

A. our planet's axis is tilted
B. Mercury's axis is tilted
C. the gravitational pull of Pluto on the southern hemisphere
D. lyrics about winter by popular musicians always mention bundling up

Canonical correct identity: 0 (A).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> A

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=1, valid=True:

> A

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=0, valid=True:

> C

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> SELECTED_TEXT: A. our planet's axis is tilted
> FINAL: A

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=None, valid=False:

> Final: A

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=0, valid=True:

> The Earth's axial tilt causes seasonal variations; December in the northern hemisphere tilts away from the Sun, leading to colder temperatures. FINAL: A

## new_strategy_spoils_reference: obqa/train/11-478

A plane takes off from the ground, lights blazing, and flies into the sky. As the plane ascends and travels to its destination,

A. the lights are brighter
B. the lights appear duller
C. the lights are closer
D. the lights are bigger

Canonical correct identity: 1 (B).

**original**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**inline**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**bullets**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> B

**rotate1**, mapping {'A': 1, 'B': 2, 'C': 3, 'D': 0}, canonical=3, valid=True:

> C

**rotate2**, mapping {'A': 2, 'B': 3, 'C': 0, 'D': 1}, canonical=1, valid=True:

> D

**content**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> SELECTED_TEXT: B. the lights appear duller
> FINAL: B

**elimination**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=1, valid=True:

> As the plane ascends, its distance from the observer increases, making the lights appear smaller and less bright. FINAL: B

**principle**, mapping {'A': 0, 'B': 1, 'C': 2, 'D': 3}, canonical=None, valid=False:

> Optical illusion; perspective changes as altitude increases. BFINAL: B