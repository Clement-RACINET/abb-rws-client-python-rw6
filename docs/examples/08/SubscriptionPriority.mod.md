# Subscriptionpriority Mod

Source file: `SubscriptionPriority.mod`

```rapid
MODULE SubscriptionPriority
    !DATE:        2026-08-21
    !AUTHOR:      C. RACINET
    !DESCRIPTION: RAPID module used to test ABB RWS subscription priorities.
    !
    !             The module updates two PERS num variables at a high and
    !             regular rate. This makes it possible to compare RWS
    !             subscription priorities:
    !
    !             - Low priority    : max delay 5 seconds
    !             - Medium priority : max delay 200 ms
    !             - High priority   : as soon as possible
    !
    !             High priority is valid for PERS RAPID variables and IO
    !             signals according to ABB RWS documentation.
    !
    !             DeactUnit M7DM1 is kept because this cell has a positioner
    !             that must be deactivated before RAPID execution.

    PERS num FastValue1 := 0;
    PERS num FastValue2 := 0;

    CONST num MaxValue1 := 9999;
    CONST num MaxValue2 := 9999;

    !=========================================================================
    PROC main()
    !DESCRIPTION: Entry point for the RWS subscription priority test.
    !-------------------------------------------------------------------------
        DeactUnit M7DM1;

        TPWrite "RWS subscription priority test ready.";
        TPWrite "FastValue1 and FastValue2 will cycle every 50 ms.";

        AutoCycleFastValues;
    ENDPROC

    !=========================================================================
    PROC AutoCycleFastValues()
    !DESCRIPTION: Updates two persistent variables every 50 ms.
    !
    !             Both variables are updated during the same RAPID loop cycle
    !             so that Python can observe how RWS subscription priority
    !             affects event delivery frequency.
    !-------------------------------------------------------------------------
        VAR num value1 := 0;
        VAR num value2 := 0;

        WHILE TRUE DO
            FastValue1 := value1;
            FastValue2 := value2;

            value1 := value1 + 1;
            value2 := value2 + 1;

            IF value1 > MaxValue1 THEN
                value1 := 0;
            ENDIF

            IF value2 > MaxValue2 THEN
                value2 := 0;
            ENDIF

            WaitTime 0.05;
        ENDWHILE
    ENDPROC

ENDMODULE
```
