MODULE RobtargetArray
    !DATE:        2026-07-16
    !AUTHOR:      C. RACINET
    !DESCRIPTION: RAPID module for Example 07 — robtarget array write test.
    !             Python writes TrajectoryPoints via RWS element by element.
    !             Call VerifyPoints from FlexPendant to check the result.
    !
    !             Reference position for this cell:
    !             trans=[1500,0,1789], rot=[0,0,1,0] (180° around Z)

    PERS robtarget TrajectoryPoints{10} := [
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]],
        [[1500,0,1789],[0,0,1,0],[0,0,0,0],[9E+9,9E+9,9E+9,9E+9,9E+9,9E+9]]
    ];

    !=========================================================================
    PROC main()
    !DESCRIPTION: Entry point. Deactivates the positioner, then stops.
    !             Python writes TrajectoryPoints via RWS while stopped here.
    !             Call VerifyPoints from FlexPendant to check the result.
    !-------------------------------------------------------------------------
        DeactUnit M7DM1;
        TPWrite "RobtargetArray ready.";
        TPWrite "Run pixi run -e examples example-07 on the PC.";
        TPWrite "Then call VerifyPoints to check the written values.";
        STOP;
    ENDPROC

    !=========================================================================
    PROC VerifyPoints()
    !DESCRIPTION: Print X coordinate of each written point on the FlexPendant.
    !-------------------------------------------------------------------------
        VAR num i;
        FOR i FROM 1 TO 10 DO
            TPWrite "Point "\Num:=i\Num:=TrajectoryPoints{i}.trans.x;
        ENDFOR
    ENDPROC

ENDMODULE
