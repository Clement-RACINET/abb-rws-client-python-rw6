# Subscription Mod

Source file: `Subscription.mod`

```rapid
MODULE Subscription
    !DATE:        2026-07-26
    !AUTHOR:      C. RACINET
    !DESCRIPTION: Minimal module to test RWS WebSocket subscription on
    !             multiple RAPID PERS variables simultaneously.
    !
    !             Both WatchedValue1 and WatchedValue2 cycle automatically
    !             and continuously as soon as this module is started
    !             (PP to Main + Start on the FlexPendant). No manual
    !             routine call is required: AUTO mode locks "Call Routine"
    !             from the Production Window by default, so all test logic
    !             lives inside main() instead.
    !
    !             DeactUnit M7DM1 is required because this cell has a
    !             positioner (vireur) that must be deactivated before
    !             any RAPID execution.

    PERS num WatchedValue1 := 0;
    PERS num WatchedValue2 := 0;

    !=========================================================================
    PROC main()
    !DESCRIPTION: Entry point. Deactivates the positioner unit, then runs
    !             the automatic cycling loop forever. Stop with the RAPID
    !             stop button on the FlexPendant.
    !-------------------------------------------------------------------------
        DeactUnit M7DM1;
        TPWrite "Subscription example ready.";
        TPWrite "WatchedValue1 and WatchedValue2 will now cycle automatically.";
        AutoCycleValues;
    ENDPROC

    !=========================================================================
    PROC AutoCycleValues()
    !DESCRIPTION: Cycles WatchedValue1 (0..9, every 2s) and WatchedValue2
    !             (0..4, every 3s) independently and forever. Two different
    !             periods make it easy to see, on the Python side, which
    !             event belongs to which resource.
    !-------------------------------------------------------------------------
        VAR num i1 := 0;
        VAR num i2 := 0;
        WHILE TRUE DO
            WatchedValue1 := i1;
            TPWrite "WatchedValue1 --> "\Num:=i1;
            i1 := (i1 + 1) MOD 10;
            WaitTime 2;

            WatchedValue2 := i2;
            TPWrite "WatchedValue2 --> "\Num:=i2;
            i2 := (i2 + 1) MOD 5;
            WaitTime 3;
        ENDWHILE
    ENDPROC

ENDMODULE
```
