MODULE ReadWriteVariable
    !**********************************************************************
    ! Example 03 - Read / Write RAPID variables
    !
    ! Auteur : Clement RACINET
    !
    ! Date : 13/07/2026
    !
    ! Purpose : Expose RAPID variables that Python can read and write
    !           via RWS symbol API.
    !
    ! Variable types demonstrated:
    !   - num    (gCounter)  : Python writes an integer as string "42"
    !   - string (gMessage)  : Python writes a quoted string "\"Hello\""
    !   - bool   (gEnabled)  : Python writes "TRUE" or "FALSE"
    !
    ! Note: PERS variables persist across program restarts.
    !       VAR variables are reset to their initial value on resetpp.
    !**********************************************************************

    ! Persistent variables - survive program restart
    PERS num    gCounter := 0;
    PERS string gMessage := "initial";
    PERS bool   gEnabled := FALSE;

    PROC main()
        ! Read the values set by Python and act on them
        IF gEnabled THEN
            TPWrite "Counter = " \Num:=gCounter;
            TPWrite "Message = " + gMessage;

            ! Increment counter from RAPID side
            gCounter := gCounter + 1;
        ELSE
            TPWrite "ExampleReadWrite: gEnabled is FALSE, skipping.";
        ENDIF
    ENDPROC

ENDMODULE
