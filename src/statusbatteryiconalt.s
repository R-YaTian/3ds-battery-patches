.arm.little
.create "statusbatteryiconalt.bin", 0

.macro load, reg, func
    ldr reg, [pc, #func-.-8]
.endmacro

.arm
_start:
    stmfd sp!, {r1-r2,r7,lr}

    cmp r5, 1    ; if update was forced (eg. after suspend/sleep)
    moveq r0, 0  ; force battery level update
    movne r0, 30 ; otherwise cache 30 calls - called every second
    load r7, BatteryCachePtr
    nop

    cmp r0, 0
    beq zerobat

    mov r1, r0
    mov r0, 0

    cmp r1, 1 ; > 1 : 0 bars
    movgt r0, 1

    cmp r1, 5 ; > 5 : 1 bar
    movgt r0, 2

    cmp r1, 25 ; > 25 : 2 bars
    movgt r0, 3

    cmp r1, 50 ; > 50 : 3 bars
    movgt r0, 4

    cmp r1, 75 ; > 75 : 4 bars
    movgt r0, 5

    b outf

zerobat:
    ldr r0, =0x1FF81000
    ldrb r0, [r0, 0x85]
    and r0, r0, 0x1C
    mov r0, r0, lsr 2

outf:
    ldmfd sp!, {r1-r2,r7,pc}

; END _start

.pool
.align 4
    BatteryCachePtr         : .word 0xdead0001 ; free addr in data section
.close
