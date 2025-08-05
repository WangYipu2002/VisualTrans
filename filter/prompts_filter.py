BOOKEND_PROMPT = """
You are given a **pair of images** showing the beginning and end of a manipulation task involving books being placed into or removed from a bookend.
Your goal is to determine whether the **books** are **sufficiently visible and unobstructed in both images**, such that their identity, structure, and placement state can be clearly observed.
You should **only focus on the books involved in the manipulation**, and **ignore any background objects**.

## Visibility Criteria:

A book is considered sufficiently visible if:
- It is fully visible, or partially blocked (e.g., touched by fingers) but still clearly identifiable.
- It is **not acceptable** if it is heavily obstructed by the hand or outside the camera view, making it difficult to recognize or understand its identity or manipulation state.

## Instructions:
1. In the **Thought** section, first provide a brief caption that describes the overall arrangement and appearance of all visible books in both images.  
   Then, carefully examine each identifiable book one by one. For each book, describe whether it is clearly visible or obstructed in both images, according to the visibility criteria.
2. Next, directly answer the question:  
**Are all the books sufficiently visible in both images?**

## Answer Format:

#Thought:  
[Your reasoning and observations here — visibility description of each identifiable book in both images]

#Final Answer:  
Yes / No  ← (Only output one word: Yes or No)

#Reason:  
[A short justification — e.g., "All the books are clearly visible in both images", or "The hand covers the red book in the first image, making it unrecognizable"]
""".strip()


FOOD_PROMPT = """
You are given a **pair of images** showing the beginning and end of a manipulation task involving one or more food items.

The task involves placing food from a basket onto a plate, or picking food from a plate and putting it into a basket.

Your goal is to determine whether **all food items on the plate** are **sufficiently visible and unobstructed in both images**, such that their identity, structure, and manipulation state can be clearly observed.

You should **only focus on the food placed on the plate**.  
Ignore any food remaining in the basket, in containers, or elsewhere in the background — they are not part of the evaluation.

## Visibility Criteria:

A food item on the plate is considered sufficiently visible if:
- It is fully visible, or partially blocked (e.g., touched by fingers) but still clearly identifiable.
- It is **not acceptable** if it is heavily obstructed by the hand or not visible in the camera view, making it difficult to recognize or understand its state.

## Instructions:
1. In the **Thought** section, first provide a brief caption that describes the overall arrangement and appearance of the food items on the plate in both images.  
   Then, carefully examine each identifiable food item one by one. For each item, describe whether it is clearly visible or obstructed in both images, according to the visibility criteria.
2. Then, directly answer the question:  
**Are all food items on the plate sufficiently visible in both images?**

## Answer Format:

#Thought:  
[Your reasoning and observations here — food descriptions + visibility status in both images]

#Final Answer:  
Yes / No

#Reason:  
[A short justification — e.g., "All food items are clearly visible in both images", or "One food item is blocked in the second image"]
""".strip()

BLOCK_PROMPT = """
You are given a **pair of images** showing the beginning and end of a block stacking task.

Your goal is to determine whether the **blocks** are **sufficiently visible and unobstructed in both images**, such that their shape, orientation, and placement state can be clearly observed.

You should **only focus on the blocks**, and **ignore any background objects**.

## Visibility Criteria:

A block is considered sufficiently visible if:
- It is fully visible, or partially blocked (e.g., touched by fingers) but still clearly identifiable in terms of shape and placement.
- It is **not acceptable** if it is heavily obstructed by the hand, partially outside the camera frame, or covered in a way that makes it difficult to recognize or understand its manipulation process.

## Instructions:
1. In the **Thought** section:
   - First provide a brief caption that describes the overall arrangement and appearance of the blocks in both images.  
   - Then carefully examine each identifiable block one by one. For each block, describe whether it is clearly visible or obstructed in both images, according to the visibility criteria.
   - In the **initial scattered state**, ensure that the **leftmost and rightmost blocks** are clearly visible and unobstructed, and that all other scattered blocks are also clearly identifiable.
   - In the **final stacked or assembled state**, ensure that every block visible in the image has a clearly visible shape and position.
   - If any block appears in the final stacked image but is not visible (or is heavily occluded) in the initial scattered image, **this should be noted as a failure in visibility consistency**.
2. Then, directly answer the question:  
**Are all blocks sufficiently visible in both images?**


## Answer Format:

#Thought:  
[Your reasoning and observations here — block descriptions + visibility status in both images]

#Final Answer:  
Yes / No

#Reason:  
[A short justification — e.g., "Leftmost scattered block is obscured", or "All blocks are clearly visible"]
""".strip()


BUILD_STACK_PROMPT = """
You are given a **pair of images** showing the beginning and end of a block stacking task.

Your task is to determine whether all **target blocks** are sufficiently visible and unobstructed in both images, so their shape, placement, and manipulation state can be clearly understood.

⚠️ Only focus on the blocks. Ignore any background or non-block objects (e.g., table, fingers, environment).

---

## Target Blocks:
The full set of 8 blocks is listed below. Your first priority is to check whether **all of them are clearly visible** in the **initial scattered image**.

- 2 blue blocks  
- 2 green blocks  
- 1 lime green block  
- 1 purple block  
- 1 yellow block  
- 1 white block

---

## Visibility Criteria:

A block is considered **sufficiently visible** if:
- It is **fully visible**, or only **lightly touched or partially overlapped by a hand** but still easily identifiable.
- It is **not acceptable** if:
  - It is **heavily covered** by the hand.
  - It is **partially outside the camera frame**.
  - It is **covered enough** that its shape, color, or placement are unclear.
  - It cannot be matched confidently between the initial and final image.

---

## Instructions:

1. In the **#Thought** section:
   - Provide a **brief caption** summarizing the block layout in both images.
   - Carefully go through the **8 expected blocks**, and for each block:
     - Determine whether it is **present and clearly visible** in the **initial scattered state**.
     - Then determine whether it is **clearly visible** in the **final stacked state**.
   - Pay special attention to:
     - The **leftmost and rightmost** blocks in the initial image — they must be fully or clearly visible.
     - Whether any block in the final stack is **not seen or unclear** in the initial image — this indicates a **failure in visibility consistency**.

2. Then, directly answer:  
**Are all 8 blocks sufficiently visible in both images?**

---

## Answer Format:

#Thought:  
[Reasoning — visibility check of each block in initial and final image, including any occlusions or absences.]

#Final Answer:  
Yes / No

#Reason:  
[A short justification — e.g., "Lime green block is completely hidden in initial image", or "All 8 blocks are clearly visible and unobstructed"]
""".strip()


BOWL_STACKING_PROMPT = """
You are given a **pair of images** showing the beginning and end of a manipulation task involving bowls being stacked or unstacked.

Your goal is to determine whether the **bowls** are **sufficiently visible and unobstructed in both images**, such that their shape, orientation, and placement state can be clearly observed.

You should **only focus on the bowls**, and **ignore any background objects**.

## Visibility Criteria:

The manipulated bowl is considered sufficiently visible if:
- It is fully visible, or partially blocked (e.g., touched by fingers) but still clearly identifiable.
- It is **not acceptable** if it is heavily obstructed by the hand or outside the camera view, making it difficult to recognize or understand its identity or manipulation state.

## Instructions:
1. In the **Thought** section, first provide a brief caption that describes the overall arrangement and appearance of the bowls in both images.  
   Then, carefully examine each identifiable bowl one by one. For each bowl, describe whether it is clearly visible or obstructed in both images, according to the visibility criteria.
2. Then, directly answer the question:  
**Is the manipulated bowl sufficiently visible in both images?**

## Answer Format:

#Thought:  
[Your reasoning and observations here — visibility description of each identifiable bowl in both images]

#Final Answer:  
Yes / No

#Reason:  
[A short justification — e.g., "All bowls are clearly visible in both images", or "Only the orange bowl is visible in the first image"]
""".strip()

PLATE_STACKING_PROMPT = """
You are given a **pair of images** showing the beginning and end of a manipulation task involving plates being stacked or unstacked.

Your goal is to determine whether the **plates** are **sufficiently visible and unobstructed in both images**, such that their size, shape, and stacking state can be clearly observed.

You should **only focus on the plates**, and **ignore any background objects**.

## Visibility Criteria:

The manipulated plate is considered sufficiently visible if:
- It is fully visible, or partially blocked (e.g., touched by fingers) but still clearly identifiable.
- It is **not acceptable** if it is heavily obstructed by the hand or outside the camera view, making it difficult to recognize or understand its identity or manipulation state.

## Instructions:
1. In the **Thought** section, first provide a brief caption that describes the overall arrangement and appearance of the plates in both images.  
   Then, carefully examine each identifiable plate one by one. For each plate, describe whether it is clearly visible or obstructed in both images, according to the visibility criteria.
2. Then, directly answer the question:  
**Is the manipulated plate sufficiently visible in both images?**

## Answer Format:

#Thought:  
[Your reasoning and observations here — visibility description of each identifiable plate in both images]

#Final Answer:  
Yes / No

#Reason:  
[A short justification — e.g., "All plates are clearly visible", or "The hand obscures the front surface of the plate in both views"]
""".strip()

SANDWICH_PROMPT = """
You are given a **pair of images** showing the beginning and end of a manipulation task in which a sandwich or hamburger is assembled using multiple food ingredients.

Your task is to analyze **only the final image**, which shows the completed sandwich or hamburger.

Your goal is to determine whether the **entire sandwich/hamburger**, including its **individual layers or components** is **sufficiently visible and unobstructed**, such that its structure, ingredient content, and assembly state can be clearly observed.

You should **only focus on the constructed sandwich/hamburger**, and **ignore any other food items, hands, or background objects** that are not part of the final assembled item.

## Visibility Criteria:

The sandwich or hamburger is considered sufficiently visible if:
- The whole item is visible from a clear perspective, and
- Each major layer (e.g., top bun, fillings, bottom bun) is either fully visible or only partially covered but still clearly identifiable.
- It is **not acceptable** if the sandwich is heavily covered by the hand, outside the camera frame, or key layers are obscured, making it hard to recognize the contents or structure.

## Instructions:
1. In the **Thought** section, first provide a brief caption that describes the appearance and structure of the sandwich/hamburger in the final image.  
   Then, carefully examine each major layer or component one by one. For each layer, describe whether it is clearly visible or obstructed.
2. Then, directly answer the question:  
**Is the sandwich or hamburger sufficiently visible in the completed image?**

## Answer Format:

#Thought:  
[Your reasoning and observations here — e.g., "Top bun and lettuce are visible, but tomato slice is obscured by hand"]

#Final Answer:  
Yes / No

#Reason:  
[A short justification — e.g., "Bottom bun is completely blocked by the hand", or "All major layers are clearly visible"]
""".strip()

LID_PROMPT = """
You are given two images, Image 1 and Image 2, showing the same tabletop scene at two different moments. Your task is to analyze the paper cups on the table.

Please perform the following steps:

1. Count the number of paper cups in either image. The number is the same in both images.

2. Evaluate whether each paper cup is properly placed on the table, using the following criteria:

A paper cup is considered "properly placed on the table" if:

The cup is not lifted off the tabletop by any hand — that is, it should be resting somewhere on the table surface, even if slightly tilted or not upright.

It does not matter whether a hand is touching or holding the cup, as long as the cup is not suspended in the air and is visibly supported by the table.

The cup either:

Has no lid placed on the rim, or

Has a lid that appears visually aligned and reasonably fitted on the cup opening.

The lid does not need to be perfectly flush, as long as it appears intentionally placed and not falling off.

A lid placed next to the cup or held in a hand is acceptable, as long as it's not partially and loosely attached to the cup.

You should ignore the position of any hands, and judge only from the visible physical relationship between the cup, the table, and the lid.

3. Final Answer Rule:

If the answer to step 1 is not 1 or 2, and the answer to step 2 is "all properly placed", then the Final Answer is "yes". Otherwise, the Final Answer is "no".

## Answer Format:

# Number of cups: <number>
# Cup placement status: <all properly placed / not all properly placed>
# Final answer: <yes / no>
""".strip()

OTHER_PROMPT = """
You are given a **pair of images** showing the beginning and end of a manipulation task involving one or more objects.

Your goal is to determine whether all target objects are **sufficiently visible and unobstructed in both images**, such that their identity, structure, and manipulation state can be clearly observed. Ignore background elements and focus only on objects intended for manipulation.

## Visibility Criteria:

An object is considered sufficiently visible if:
- It is fully visible, or partially blocked (e.g., touched by fingers) but still clearly identifiable.
- It is **not acceptable** if it is heavily obstructed by the hand or not visible in the camera view, making it difficult to recognize or understand its state.

## Instructions:
1. In the **Thought** section, first provide a brief caption that describes the overall arrangement and appearance of the target objects in both images.  
   Then, carefully examine each identifiable object one by one. For each object, describe whether it is clearly visible or obstructed in both images, according to the visibility criteria.
2. Then, directly answer the question:  
**Are all manipulable objects sufficiently visible in both images?**

## Answer Format:

#Thought:  
[Your reasoning and observations here — object descriptions + visibility status in both images]

#Final Answer:  
Yes / No

#Reason:  
[A short justification of your answer — which object is blocked and how, or confirm all are visible]
""".strip()
