.arm.little
.create "statusbattery.bin", 0

.macro addr, reg, func
    add reg, pc, #func-.-8
.endmacro
.macro load, reg, func
    ldr reg, [pc, #func-.-8]
.endmacro
.macro _svc, num
    .word 0xEF000000 + num
.endmacro

.arm
_start:
    mov r3, 0 ; restore overwritten instruction

    stmfd sp!, {r0-r12,lr}
    add r12, sp, 14 * 0x4 ; get old SP

    cmp r5, 2      ; if update was forced (eg. after suspend/sleep)
    moveq r0, 0    ; force battery level update
    movne r0, 2000 ; otherwise cache 2000 calls - called each frame
    bl getBatteryLevel

    add r4, r12, 0x10
check:
    ldrh r1, [r4]
    cmp r1, 0
    beq exit
    add r4, r4, 2
    add r3, r3, 2
    b check
exit:
    add r12, r12, r3

    cmp r0, 0
    beq zerobat

    load r4, Prefix
    str r4, [r12, 0x10]

    cmp r0, 100
    bge fullbat

    mov r6, 0
loop:
    cmp r0, 10
    blt outloop
    sub r0, r0, 10
    add r6, r6, 1
    b loop
outloop:
    cmp r6, 0
    addne r6, r6, 0x30
    addeq r6, r6, 0x20
    add r0, r0, 0x30
    orr r6, r6, r0, lsl 16

    str r6, [r12, 0x10 + 2]

    load r4, PercentSign
    str r4, [r12, 0x10 + 6]
    mov r4, 0
    str r4, [r12, 0x10 + 10]

    b outf

zerobat:
    load r4, SMErrorMessage
    str r4, [r12, 0x10]
    load r4, SMErrorMessage + 4
    str r4, [r12, 0x10 + 4]
    mov r4, 0
    str r4, [r12, 0x10 + 8]

    b outf

fullbat:
    load r4, FullBatteryMessage
    str r4, [r12, 0x10 + 2]
    load r4, FullBatteryMessage + 4
    str r4, [r12, 0x10 + 6]
    mov r4, 0
    str r4, [r12, 0x10 + 10]

outf:
    ldmfd sp!, {r0-r12,pc}

; END _start

.include "src/getbatterylevel.s", 0

.pool
.align 4
    SMErrorMessage          : .dcb " ", 0, "E", 0, \
                                   "r", 0, "r", 0
    FullBatteryMessage      : .dcb "1", 0, "0", 0, \
                                   "0", 0, "%", 0
    PercentSign             : .dcb "%", 0,  0 , 0
    Prefix                  : .dcb " ", 0,  0 , 0
.close
