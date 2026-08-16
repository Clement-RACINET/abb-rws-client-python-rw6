# Iosignal Mod

Source file: `IOSignal.mod`

```rapid
MODULE ExampleIOSignal
    !**********************************************************************
    ! Example 05 - IO Signal interaction with Python
    !
    ! Author  : Clement RACINET
    !
    ! Date    : 13/07/2026
    !
    ! Purpose : RAPID side of the IO signal example.
    !           This module demonstrates safe read/write of a virtual
    !           digital output signal via the ABB RWS Python client.
    !
    !           The signal TEST_DO_RWS must be declared as a Virtual DO
    !           in the IO system (no physical wiring required).
    !           Python writes the signal value; this program reads it
    !           back and logs the result on the FlexPendant.
    !
    ! Prerequisites:
    !   - A virtual digital output "TEST_DO_RWS" configured in the IO
    !     system under a Virtual unit (e.g. VIRTUAL1).
    !   - No physical hardware required.
    !
    ! How to use:
    !   1. Create the virtual signal in RobotStudio:
    !         Controller > Configuration > I/O System > Signal
    !         Name: TEST_DO_RWS  |  Type: DO  |  Unit: VIRTUAL1
    !   2. Load this module and start RAPID (T_ROB1)
    !   3. Run: pixi run python examples/05/05_io_signal.py
    !   4. Observe the TPWrite output on the FlexPendant
    !
    ! Safety:
    !   This module only touches a virtual signal. No motion, no physical
    !   output, no risk of hardware damage.
    !**********************************************************************

    ! Signal alias - connects the RAPID variable to the configured IO signal.
    ! AliasIO must be called at runtime before any SetDO/WaitUntil.
    VAR signaldo TEST_DO_RWS_alias;

    PROC main()
        ! Connect the alias to the configured virtual signal
        AliasIO TEST_DO_RWS, TEST_DO_RWS_alias;
        TPWrite "ExampleIOSignal: AliasIO OK - TEST_DO_RWS connected.";

        ! Reset signal to a known state
        SetDO TEST_DO_RWS_alias, 0;
        TPWrite "ExampleIOSignal: signal reset to 0 - ready for Python.";

        ! Wait for Python to set the signal HIGH (timeout 60s)
        ! Note: WaitDI requires signaldi - use WaitUntil + DOutput for signaldo
        TPWrite "ExampleIOSignal: waiting for Python to set signal HIGH...";
        WaitUntil DOutput(TEST_DO_RWS_alias) = 1 \MaxTime:=60;

        TPWrite "ExampleIOSignal: signal HIGH detected - Python write confirmed.";

        ! Reset signal after acknowledgement
        SetDO TEST_DO_RWS_alias, 0;
        TPWrite "ExampleIOSignal: signal reset to 0 - done.";
    ENDPROC

ENDMODULE
```
