/* Reproduce the single overwritten instruction, then resume the pinned HAL. */
.text
.balign 4
.global original_hint
.type original_hint, %function
original_hint:
    sub sp, sp, #0x50
    b original_hint_tail
.size original_hint, .-original_hint
.global original_interactive
.type original_interactive, %function
original_interactive:
    sub sp, sp, #0xa0
    b original_interactive_tail
.size original_interactive, .-original_interactive
