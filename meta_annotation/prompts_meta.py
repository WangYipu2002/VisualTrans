SYSTEM_PROMPT_BOWL1 = """
You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving stacked or assembled objects on a flat surface.

Your task is to extract key meta-information to support downstream processing. Please complete the following subtasks:

1. Determine which image shows a "completed stack or assembly", meaning the structure is fully assembled and stable — not an empty setup and not in the middle of the assembly process.

2. For the scene (regardless of completion), determine whether the manipulation is occurring on a **dark blue bed** or a **dark green bed**.  
Answer with one of: `"dark blue bed"` or `"dark green bed"`.

3. In the non-completed image, list all the bowls you can see. You must describe each bowl using only one of the following names, each defined by its visual characteristics and hex color:

light teal bowl — a medium saturated lime green (#5E9C95)
pale sage green bowl — a very light sage green, with cooler tones, with a muted green  (#C5E3D0)
light purple bowl — a muted, cool lavender shade with a gentle, calm appearance. (#C8BFE7)
dark forest green bowl — a deep green, rich and subdued. (#334B46)
orange bowl (#FF4500)

4. In the non-completed image, identify and report:
- The leftmost visible object  
- The rightmost visible object  
- The object closest to the camera  

If the position is unclear or ambiguous, write `none` for that field. Use object names from step 3.

5. In the non-completed image, construct a scene graph by identifying adjacent objects and their clearly interpretable pairwise spatial relationships.
Describe each spatial relationship using only one of the following 8 predefined spatial relations. These relations are mutually exclusive and prioritize specificity from the **camera's viewpoint**. The terms are interpreted based on the object's 2D position in the image (The origin (0,0) is in the upper left corner of the image):

left: on the left side (x is small), y is roughly the same.
right: on the right side (x is large), y is roughly the same.
top: higher in the image (y is small), x is roughly the same.
bottom: lower in the image (y is large), x is roughly the same.
left-top: left and higher (x and y are both small).
right-top: right and higher (x is large, y is small).
left-bottom: left and lower (x is small, y is large).
right-bottom: right and lower (x and y are both large).


**Important Rule for Reporting a Relationship:**
You must only report a relationship if you are certain that:

a) Object A is the only adjacent object located in the specified direction of object B, within a clearly adjacent spatial region.
There must be no other object in the same direction that could also reasonably satisfy that spatial relation with object B.
This ensures all reported relations are unambiguous, mutually exclusive, and spatially unique.
If there is any ambiguity or overlap in the region (e.g., more than one object partially in the right-bottom of B), then do not report that relation.
✅ Use object names from step 3 only.
✅ Only include relations between neighboring objects (objects that are adjacent or visually close in the image).

b)Each scene graph triple must follow the format:  
`(A, spatial_relation, B)` → "A is located in the **spatial_relation direction of B**".  
In other words, **B is the reference object**, and **A is positioned relative to B**.
Do not reverse this logic.

**Example (valid):**
(orange bowl, right, light purple bowl)
→ There is only one adjacent object clearly to the right of the light purple bowl: the orange bowl.

**Example (invalid, do not report):**
If two objects are both near the right-top of a bowl, and it's unclear which one is closer or more aligned — do not report that relation.


Output format (strictly follow this structure):
# Completed image: Image 1 / Image 2  
# Surface type: dark blue bed / dark green bed  
# Object list: [object_1, object_2, ...]  
# Position: right:object_1/none, left:object_2/none, closest:object_3/none  
# Scene graph: (object_1, spatial_relation, object_2),...
""".strip()

SYSTEM_PROMPT_BOWL2="""
In the image, identify visible stacked or assembled bowls that are part of the structure placed on the table or bed surface.

light teal bowl — a medium saturated lime green (#5E9C95)
pale sage green bowl — a very light sage green, with cooler tones, with a muted green  (#C5E3D0)
light purple bowl — a muted, cool lavender shade with a gentle, calm appearance. (#C8BFE7)
dark forest green bowl — a deep green, rich and subdued. (#334B46)
orange bowl (#FF4500)

For each bowl ({object_list}), list bowls from **top to bottom**, based strictly on their **physical stacking order**, not visual appearance or camera perspective.

Do not invent new names, and do not modify the provided names in any way.

Output format (strictly follow this structure):
# Completed structure: [top_object, ..., bottom_object]
""".strip()

SYSTEM_PROMPT_PLATE1 = """
You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving stacked or assembled plates on a flat surface.

Your task is to extract key meta-information to support downstream processing. Please complete the following subtasks:

1. Determine which image shows a "completed stack or assembly", meaning the structure is fully assembled and stable — not an empty setup and not in the middle of the assembly process.

2. For the scene, determine whether the manipulation is occurring on a **brown pillow**.  
Answer with one of: `"has brown pillow"` or `"no brown pillow"`.

3. In the non-completed image, list all the plates you can see. You must describe each plate using **only one of the following names**:
- blue plate
- green plate
- red plate
- yellow plate

4. In the non-completed image, identify and report:
- The leftmost visible object  
- The rightmost visible object  
- The object closest to the camera  

If the position is unclear or ambiguous, write `none` for that field. Use object names from step 3.

5. In the non-completed image, construct a scene graph by identifying adjacent objects and their clearly interpretable pairwise spatial relationships.
Describe each spatial relationship using only one of the following 8 predefined spatial relations. These relations are mutually exclusive and prioritize specificity from the **camera's viewpoint**. The terms are interpreted based on the object's 2D position in the image (The origin (0,0) is in the upper left corner of the image):

left: on the left side (x is small), y is roughly the same.
right: on the right side (x is large), y is roughly the same.
top: higher in the image (y is small), x is roughly the same.
bottom: lower in the image (y is large), x is roughly the same.
left-top: left and higher (x and y are both small).
right-top: right and higher (x is large, y is small).
left-bottom: left and lower (x is small, y is large).
right-bottom: right and lower (x and y are both large).


**Important Rule for Reporting a Relationship:**
You must only report a relationship if you are certain that:

a) Object A is the only adjacent object located in the specified direction of object B, within a clearly adjacent spatial region.
There must be no other object in the same direction that could also reasonably satisfy that spatial relation with object B.
This ensures all reported relations are unambiguous, mutually exclusive, and spatially unique.
If there is any ambiguity or overlap in the region (e.g., more than one object partially in the right-bottom of B), then do not report that relation.
✅ Use object names from step 3 only.
✅ Only include relations between neighboring objects (objects that are adjacent or visually close in the image).

b)Each scene graph triple must follow the format:  
`(A, spatial_relation, B)` → "A is located in the **spatial_relation direction of B**".  
In other words, **B is the reference object**, and **A is positioned relative to B**.
Do not reverse this logic.

**Example (valid):**
(yellow plate, right, blue plate)
→ There is only one adjacent object clearly to the right of the blue plate: the yellow plate.

**Example (invalid, do not report):**
If two objects are both near the right-top of a plate, and it's unclear which one is closer or more aligned — do not report that relation.

Output format (strictly follow this structure):
# Completed image: Image 1 / Image 2  
# Surface type: has brown pillow / no brown pillow  
# Object list: [object_1, object_2, ...]  
# Position: right:object_1/none, left:object_2/none, closest:object_3/none  
# Scene graph: (object_1, spatial_relation, object_2),...
""".strip()

SYSTEM_PROMPT_PLATE2 = """
In the image, identify visible stacked or assembled plates that are part of the structure placed on the table or bed surface.

For each plate ({object_list}), list plates from **top to bottom**, based strictly on their **physical stacking order**, not visual appearance or camera perspective.

Do not invent new names, and do not modify the provided names in any way.

Output format (strictly follow this structure):
# Completed structure: top_object, ..., bottom_object
""".strip()

SYSTEM_PROMPT_LEGO1 = """
You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving stacked or assembled LEGO blocks on a flat surface.

Your task is to extract key meta-information to support downstream processing. Please complete the following subtasks:

1. Determine which image shows a "completed stack or assembly", meaning the structure is fully assembled and stable — not an empty setup and not in the middle of the assembly process.

2. For the scene (regardless of completion), determine whether the manipulation is occurring on a **dark blue bed** or a **dark green bed**.  
Answer with one of: `"dark blue bed"` or `"dark green bed"`.

3. In the non-completed image, list all the blocks you can see.  Use the format "*color block*" for each item (e.g., "yellow block", "blue block").  If there are multiple blocks of the same color, repeat them individually in the list. 

4. In the non-completed image, identify and report:
- The leftmost visible object  
- The rightmost visible object  

If the position is unclear or ambiguous, write `none` for that field. Use object names from step 3.

5. In the non-completed image, construct a scene graph by identifying adjacent objects and their clearly interpretable pairwise spatial relationships.
Describe each spatial relationship using only one of the following 8 predefined spatial relations. These relations are mutually exclusive and prioritize specificity from the **camera's viewpoint**. The terms are interpreted based on the object's 2D position in the image (The origin (0,0) is in the upper left corner of the image):

left: on the left side (x is small), y is roughly the same.
right: on the right side (x is large), y is roughly the same.
top: higher in the image (y is small), x is roughly the same.
bottom: lower in the image (y is large), x is roughly the same.
left-top: left and higher (x and y are both small).
right-top: right and higher (x is large, y is small).
left-bottom: left and lower (x is small, y is large).
right-bottom: right and lower (x and y are both large).


**Important Rule for Reporting a Relationship (Enhanced Conservative Version):**

You must only report a relationship if **all** of the following conditions are strictly met:


a) **Unambiguous Directional Uniqueness and Adjacency**  
Object A must be the **only clearly visible** and **spatially adjacent** object located in the specified direction of object B.  
There must be **no other competing object** in the same directional region (even partial overlap or borderline cases are disallowed).  
> ✅ If there is **any ambiguity, visual overlap, occlusion, or uncertainty** or **the spacing or alignment does not clearly satisfy any directional label**, do **not** report the relation.


b) **Strict Positional Format**  
Each scene graph triple must follow the format:  
`(A, spatial_relation, B)` → "A is located in the **spatial_relation** direction of B."  
B is the **reference** object; A is the **positioned** object.  
> 🚫 Do not reverse this logic.

c) **Handling Non-Unique Object Names**  
If any object (e.g., "red block") appears more than once in the object list, **remove all relations involving such objects**.  
Then, you must **re-check** each remaining relation:

- ✅ Only keep it if A is **still** the clearly adjacent and uniquely positioned object relative to B.
- 🚫 Do **not** skip over previously removed or occluded objects.
- 🚫 Do **not** "promote" farther objects to be adjacent just because a closer one was removed.

d)**Be Selective: precise is better than many**  
Do **not** attempt to maximize the number of scene graph relations.  
You are encouraged to report **certain and precise and visually justified** relationships if necessary, many relations are not necessary.

Output format (strictly follow this structure):
# Completed image: Image 1 / Image 2  
# Surface type: dark blue bed / dark green bed  
# Object list: [object_1, object_2, ...]  
# Position: right:object_1/none, left:object_2/none  
# Scene graph: (object_1, spatial_relation, object_2),...
""".strip()

SYSTEM_PROMPT_LEGO2 = """
In the image, describe the configuration of all visible components that are part of the stacked structure on the table or bed.

For each object ({object_list}), provide the following:

Object: The object's name.  
Only use the names provided in the list above. Do not invent new names or add any identifiers (e.g., numbers or positions).  
If the provided object list contains multiple blocks of the same color, this means the same type of block appears multiple times in the structure. You must describe each occurrence accordingly.
If a listed object is not visible in the assembled structure, skip it.

Layer: An integer representing the vertical level of the object.  
- Layer 1 is the bottommost layer in direct contact with the table or bed.  
- Multiple objects can exist in the same layer if they lie side-by-side at the same level.

Above: List the names of blocks that are **directly placed on top** of this object and are in **visible physical contact**.  
If no block is placed on top, write `"none"`.

Below: List the names of blocks that are **directly supporting** this object from below and are in **visible physical contact**.  
If no block is underneath, write `"none"`.

Do not assume any physical contact unless it is clearly visible in the image. Do not infer relationships that are not visually supported.

Output format (strictly follow this structure):
# Completed lego structure:
- Object: object_name
  Layer: N
  Above: object_name, object_name, ... # or "none"
  Below: object_name, object_name, ... # or "none"
""".strip()

SYSTEM_PROMPT_BUILD_LEGO = """You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving stacked or assembled objects on a flat surface.
Your task is to extract key meta-information to support downstream processing. Please complete the following subtasks:

1. Determine which image shows a "completed stack or assembly", meaning the structure is fully assembled and stable — not an empty setup and not in the middle of the assembly process.

2. In the non-completed image, list all the blocks you can see.  Use the format "*color block*" for each item (e.g., "yellow block", "blue block").  If there are multiple blocks of the same color, repeat them individually in the list. 

3. In the non-completed image, identify and report:
- The leftmost visible object
- The rightmost visible object

4. In the non-completed image, construct a scene graph by identifying adjacent objects and their clearly interpretable pairwise spatial relationships.
Describe each spatial relationship using only one of the following 8 predefined spatial relations. These relations are mutually exclusive and prioritize specificity from the **camera's viewpoint**. The terms are interpreted based on the object's 2D position in the image (The origin (0,0) is in the upper left corner of the image):

left: on the left side (x is small), y is roughly the same.
right: on the right side (x is large), y is roughly the same.
top: higher in the image (y is small), x is roughly the same.
bottom: lower in the image (y is large), x is roughly the same.
left-top: left and higher (x and y are both small).
right-top: right and higher (x is large, y is small).
left-bottom: left and lower (x is small, y is large).
right-bottom: right and lower (x and y are both large).


**Important Rule for Reporting a Relationship (Enhanced Conservative Version):**

You must only report a relationship if **all** of the following conditions are strictly met:


a) **Unambiguous Directional Uniqueness and Adjacency**  
Object A must be the **only clearly visible** and **spatially adjacent** object located in the specified direction of object B.  
There must be **no other competing object** in the same directional region (even partial overlap or borderline cases are disallowed).  
> ✅ If there is **any ambiguity, visual overlap, occlusion, or uncertainty** or **the spacing or alignment does not clearly satisfy any directional label**, do **not** report the relation.


b) **Strict Positional Format**  
Each scene graph triple must follow the format:  
`(A, spatial_relation, B)` → "A is located in the **spatial_relation** direction of B."  
B is the **reference** object; A is the **positioned** object.  
> 🚫 Do not reverse this logic.

c) **Handling Non-Unique Object Names**  
If any object (e.g., "red block") appears more than once in the object list, **remove all relations involving such objects**.  
Then, you must **re-check** each remaining relation:

- ✅ Only keep it if A is **still** the clearly adjacent and uniquely positioned object relative to B.
- 🚫 Do **not** skip over previously removed or occluded objects.
- 🚫 Do **not** "promote" farther objects to be adjacent just because a closer one was removed.


d)**Be Selective: precise is better than many**  
Do **not** attempt to maximize the number of scene graph relations.  
You are encouraged to report **certain and precise and visually justified** relationships if necessary, many relations are not necessary.

**Example (valid):**  
(red block, right-bottom, blue block)  
→ There is only one clearly visible adjacent object to the right-bottom of the blue block: the red block.

**Example (invalid):**  
- Two objects are both near the right-bottom of B: relation is ambiguous → do not report.  
- A closer object was removed due to non-unique name, and a farther one is now in the same direction → do not report.


Output format (strictly follow this structure):
# Completed image: Image 1 / Image 2  
# Object list: [object_1, object_2, ...]
# Position: right:object_1/none, left:object_2/none
# Scene graph: (object_1, spatial_relation, object_2),...
""".strip()

SYSTEM_PROMPT_INSERT_CUP = """You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving stacked or assembled objects on a flat surface.

Please complete the following tasks:

1. For the scene, determine whether the manipulation is occurring on a **brown pillow**.  
Answer with one of: `"has brown pillow"` or `"no brown pillow"`.

2. In the non-completed image, list all the cups you can see. You must describe each cup using **only one of the following names**:
- blue cup
- green cup
- red cup
- yellow cup

3. For both Image 1 and Image 2, choose **one of the following two tasks** based on whether stacking is present:

**(a) If there is NO stacking of cups** (i.e., no cups are physically inside or directly on top of others):  
Construct a scene graph by identifying adjacent objects and their clearly interpretable pairwise spatial relationships.

Describe each spatial relationship using only one of the following 8 predefined spatial relations. These relations are mutually exclusive and prioritize specificity from the **camera's viewpoint**. The terms are interpreted based on the object's 2D position in the image (The origin (0,0) is in the upper left corner of the image):

left: on the left side (x is small), y is roughly the same.
right: on the right side (x is large), y is roughly the same.
top: higher in the image (y is small), x is roughly the same.
bottom: lower in the image (y is large), x is roughly the same.
left-top: left and higher (x and y are both small).
right-top: right and higher (x is large, y is small).
left-bottom: left and lower (x is small, y is large).
right-bottom: right and lower (x and y are both large).

**Important Rule for Reporting a Relationship:**
You must only report a relationship if you are certain that:

1) Object A is the only adjacent object located in the specified direction of object B, within a clearly adjacent spatial region.
There must be no other object in the same direction that could also reasonably satisfy that spatial relation with object B.
This ensures all reported relations are unambiguous, mutually exclusive, and spatially unique.
If there is any ambiguity or overlap in the region (e.g., more than one object partially in the right of B), then do not report that relation.
✅ Use object names from step 3 only.
✅ Only include relations between neighboring objects (objects that are adjacent or visually close in the image).

2)Each scene graph triple must follow the format:  
`(A, spatial_relation, B)` → "A is located in the **spatial_relation direction of B**".  
In other words, **B is the reference object**, and **A is positioned relative to B**.
Do not reverse this logic.

3)**Be Selective: precise is better than many**  
Do **not** attempt to maximize the number of scene graph relations.  
You are encouraged to report **certain and precise and visually justified** relationships if necessary, many relations are not necessary.

**Example (valid):**
`(red cup, right, blue cup)`  
→ There is only one adjacent object clearly to the right of the blue cup: the red cup.

**Example (invalid, do not report):**
If two objects are both near the right of a cup, and it's unclear which one is closer or more aligned — do not report that relation.


**(b) If there IS stacking of cups** (i.e., any cups are physically nested or stacked vertically):  
Do **not** generate a scene graph.  
Instead, for each group of stacked cups, report their stacking order.

Use the following format:  
`Completed structure: [top_object, ..., bottom_object]`  
→ The first object in the list is the one on **top**, and the last is the one on **bottom**.  

✅ Use object names from step 2 only.  
✅ from top to bottom, based on their vertical position in the image (y-axis) — that is, objects appearing higher in the image are considered "top", and those lower are considered "bottom",

Output format (strictly follow this structure):

# Surface type: has brown pillow / no brown pillow  
# Object list: [object_1, object_2, ...]  
For each image:
- If the image shows stacked cups, output:
  # Completed structure (Image X): [top_object, ..., bottom_object]
- If the image shows no stacking, output:
  # Scene graph (Image X): (object_1, spatial_relation, object_2), ...
"""


SYSTEM_PROMPT_SANDWICH = """
You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving assembling or disassembling a sandwich(hamburger) on a flat surface.

Your task is to extract key meta-information to support downstream processing. Please complete the following subtasks:

1. Determine which image shows a "completed sandwich(hamburger)", meaning the sandwich(hamburger) is fully assembled and stable — not an empty setup and not in the middle of the assembly process.

2. **Identify the surface type**: Determine whether the manipulation is happening on a **blue bed** or a **beige bed** (based on the visible flat surface underneath the objects).
- Answer with one of: `"blue bed"` or `"beige bed"`.

3. **List ingredients in the non-completed image**: For the image **that does not show the completed sandwich(hamburger)**, list **all visible food components** used in the assembly. Use precise English phrases that combine both color and object type (e.g., `Red tomato slices`, `Brown and beige bacon strip`). 
- Ignore any background, hands, or unrelated items.
- Ensure the names are correct and match the objects in the image.
- All lowercase letters.

4. In the non-completed image, construct a scene graph by identifying adjacent objects and their clearly interpretable pairwise spatial relationships.
Describe each spatial relationship using only one of the following 8 predefined spatial relations. These relations are mutually exclusive and prioritize specificity from the **camera's viewpoint**. The terms are interpreted based on the object's 2D position in the image (The origin (0,0) is in the upper left corner of the image):

left: on the left side (x is small), y is roughly the same.
right: on the right side (x is large), y is roughly the same.
top: higher in the image (y is small), x is roughly the same.
bottom: lower in the image (y is large), x is roughly the same.
left-top: left and higher (x and y are both small).
right-top: right and higher (x is large, y is small).
left-bottom: left and lower (x is small, y is large).
right-bottom: right and lower (x and y are both large).

🔒 Important Rules for Reporting a Relationship:

a) Object A must be directly adjacent to object B in the specified direction, with no other ingredient in between or overlapping that region.  
Objects should be **visually close** — far or isolated objects should not be considered adjacent.

b) If the directional relationship is ambiguous, or if more than one object lies in the target region, do **not** report the relation.

c) Only report relationships where the direction is **visually unique and mutually exclusive**.

💡 Tip:  
Visually divide the scene into 3 horizontal regions (left, center, right).  
Begin with the center objects, and only examine near neighbors.  
Do not report long-distance relations across the entire scene.

✅ Format:
(A, relation, B) → A is located in the **relation-direction** of B  
→ **B is the reference object**, A is described relative to it.

Example (valid):
(yellow cheese slice, right, green vegetable leaf)

Example (invalid):
(pink ham slice, right-bottom, beige bun slice) ← too far apart and other items intervene.


5.List vertical sandwich (hamburger) structure (top-down)
Based **only on the completed image**, list the ingredients from **top to bottom**, following their **clearly observable physical stacking order**.

You must follow these strict rules:
✅ Only select names from list in step 3.
✅ Only include components whose **vertical position (above or below another visible object)** is clearly and unambiguously observable.  
✅ It is acceptable to skip intermediate layers that are **partially occluded or whose stacking order is unclear**.  
✅ The result may be a non-continuous list (e.g., top and bottom layers), as long as the reported items have **definitive vertical order** among them.

🚫 Do NOT include:
- Any object that is partially hidden and whose vertical order is ambiguous.
- Any inference based on texture, edge, or suspected shape.
- Any guesswork to "fill in" missing layers.

🎯 Your goal is to provide a **partially ordered vertical list** of sandwich ingredients where the **relative stacking (above/below)** between reported items is absolutely certain.


Output format (strictly follow this structure):
# Completed image: Image 1 / Image 2  
# Surface type: blue bed / beige bed  
# Object list: [object_1, object_2, ...]    
# Scene graph: (object_1, spatial_relation, object_2),...
# Completed structure: [top_object, ..., bottom_object]
""".strip()


SYSTEM_PROMPT_TABLE_CLEANUP ="""You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving organise the desktop.
Your task is to extract key meta-information to support downstream processing. Please complete the following four subtasks:

1. Determine which image represents a "completed tabletop setup".

- The tablecloth is properly unfolded and not pushed aside or disorganized.
- All relevant objects (e.g., plates, food items, cups, forks) are placed **on top of the tablecloth**.
- Plates and food(if any) should be neatly aligned: food(if any) centered on plates, utensils beside them, and all objects aligned intentionally.

2. In the selected "completed" image, describe objects that are manipulated. Ignore background items, hands, and objects not involved in the task.
Object: A short descriptor (e.g., "red tablecloth").

Output format (strictly follow this structure):
# Completed image: Image 1 / Image 2  
# Object list: [object_1, object_2, ...]  
""".strip()

SYSTEM_PROMPT_BOOKSHELF ="""You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving organizing books into a bookend.

Your task is to extract key meta-information to support downstream reasoning. Please complete the following four subtasks:

1. Determine which image represents a "completed book arrangement":
- All books are placed inside the bookend in an upright position.
- No books are left scattered or lying flat outside the bookend.
- The scene appears finalized and not in the middle of the organization process.

2. For the scene (regardless of completion), determine whether the manipulation is occurring on a **dark blue bed** or a **yellow table**.  
Answer with one of: `"dark blue bed"` or `"yellow table"`.

3. In the non-completed image, identify and report: (range: red book,green book and blue book)

The leftmost visible book

The rightmost visible book

The book closest to the camera

If the position is unclear or ambiguous, write none for that field
⚠️ Note: The same book may occupy more than one of these positions (e.g., it can be both the closest and the leftmost book).

4. In the **completed** image, list the books arranged inside the bookend from left to right. Use short visual descriptors such as visible color (range: red book,green book and blue book).

**Output format (strictly follow this structure):**
# Completed image: Image 1 / Image 2  
# Surface type: dark blue bed / yellow table  
# Position: right:book_1/none, left:book_2/none, closest:book_3/none  
# Completed structure: [book_1, book_2, ...]

""".strip()

SYSTEM_PROMPT_FOOD ="""You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving arranging food items on a plate.

Your task is to extract key meta-information to support downstream reasoning. Please complete the following subtasks:

1.  For **both** Image 1 and Image 2, list all food items that are currently placed **on the right-side plate**.
  - Use concise visual descriptors.
  - Only include items that are clearly **inside or resting directly on** the right-hand plate.
  - Do **not** include items placed outside the plate or on other surfaces.
  - Note: The contents of the right-side plate in Image 1 and Image 2 **often differ**, so make sure to carefully observe each image and report the food items **independently**.

**Output format (strictly follow this structure):**
# Plate contents (Image 1): [item_1, item_2, ...]  
# Plate contents (Image 2): [item_1, item_2, ...]
""".strip()


SYSTEM_PROMPT_BEADS = """You are a multimodal reasoning assistant. I will give you a pair of images (Image 1 and Image 2), showing two different moments in a manipulation task involving sorting beads into groups.

Your task is to extract key meta-information to support downstream reasoning. Please complete the following three subtasks:

1. Determine which image shows a "completed grouping result":
- Beads are clearly separated into **distinct spatial groups** based on color, shape, or other apparent criteria.
- The layout appears intentional and structured (not randomly scattered or loosely clustered).
- The grouping task appears finalized, not still in progress.

2. For the scene (regardless of completion), determine whether the manipulation is occurring on a **red bed** or a **yellow table**.  
Answer with one of: `"red bed"` or `"yellow table"`.

3. In the **completed image**, count how many distinct groups of beads with the **same color** have been formed.
- A group refers to a cluster of beads that share the **same color** and are placed **spatially close together**, clearly separated from beads of other colors.
- Do not count scattered single beads that are not visibly grouped.
- Report the total number of such color-based groups as an integer.

**Output format (strictly follow this structure):**
# Completed image: Image 1 / Image 2  
# Surface type: red bed / yellow table
# Number of groups: integer(2/3/.../10)
""".strip()

SYSTEM_PROMPT_CONNECT_FOUR = """
You are given 3 images showing a Connect Four board (blue plastic grid) placed on a tabletop. The board contains red and yellow circular discs inserted into its vertical slots.

Please complete the following task:

1. For the scene, determine whether the manipulation is occurring on a **yellow table** or a **green table**.  
Answer with one of: `"yellow table"` or `"green table"`.

2. Analyze only the **discs that are already inserted inside the blue grid**, and extract their positions.

Please follow these instructions strictly:

1) Only consider discs that are **fully enclosed within one of the circular holes of the blue plastic grid** — meaning they are clearly sitting inside the grid and not outside, not partially inserted, not lying on the table, and not held by hand.

2) The blue grid has 6 horizontal rows and 7 vertical columns.

   Numbering convention:
   - **Rows** are numbered **from bottom to top**:
     - Row 1 is the bottom-most row,
     - Row 6 is the top-most row.
   - **Columns** are numbered **from left to right**:
     - Column 1 is the left-most vertical slot,
     - Column 7 is the right-most vertical slot.

   A disc that sits in the bottom-left corner of the grid is at position **(row: 1, col: 1)**.

3) Column assignment must follow **uniform vertical segmentation**:

   - The blue grid is evenly divided into **7 vertical columns** of equal width.
   - You must mentally divide the entire width of the blue frame into 7 equal **vertical slices**.
   - The column number of each disc is determined **only by which vertical slice its center falls into**, regardless of spacing between discs.
   - **Do not estimate column index based on distance to neighbors** — always use the fixed grid alignment.
   - Even if the board is shown at an angle or rotated slightly, you should still divide the full width of the visible blue grid into 7 equal parts.


Output format (strictly follow this structure):

# Surface type: yellow table / green table
# Disc positions(Image 1): "red": [{"row": <number>, "col": <number>},...],"yellow": [{"row": <number>, "col": <number>},...]
# Disc positions(Image 2):
# Disc positions(Image 3):
""".strip()


