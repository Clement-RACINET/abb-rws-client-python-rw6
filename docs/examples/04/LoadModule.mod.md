# Loadmodule Mod

Source file: `LoadModule.mod`

```rapid
MODULE LoadModule
    !**********************************************************************
    ! Example 04 - Dynamic module loading
    !
    ! Auteur : Clement RACINET
    !
    ! Date : 13/07/2026
    !
    ! Purpose : This module is loaded at runtime by Python via RWS.
    !           It demonstrates that a module can be injected into a
    !           running task without FlexPendant interaction.
    !
    ! How to use:
    !   1. Transfer this file to the controller: $HOME/LoadModule.mod
    !      (via FTP, USB, or RWS fileservice)
    !   2. Run: pixi run python examples/04_load_module.py
    !   3. The module is now available in T_ROB1
    !   4. Run: pixi run python examples/02_start_stop.py to execute it
    !**********************************************************************

    CONST robtarget pSafePos := [[1500, 0, 1789],
                                    [0, 0, 1, 0],
                                    [0, 0, 0, 0],
                                    [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];

    PROC main()

        DeactUnit M7DM1;

        TPWrite "LoadModule: loaded and running!";

        ! Move to safe position to confirm physical execution
        MoveJ pSafePos, v100, fine, tool0;

        TPWrite "LoadModule: motion complete.";
    ENDPROC

ENDMODULE
```
