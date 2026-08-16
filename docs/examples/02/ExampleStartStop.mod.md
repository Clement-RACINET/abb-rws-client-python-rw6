# Examplestartstop Mod

Source file: `ExampleStartStop.mod`

```rapid
MODULE StartStop
    !**********************************************************************
    ! Example 02 - Start / Stop
    !
    ! Auteur : Clement RACINET
    !
    ! Date : 13/07/2026
    !
    ! Purpose : Minimal RAPID program to demonstrate start/stop from Python.
    !           The robot moves to a safe home position and stops.
    !
    ! Usage   : Load this module into T_ROB1.
    !           Run from Python: pixi run python examples/02_start_stop.py
    !
    ! Note    : Adapt pHome to a safe position for your robot cell.
    !**********************************************************************

    ! Safe home position : ADAPT TO YOUR CELL
    CONST robtarget pHome := [[1500, 0, 1789],
                               [0, 0, 1, 0],
                               [0, 0, 0, 0],
                               [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
                               
    CONST robtarget pTarget := [[1800, 0, 1789],
                               [0, 0, 1, 0],
                               [0, 0, 0, 0],
                               [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]];
    PROC main()
        
        DeactUnit M7DM1;
        
        ! Move to home position at medium speed
        MoveJ pHome, v10, fine, tool0;
        MoveJ pTarget, v10, fine, tool0;
        MoveJ pHome, v10, fine, tool0;

        ! Signal Python that work is done
        TPWrite "StartStop: done.";
    ENDPROC

ENDMODULE
```
