.syntax unified
.thumb
.cpu arm7tdmi
.global native_call
native_call:
 push {lr}
 ldr r0, arg0
 ldr r1, arg1
 ldr r2, arg2
 ldr r3, target
 bl dispatch
 ldr r1, result
 str r0, [r1]
 pop {pc}
dispatch:
 bx r3
.align 2
arg0: .word 0x11111111
arg1: .word 0x22222222
arg2: .word 0x33333333
target: .word 0x44444444
result: .word 0x55555555
