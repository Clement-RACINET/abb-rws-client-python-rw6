MODULE ExampleSubscription
    !DATE:        2026-07-16
    !AUTHOR:      C. RACINET
    !DESCRIPTION: Minimal module to test RWS WebSocket subscription.
    !             Run ToggleWatchedValue from the FlexPendant to trigger
    !             a value change event on the Python side.
    !
    !             DeactUnit M7DM1 is required because this cell has a
    !             positioner (vireur) that must be deactivated before
    !             any RAPID execution.

    PERS num WatchedValue := 0;

    !=========================================================================
    PROC main()
    !DESCRIPTION: Entry point. Deactivates the positioner unit, then
    !             waits. The actual test is driven from the FlexPendant
    !             by calling ToggleWatchedValue manually.
    !-------------------------------------------------------------------------
        DeactUnit M7DM1;
        TPWrite "ExampleSubscription ready.";
        TPWrite "Call ToggleWatchedValue to trigger WebSocket events.";
        STOP;
    ENDPROC

    !=========================================================================
    PROC ToggleWatchedValue()
    !DESCRIPTION: Toggles WatchedValue between 0 and 1.
    !             Each call triggers one WebSocket event on the Python client.
    !-------------------------------------------------------------------------
        IF WatchedValue = 0 THEN
            WatchedValue := 1;
            TPWrite "WatchedValue → 1";
        ELSE
            WatchedValue := 0;
            TPWrite "WatchedValue → 0";
        ENDIF
    ENDPROC

    !=========================================================================
    PROC CycleWatchedValue()
    !DESCRIPTION: Cycles WatchedValue 0→1→2→...→9→0 in a loop with 2s delay.
    !             Useful to observe a stream of events without needing to
    !             call ToggleWatchedValue manually each time.
    !             Stop with the RAPID stop button on the FlexPendant.
    !-------------------------------------------------------------------------
        VAR num i := 0;
        WHILE TRUE DO
            WatchedValue := i;
            TPWrite "WatchedValue → "\Num:=i;
            i := (i + 1) MOD 10;
            WaitTime 2;
        ENDWHILE
    ENDPROC

ENDMODULE
