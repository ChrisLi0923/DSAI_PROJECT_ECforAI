# Retrieval pilot sampled error review

Illustrative, reproducibly sampled development examples; no internal causal claims.

## annotation_absent_from_top_k_but_answer_correct: obqa/validation/7-428

Tree rings can

A. indicate how often the tree needs pruning
B. tell you what year a tree was planted
C. tell you how tall a tree is
D. indicate the year the tree will die

Canonical gold=1; annotated fact (diagnostic only): the number of rings in a tree trunk can be used to estimate the age of the tree

Retrieved obqa-fact-bc723286b4170ff48c62, BM25=42.3159: a tree growing a tree-growth ring occurs once per year

Retrieved obqa-fact-35f18af8a567f4a14a1c, BM25=41.3178: if a tree is cut down then that tree will die

Retrieved obqa-fact-5fbeaf57af3fc55972cb, BM25=37.4061: the number of rings in a tree trunk can be used to estimate the age of the tree

original: raw='D', canonical=3, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=1

## annotation_absent_from_top_k_but_answer_correct: obqa/validation/9-106

Plants need light for

A. love
B. glucose
C. reading
D. driving

Canonical gold=1; annotated fact (diagnostic only): darkness has a negative impact on photosynthesis

Retrieved obqa-fact-c69d161ae5f9d116a8a9, BM25=9.2589: chlorophyll is used for absorbing light energy by plants

Retrieved obqa-fact-e2b15a744a8d89fdefe4, BM25=8.4360: a plant light is used for help plants by mimicking sunlight

Retrieved obqa-fact-0fbb70439f391c2e5fa3, BM25=7.4974: bad weather decreases visibility while driving

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=1

## annotation_absent_from_top_k_but_answer_correct: obqa/validation/7-1191

Layers of the earth include all but

A. mantle
B. center
C. crust
D. inner core

Canonical gold=1; annotated fact (diagnostic only): the crust is a layer of the Earth

Retrieved obqa-fact-5f07ee7a9bf414ee3e6a, BM25=17.2852: the mantle is located just below Earth 's crust

Retrieved obqa-fact-76ebc161242db1287103, BM25=13.1514: the crust is a layer of the Earth

Retrieved obqa-fact-cc76e8514500f680ad4e, BM25=13.1514: the mantle is a layer of the Earth

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=1

## annotation_absent_from_top_k_but_answer_correct: obqa/validation/1372

The next moon phase after a solar eclipse is

A. first quarter
B. full moon
C. third quarter
D. super moon

Canonical gold=0; annotated fact (diagnostic only): a solar eclipse could only happen during the new moon

Retrieved obqa-fact-d44637fccb283c746b30, BM25=45.4540: the first quarter phase of the moon occurs after the new moon

Retrieved obqa-fact-83b5d530aa96098335df, BM25=24.3822: a solar eclipse could only happen during the new moon

Retrieved obqa-fact-83289ab7600d0a0a43af, BM25=21.8556: the solar system contains the moon

original: raw='A', canonical=0, valid=True

R0: raw='A', canonical=0, valid=True

R1: raw='A', canonical=0, valid=True

R3: raw='A', canonical=0, valid=True

Ordered-triple canonical=0

## annotation_absent_from_top_k_but_answer_correct: obqa/validation/7-535

Viewing stars is made easier by

A. technology that uses electromagnetic induction
B. technology that collects electromagnetic radiation
C. technology that picks up sound in space
D. technology that transforms kinetic energy

Canonical gold=1; annotated fact (diagnostic only): a telescope is used for observing stars

Retrieved obqa-fact-c9bd16e1c8bfd6d2bd9f, BM25=14.8552: as an object moves , the kinetic energy of that object will increase

Retrieved obqa-fact-821b9d59794b070e4d1f, BM25=14.4178: a thermal conductor is made of materials that conduct thermal energy

Retrieved obqa-fact-ae178497e42c16ba2751, BM25=13.7369: when sound reaches the ear , that sound can be heard

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=1

## low_lexical_overlap_candidate_irrelevance: obqa/validation/7-1059

The Grand Canyon became so deep and large because

A. water sources are there
B. rivers are around it
C. water is really strong
D. rushing water eroded it

Canonical gold=3; annotated fact (diagnostic only): the Grand Canyon was formed by the Colorado River flowing over long periods of time

Retrieved obqa-fact-c728b6af0c3e47ca1361, BM25=16.9769: when a body of water receives more water than it can hold , a flood occurs

Retrieved obqa-fact-8ee4e5df03693576db93, BM25=16.7598: clouds are formed by water vapor rising and condensing

Retrieved obqa-fact-c4582b6b77d1aa155fb2, BM25=16.7077: beads of water are formed by water vapor condensing

original: raw='D', canonical=3, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=3

## low_lexical_overlap_candidate_irrelevance: obqa/validation/7-473

do scars come naturally?

A. they just appear
B. they are gifted
C. they are bought
D. they are earned

Canonical gold=3; annotated fact (diagnostic only): a scar is an acquired characteristic

Retrieved obqa-fact-900796d529264bedba97, BM25=33.2527: musical instruments make sound when they are played

Retrieved obqa-fact-aef5217f42c81754fbde, BM25=33.2527: sugar dissolves in water when they are combined

Retrieved obqa-fact-ab108fe8b485faddd201, BM25=22.1242: usually plants store the food they produce for future use

original: raw='D', canonical=3, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=3

## low_lexical_overlap_candidate_irrelevance: obqa/validation/8-198

if a person had one of these, they could live permanently under water

A. a very long nose
B. two hands and two legs
C. a very big mouth
D. a gill for extracting gases

Canonical gold=3; annotated fact (diagnostic only): gills are used for breathing water by aquatic animals

Retrieved obqa-fact-cedd0ac178f831782170, BM25=17.4348: a desert environment contains very little food

Retrieved obqa-fact-7ac105f23909aafe7be2, BM25=16.7059: fossil fuels forming occurs over a period of 300000000 years which is considered a very long time to a human

Retrieved obqa-fact-720a85d707429a0c7d22, BM25=15.2981: if two animals have the same food source then those two animals compete for food

original: raw='D', canonical=3, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=3

## low_lexical_overlap_candidate_irrelevance: obqa/validation/7-1139

To have a positive impact of the environment

A. use Styrofoam plates and bowls
B. use more paper towels
C. salvage plastic bottles instead of throwing them away
D. drive a car that guzzles gas

Canonical gold=2; annotated fact (diagnostic only): recycling has a positive impact on the environment

Retrieved obqa-fact-5473e97f044e306c1d04, BM25=17.8705: as the use of alternative fuels increases , the use of gasoline will decrease

Retrieved obqa-fact-964bf62386de17bc96b3, BM25=14.7362: landfills have a negative impact on the environment

Retrieved obqa-fact-bc1ff30b68b770ec9b40, BM25=14.4023: as the use of a resource decreases , the length of time that resource will be available increases

original: raw='C', canonical=2, valid=True

R0: raw='C', canonical=2, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=2

## low_lexical_overlap_candidate_irrelevance: obqa/validation/304

Draining the rain with a rain gutter onto bare ground through a spout will

A. make the ground underneath contain less soil
B. attract more dirt to where the water is falling
C. cause the ground to become very hard
D. draw up more water from underground

Canonical gold=0; annotated fact (diagnostic only): pouring water onto soil causes that soil to wash away

Retrieved obqa-fact-c5e99abcebc92a57372a, BM25=25.7891: precipitation is when hail fall from clouds to the ground

Retrieved obqa-fact-13c755166d465af85310, BM25=25.6453: an earthquake causes the ground to shake

Retrieved obqa-fact-a947c464eb2ae440e03e, BM25=24.6239: magma is found below the ground

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=0

## retrieval_rescues_reference: obqa/validation/7-57

Gas can fill any container it is given, and liquid

A. is standard weight and size
B. is the opposite of variable
C. only needs a few
D. uses what it needs

Canonical gold=3; annotated fact (diagnostic only): Matter in the liquid phase has definite volume

Retrieved obqa-fact-dd315e0f08630296d6e3, BM25=22.4088: matter with variable volume and shape assumes the shape and size of its entire container

Retrieved obqa-fact-1daed197a0b4ac58e653, BM25=15.9622: a candle is a source of light when it is burned

Retrieved obqa-fact-0539ec750a8c976c39b4, BM25=15.0089: as the size of a flower increases , the number of pollinators it will attract increases

original: raw='D', canonical=3, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=1

## retrieval_rescues_reference: obqa/validation/7-921

A body may find its temperature to be lowered after

A. water is heated up
B. fluid spreads from pores
C. the air becomes arid
D. the sky stays bright

Canonical gold=1; annotated fact (diagnostic only): sweat cools a body

Retrieved obqa-fact-47489f8721cfd1c7aa67, BM25=14.5867: precipitation is when water falls from the sky

Retrieved obqa-fact-22399de449bd8f4dca8c, BM25=14.5434: evaporation is when water is drawn back up into the air in the water cycle

Retrieved obqa-fact-656ee3ccac46415201dc, BM25=11.0595: the Earth rotating on its axis causes the sun to appear to move across the sky during the day

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=2

## retrieval_rescues_reference: obqa/validation/9-545

nest sitting is left up to the

A. daddy
B. the embryo's creator
C. strangers
D. male siblings

Canonical gold=1; annotated fact (diagnostic only): female birds sit in nests

Retrieved obqa-fact-e89dcfd66adad62a11f7, BM25=8.8206: a nest is made of branches

Retrieved obqa-fact-22399de449bd8f4dca8c, BM25=8.2656: evaporation is when water is drawn back up into the air in the water cycle

Retrieved obqa-fact-b2aac464ec74f406f689, BM25=7.9250: remora fish eat food by attaching themselves to sharks and eating the food left behind

original: raw='B', canonical=1, valid=True

R0: raw='A', canonical=0, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=0

## retrieval_rescues_reference: obqa/validation/239

Deer entered the city

A. to look for people
B. less food in the wilderness
C. because coyotes chased them
D. they have become confused

Canonical gold=1; annotated fact (diagnostic only): if a habitat can no longer support animals then those animals will move to another area

Retrieved obqa-fact-2fcaf880bac9f85515ca, BM25=13.6998: bacteria can cause people to become ill

Retrieved obqa-fact-ab108fe8b485faddd201, BM25=12.8368: usually plants store the food they produce for future use

Retrieved obqa-fact-4a63905a0fe05d7bd2b7, BM25=12.5126: medicine can cause people to have bad reactions

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=0

## retrieval_rescues_reference: obqa/validation/1472

Insects are eaten by

A. dogs
B. lizard-like amphibians
C. flies
D. cats

Canonical gold=1; annotated fact (diagnostic only): a salamander eats insects

Retrieved obqa-fact-83b3efca61e6db2222f0, BM25=8.2006: amphibians undergo metamorphosis

Retrieved obqa-fact-7dab7b97ce3f07bfd6cb, BM25=7.6716: amphibians hatch from eggs

Retrieved obqa-fact-d181ea4afcb517fd933b, BM25=7.6696: the smell of rotting meat attracts flies

original: raw='C', canonical=2, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='C', canonical=2, valid=True

Ordered-triple canonical=2

## retrieval_spoils_reference: obqa/validation/8-481

A pelican is hungry, so decides to try to catch some fish. In order to do this, the pelican will

A. use the back of its head
B. use the bottom of its stomach
C. use the front of its face
D. use the back of its tail

Canonical gold=2; annotated fact (diagnostic only): a beak is used for catching prey by some birds

Retrieved obqa-fact-5473e97f044e306c1d04, BM25=41.9750: as the use of alternative fuels increases , the use of gasoline will decrease

Retrieved obqa-fact-1372d2f21494b8dd6e7b, BM25=32.6147: as the use of a crop increases , the amount of crops planted will increase

Retrieved obqa-fact-bc1ff30b68b770ec9b40, BM25=29.4790: as the use of a resource decreases , the length of time that resource will be available increases

original: raw='C', canonical=2, valid=True

R0: raw='C', canonical=2, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=2

## retrieval_spoils_reference: obqa/validation/6

What is the ultimate source of greeting cards?

A. deserts
B. waterfalls
C. forests
D. canyons

Canonical gold=2; annotated fact (diagnostic only): creating paper requires cutting down trees

Retrieved obqa-fact-61d6b60828317bbd335b, BM25=7.5253: some rabbits live in forests

Retrieved obqa-fact-8f4ef45c9e6b680b3447, BM25=7.5253: some birds live in forests

Retrieved obqa-fact-a5741d2f8b6a2bb3863d, BM25=7.5253: some crickets live in forests

original: raw='C', canonical=2, valid=True

R0: raw='C', canonical=2, valid=True

R1: raw='A', canonical=0, valid=True

R3: raw='C', canonical=2, valid=True

Ordered-triple canonical=2

## retrieval_spoils_reference: obqa/validation/7-556

Substances may be combined by the pouring of one into another, for example when

A. filling up a tub
B. putting a lemon in water
C. adding grenadine to soda
D. putting food in a bowl

Canonical gold=2; annotated fact (diagnostic only): An example of combining two substances is pouring one substance into the other substance

Retrieved obqa-fact-7338d33f03e245337280, BM25=20.0218: An example of combining two substances is pouring one substance into the other substance

Retrieved obqa-fact-aef5217f42c81754fbde, BM25=16.5126: sugar dissolves in water when they are combined

Retrieved obqa-fact-22399de449bd8f4dca8c, BM25=15.9272: evaporation is when water is drawn back up into the air in the water cycle

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=2

## retrieval_spoils_reference: obqa/validation/1565

The epidermis is part of

A. is the largest organ and also the body's first defense against germs
B. is used the second largest organ and used for breathing by humans
C. soaks in toxins in the air
D. repels sunlight and UV rays

Canonical gold=0; annotated fact (diagnostic only): skin is used for protecting the body from harmful substances

Retrieved obqa-fact-4124a498fbe0b68bc0df, BM25=41.9535: the skin is the largest organ in the human body

Retrieved obqa-fact-d01873a25f78ae9460d6, BM25=25.5252: slope is a measure of the difference in elevation between one part of the land and another part of the land

Retrieved obqa-fact-7b66a1defe53b808c36a, BM25=19.7272: a stinger is used for defense by a wasp

original: raw='A', canonical=0, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=0

## retrieval_spoils_reference: obqa/validation/933

A source of sugar in an ecosystem is

A. air
B. soil
C. tree
D. bird

Canonical gold=2; annotated fact (diagnostic only): a producer is a source of sugar in an ecosystem

Retrieved obqa-fact-c1f694e745f6a7f24614, BM25=19.0668: a producer is a source of sugar in an ecosystem

Retrieved obqa-fact-6ce34dcd1fd9e2c09bd8, BM25=16.8217: a tree is a source of food for animals in an ecosystem

Retrieved obqa-fact-a83ae62edf7282a6ba89, BM25=16.8217: a tree is a source of food for birds in an ecosystem

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=2

## annotated_fact_retrieved_but_answer_wrong: obqa/validation/7-131

When vapor condenses overnight it often ends up on

A. bees
B. clothing
C. rosebuds
D. people

Canonical gold=2; annotated fact (diagnostic only): dew is formed when water vapor condenses over night

Retrieved obqa-fact-8a4badf31f33c77720e4, BM25=14.1410: dew is formed when water vapor condenses over night

Retrieved obqa-fact-15e0b3f9a3e35ef5b354, BM25=9.7626: landslides often occur on mountains

Retrieved obqa-fact-80752fb5145fda4f17cb, BM25=9.0482: bees eat pollen

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='B', canonical=1, valid=True

R3: raw='B', canonical=1, valid=True

Ordered-triple canonical=1

## annotated_fact_retrieved_but_answer_wrong: obqa/validation/8-64

The insect's cocoon being created occurs during the

A. adult stage in a life cycle
B. egg formation in a life cycle
C. stage when wings first start to form
D. final stage in a life cycle

Canonical gold=2; annotated fact (diagnostic only): the cocoons being created occurs during the the pupa stage in a life cycle

Retrieved obqa-fact-63bceb67de0f38416332, BM25=61.0036: the cocoons being created occurs during the the pupa stage in a life cycle

Retrieved obqa-fact-2765b517454eef067df1, BM25=54.5555: adulthood is a stage in the life cycle process

Retrieved obqa-fact-ee30c48b1599fcc2ebc7, BM25=54.5555: reproduction is a stage in the life cycle process

original: raw='D', canonical=3, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=3

## annotated_fact_retrieved_but_answer_wrong: obqa/validation/1706

We looked at the arrow on the compass and then turned around and walked in the opposite direction.  We were walking

A. south
B. east
C. west
D. north

Canonical gold=0; annotated fact (diagnostic only): the floating arrow on a compass always points towards the north

Retrieved obqa-fact-c374cb22db7ab4d78b67, BM25=22.9447: the floating arrow on a compass always points towards the north

Retrieved obqa-fact-93db901faa0d3dec5658, BM25=15.4724: the sun sets in the west

Retrieved obqa-fact-a1d202b042326c3b2914, BM25=13.8117: a compass is a kind of tool for determining direction by pointing north

original: raw='D', canonical=3, valid=True

R0: raw='D', canonical=3, valid=True

R1: raw='D', canonical=3, valid=True

R3: raw='D', canonical=3, valid=True

Ordered-triple canonical=0

## annotated_fact_retrieved_but_answer_wrong: obqa/validation/1470

The moon is what to the earth?

A. the largest star in the sky
B. the brightest celestial object
C. the closest body in in space
D. the biggest thing in the universe

Canonical gold=2; annotated fact (diagnostic only): the moon is the celestial object that is closest to the Earth

Retrieved obqa-fact-d722ab065073862002f8, BM25=35.8176: the moon is the celestial object that is closest to the Earth

Retrieved obqa-fact-4124a498fbe0b68bc0df, BM25=32.3651: the skin is the largest organ in the human body

Retrieved obqa-fact-4edf07c838059e66cbcc, BM25=29.2025: the North Star does not move in the sky in the Northern Hemisphere each night

original: raw='B', canonical=1, valid=True

R0: raw='B', canonical=1, valid=True

R1: raw='A', canonical=0, valid=True

R3: raw='C', canonical=2, valid=True

Ordered-triple canonical=1

## annotated_fact_retrieved_but_answer_wrong: obqa/validation/452

When water freezes, that water

A. heats up by at least 10 degrees
B. undergoes a change opposite to compressor
C. takes up less space
D. breaks into little pieces

Canonical gold=1; annotated fact (diagnostic only): when water freezes , that water expands

Retrieved obqa-fact-aeb7f41e4a95839842e6, BM25=20.7375: when water freezes , that water expands

Retrieved obqa-fact-22399de449bd8f4dca8c, BM25=19.2501: evaporation is when water is drawn back up into the air in the water cycle

Retrieved obqa-fact-3bb973d593d6ed0b74d9, BM25=15.2913: An example of evaporation is a body of water drying up by absorbing heat energy

original: raw='C', canonical=2, valid=True

R0: raw='C', canonical=2, valid=True

R1: raw='C', canonical=2, valid=True

R3: raw='C', canonical=2, valid=True

Ordered-triple canonical=2