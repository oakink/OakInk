### Sequence label and its meanings

1. The first part of the sequence label represents `object_id`. For example, the sequence labeled as `S100014_xxxx_xxxx` means that the object used in this sequence is `S100014.obj` (stored at `$OAKINK_DIR/image/obj/S100014.obj` )

2. The second part of the sequece label represent `intent_id`. The intent  is labeled per sequence. We asked a subject to perform intent of  _use_ and  record his/her hand during the whole course of interaction.  The `intent_name` to `intent_id` mappings are:

   ```python
   "use": "0001",
   "hold": "0002",
   "liftup": "0003",
   "handover": "0004", # handover = give + receive
   ```

3. The third (and fourth) part of the sequence represet `subject_id` which cooresponds to a certain person. 

In summary: 

* sequence: **A_B_C**  :  **A** means `object_id`, **B** means `intent_id`, and **C** means `subject_id`;

* sequence **A_B_C_D** :  **A** means `object_id`, **B** means `intent_id`,  and **C** & **D** means `subject_id`;  (**C** is the giver, **D** is the receiver)
