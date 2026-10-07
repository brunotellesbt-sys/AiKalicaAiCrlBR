.syntax unified
.thumb
.section .text
.global journey_fixture_call4
.thumb_func
journey_fixture_call4:
    push {r4, lr}
    ldr r0, .Larg0
    ldr r1, .Larg1
    ldr r2, .Larg2
    ldr r3, .Larg3
    ldr r4, .Lfunction
    bl .Lcall
    ldr r1, .Lresult
    str r0, [r1]
    pop {r4, pc}
.Lcall:
    bx r4
.balign 4
.Larg0: .word 0x11111111
.Larg1: .word 0x22222222
.Larg2: .word 0x33333333
.Larg3: .word 0x44444444
.Lfunction: .word 0x55555555
.Lresult: .word 0x66666666
