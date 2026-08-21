MODULE SymbolPropertiesTest
    !DATE:        2026-08-21
    !AUTHOR:      C. RACINET
    !DESCRIPTION: RAPID module for Example 09 - RWS symbol properties test.
    !             Python reads symbol metadata via:
    !             GET /rw/rapid/symbol/properties/{symbolurl}
    !
    !             This module provides:
    !             - one scalar PERS num;
    !             - one one-dimensional PERS num array.
    !
    !             The goal is to validate parsing of:
    !             - symburl;
    !             - symtyp;
    !             - dattyp;
    !             - ndim;
    !             - dim;
    !             - local;
    !             - ro.
    !
    !             Expected Python-side result:
    !             ScalarValue -> ndim=0, dim=()
    !             Array1D     -> ndim=1, dim=(4,)
    !
    !             DeactUnit M7DM1 is required because this cell has a
    !             positioner that must be deactivated before RAPID execution.

    PERS num ScalarValue := 42;
    PERS num Array1D{4} := [10,20,30,40];

    !=========================================================================
    PROC main()
    !DESCRIPTION: Entry point. Deactivates the positioner, prints the current
    !             test values, then stops.
    !
    !             Python can read symbol properties while RAPID is stopped.
    !-------------------------------------------------------------------------
        DeactUnit M7DM1;

        TPWrite "SymbolPropertiesTest ready.";
        TPWrite "ScalarValue=" \Num:=ScalarValue;
        TPWrite "Array1D length should be 4.";

        PrintArray1D;

        TPWrite "Run pixi run -e examples python examples\\09\\symbol_properties.py";
        STOP;
    ENDPROC

    !=========================================================================
    PROC PrintArray1D()
    !DESCRIPTION: Print each Array1D value on the FlexPendant.
    !             This routine is only a visual check that the module was
    !             loaded correctly and that the array exists.
    !-------------------------------------------------------------------------
        VAR num i;

        FOR i FROM 1 TO 4 DO
            TPWrite "Array1D{" + NumToStr(i, 0) + "}=" \Num:=Array1D{i};
        ENDFOR
    ENDPROC

ENDMODULE
