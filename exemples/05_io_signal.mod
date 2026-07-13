MODULE ExampleIOSignal
    !**********************************************************************
    ! Example 05 — IO Signal interaction with Python
    !
    ! Purpose : RAPID side of the IO signal example.
    !           Python writes DO_EXAMPLE; this program reads it and reacts.
    !
    ! Prerequisites:
    !   - A digital output signal "DO_EXAMPLE" configured in the IO system
    !   - A digital input  signal "DI_EXAMPLE" configured (optional)
    !
    ! How to use:
    !   1. Load this module and start RAPID
    !   2. Run: pixi run python examples/05_io_signal.py
    !   3. Observe the TPWrite output on the FlexPendant
    !**********************************************************************

    ! Signal aliases — must match the names in the IO configuration
    ALIAS signaldo DO_EXAMPLE_OUT;
    ALIAS signaldi DI_EXAMPLE_IN;

    PROC main()
        ! Wait for Python to set the signal high
        TPWrite "Waiting for DO_EXAMPLE to go HIGH...";
        WaitDI DI_EXAMPLE_IN, 1 \MaxTime:=30;

        TPWrite "Signal received! Executing response action.";

        ! Pulse the output for 500ms as acknowledgement
        PulseDO \PLength:=0.5, DO_EXAMPLE_OUT;

        TPWrite "ExampleIOSignal: done.";
    ENDPROC

ENDMODULE
