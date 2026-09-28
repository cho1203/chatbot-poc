- No part of this manual may be reproduced in any form.
- All specifications and designs are subject to change without notice.

The  products  in  this  manual  are  controlled  based  on  Japan's  'Foreign  Exchange  and Foreign Trade Law'. The export from Japan may be subject to an export license by the government of Japan. Further, re-export to another country may be subject to the license of the government of the country from where the product is re-exported. Furthermore, the product may also be controlled by re-export regulations of the United States government. Should you wish to export or re-export these products, please contact FANUC for advice.

In this manual we have tried as much as possible to describe all the various matters. However, we cannot describe all the matters which must not be done, or which cannot be done, because there are so many possibilities. Therefore, matters which are not especially described as possible in this manual should be

regarded as 'impossible'.

This manual contains the program names or device names of other companies, some of which  are  registered  trademarks  of  respective  owners.  However,  these  names  are  not followed by ® or ™ in the main body.

## SAFETY PRECAUTIONS

When using machines incorporating FANUC MANUAL GUIDE i ,  be  sure  to  observe  the  descriptions herein.

## Contents

| DEFINITION OF WARNING, CAUTION, AND NOTE.........................................................................s-1                                  |
|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| GENERAL WARNINGS AND CAUTIONS............................................................................................s-1                          |
| OVERVIEW OF THIS MANUAL............................................................................................................s-2                |
| SYMBOLS USED......................................................................................................................................s-3 |
| FORMAT OF PROGRAMS TO BE USED ..............................................................................................s-3                       |

## DEFINITION OF WARNING, CAUTION, AND NOTE

This manual includes safety precautions for protecting the user and preventing damage to the machine. Precautions are classified into Warning and Caution according to the degree of the risk or the severity of damage.

Also, supplementary information is described as Note.

Read the Warning, Caution, and Note thoroughly before attempting to use the machine.

## WARNING

Applied when there is a danger of the user being injured or when there is a damage of both the user being injured and the equipment being damaged if the approved procedure is not observed.

## CAUTION

Applied when there is a danger of the equipment being damaged, if the approved procedure is not observed.

## NOTE

The Note is used to indicate supplementary information other than Warning and Caution.

- Read this manual carefully, and store it in a safe place.

## GENERAL WARNINGS AND CAUTIONS

To ensure safety while using a machine featuring the MANUAL GUIDE i function, observe the following precautions:

## WARNING

- 1 Confirm, on the screen, that the data has been entered correctly before proceeding to the next operation. Attempting operation with incorrect data may cause the tool to strike the workpiece or machine, possibly breaking the tool or machine or injuring the operator.
- 2 Before starting the machine using the tool compensation function, carefully determine the direction of compensation and the compensation value, and ensure that the tool will not strike the workpiece or machine. Otherwise the tool or machine may be damaged or the operator may be injured.

WARNING 3 When using constant surface speed control, set the maximum rotating speed of the spindle to a value that is allowed for the workpiece and workpiece hold unit. Otherwise, the workpiece or hold unit may be removed by centrifugal force to damage the tool machine or injure the operator. 4 Set all necessary parameters and data items before starting MANUAL GUIDE i operations. Note that if the cutting conditions are not suitable for the workpiece, the tool may be damaged or the operator may be injured. 5 After creating a machining program using MANUAL GUIDE i functions, do no run the machine on that program immediately. Instead, confirm every step of the resultant program, and make sure that the tool path and machining operation are correct and that the tool will not strike the workpiece or machine. Before starting production machining, run the machine with no workpiece attached to the machine to make sure that the tool will not strike a workpiece or the machine. If the tool strikes the machine and/or work-piece, the tool and/or machine may be damaged, and even injuries the operator.

- CAUTION After pressing the power-on button, do not touch any keys on the keyboard until the initial screen appears. Some keys are used for maintenance or special operations such that pressing such a key may cause an unexpected operation.

## OVERVIEW OF THIS MANUAL

This manual describes the functions of MANUAL GUIDE i for the Series 0 i -MODEL C, 0 i -MODEL D, Series 16 i /18 i /21 i -MODEL B, or Series 30 i /31 i /32 i -MODEL A.

For other functions, refer  to  the  operator's  manual  for  the  Series  0 i -MODEL C, 0 i -MODEL D, Series 16 i /18 i /21 i -MODEL B, Series 30 i /31 i /32 i -MODEL A, or Series 30 i /31 i /32 i -MODEL B. The  specifications  and  usage  of  MANUAL  GUIDE i may  vary  according  to  the  specifications  of  the operator's panel of a machine tool. Be sure to read the manual provided by the machine tool builder.

The  functions  of  the  CNC  machine  tool  system  are  determined  not  only  by  the  CNC,  but  by  the combination of the machine tool, the power magnetic circuit in the machine tool, the servo system, the CNC, and the operator's panel.

It is impossible to cover all possible combinations of all functions, programming methods, and operations in a single manual.

This manual explains only the MANUAL GUIDE i operations provided for the CNC. For individual CNC machine tools, refer to applicable manuals from the machine tool builders.

This manual explains as many detailed functions as possible. However, it is not possible to describe all of the  items  which  cannot  be  done  or  which  the  operator  must  not  do.  Therefore,  please  assume  that functions other than those described in this manual cannot be performed.

Detailed  information  and  special  conditions  are  explained  in  notes.  The  readers  may  encounter  new technical terms in the notes not previously defined or described. In this case, read this manual through first, then review the details.

s-2

## 2.8 CUT

NEWPRG

OPEN

SRCH ↑

SRCH ↓

↑

SRCH ↓

PASTE

KEYPST

DELETE

CUT

COPY

O SRCH

CUT

<!-- image -->

Pressing soft key [CUT] displays a message that prompts you to select a range of data to be cut. First select the cut range (by displaying it in yellow), using cursor keys, and then press soft key [CUT]. The data  cut  off  from  the  specified  range  is  stored  on  the  clipboard.  The  contents  of  the  clipboard  can  be pasted to other places in the program and to other programs.

Clip board is the memory, in which the content of part program can be stored temporary. By pressing soft key [CUT] or [COPY], the content of the cursor selected is stored in it, then the old content is cleared. The content of the clip board is cleared at the power off of CNC.

A clip board size can be selected using bits 4 (CLP1) and 5 (CLP2) of parameter No. 14701.

Bit 4(CLP1)= 0, bit 5(CLP2)= 0: Sets a clip board size of 1024 bytes.

Bit 4(CLP1)= 1, bit 5(CLP2)= 0: Sets a clip board size of 2048 bytes.

Bit 4(CLP1)= 0, bit 5(CLP2)= 1: Sets a clip board size of 4096 bytes.

Bit 4(CLP1)= 1, bit 5(CLP2)= 1: Sets a clip board size of 8192 bytes.

## NOTE

The contents of the clipboard are preserved until the power is shut off or other data is stored on the clipboard. So, the clipboard contents can be used any number of times.

## 2.9 COPY

NEWPRG

SRCH

OPEN

Pressing soft key [COPY] displays a message that prompts you to select a range of data to be copied. First select the copy range (by displaying it in yellow), using cursor keys, and then press soft key [COPY]. The data  copied  from  the  specified  range  is  stored  on  the  clipboard.  The  contents  of  the  clipboard  can  be pasted to other places in the program and to other programs.

## NOTE

Once a range of data to be copied has been selected, the cursor is placed back to the first block in the selected range if parameter CEB (No.14705#1) = 0 or the last block if CEB (No.14705#1) = 1.

## 2.10 PASTE

NEWPRG

OPEN

SRCH ↑

SRCH ↓

O SRCH

O SRCH

COPY

COPY

CUT

DELETE

DELETE

KEYPST

KEYPST

PASTE

PASTE

<!-- image -->

Pressing soft key [PASTE] pastes the contents of the clipboard to the place that immediately follows the current cursor position.

The clipboard contents are preserved.

## NOTE

If the setting value of the parameter No.27335 is bigger than the value of the parameter No.27336, then the number of speed steps for the machining simulation speed level is equivalent to be the same value with the setting in No.27336.

## 3.8 BLANK CUTOUT DISPLAY IN ANIMATED SIMULATION

The beginning angle of the blank cutout display can be changed in machining animated simulation. This function is enabled when the parameter No.27312#7 is set to 1.

## 3.8.1 Operation

By  pressing  [CUTDSP]  soft  key  the  beginning  angle  of  the  blank  cutout  display  can  be  changed according to following order.

0 degree -&gt; 90 degree -&gt; 180 degree -&gt; 270 degree-&gt;OFF

<!-- image -->

Beginning angle of the blank cutout and the display position is kept until CNC switching off.

## 4.12.1 Format of Comment Display G code G2900

The format of comment display G code G2900 is as follows.

## G2900 Pp(xxxxx) ;

| Address   | Meaning                                                                                                                                                                                                                                                                                                                                                                                                   |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| P         | Display / Deletion setting P0 : The comment is deleted from the screen P1 : The comment is displayed on the screen                                                                                                                                                                                                                                                                                        |
| (xxxxx)   | Comment The character string in round parentheses is displayed on the screen. The string can be formed by the following set of characters: • Only a special alphabet/figure/sign • A special sign; The following signs except % () ?,@#=*+[]& /. SP (Note) Note) SP means space. • The number of characters which can be displayed is 37 characters or less. (Do not depend on the size of the indicator) |

(Examples)

(1) G2900 P1 (ABC 12345) 'ABC 12345' is displayed.

(2) G2900 P0 The comment is deleted.

## 4.12.2 Notes

The notes of G2900 are as follows.

- (1) In the case of specifying number for address P excluding 0 or 1, and specifying no comment, nether comment display nor deletion are done.
- (2) When there is no character string in the specified comment, the comment is erased from the screen.
- (3) The name of machining cycle is not displayed during the comment display.
- (4) If the G code G2900 is executed in machining simulation or machining drawing, then the character string is not displayed.
- (5) In the NC program conversion, comment display G code G2900 is output as it is into the converted program.
- (6) The  comment  remains  on  the  base  screen  when  returning  from  machining  simulation  screen  or machining  drawing  screen  after  switching  to  them.  However,  the  comment  is  erased  on  the  base screen  when  returning  from  machining  simulation  screen  after  switching  to  them  in  Series 30 i /31 i /32 i -A or Series 0 i -D.
- (7) If  the  mode switch is done in the state of STOP or the state of HOLD then the comment remains being displayed.
- (8) When  the  G  code  G2900  is  executed  during  the  automatic  operation  in  the  RMT  mode  or  the subprogram is called from M198, then the comment is not displayed.
- (9) If the parameter No.14700#0 is set to 1, then the comment cannot be displayed until switching to the NC screen once and returning back to MANUAL GUIDE i .

- &lt;4&gt;  Pressing  the  soft  key  corresponding  to  the  tool  management  data  to  be  output  displays  a confirmation message. Pressing the soft key [YES] directs the tool management data to the memory card.

## 8.4.8 Inputting Tool Management Data from the Memory Card

The following procedure can input tool management data.

- &lt;1&gt;  On the machine operator's panel, select the edit mode to display a window for tool management.
- &lt;2&gt;  Press  the  soft  key  [TOOL]  to  display  the  tool  management  function  window,  and  then  press  the leftmost soft key [&lt;] or the rightmost soft key [&gt;] several times. The soft keys shown below appear.

OUTPUT

CLOSE

INPUT

- &lt;3&gt;  Press the soft key [INPUT]. The following array of soft keys appear, enabling data to be selected for input.

TOOL

[TOOL]

P\_NAME

DSPCT

STATUS

CSTM

MAG

:  Inputs tool management information and tool database data.

[MAG]

:  Inputs magazine management table data.

[STATUS]  : Inputs tool life status name data.

[CSTM]

:  Inputs customization data name data.

Displaying the following 3 items requires installing the tool management expansion option.

[DSPCT]

:  Inputs window customization data.

[P\_NAME]  : Inputs spindle and standby position name data.

[POINT]

:  Inputs customization data decimal point position data.

- &lt;4&gt;  Pressing the soft key corresponding to the tool management data to be input displays a confirmation message. Pressing the soft key [EXEC] causes the tool management data to be input to the memory card.

POINT

CANCEL

2.MEMORY CARD

## 2 MEMORY CARD INPUT/OUTPUT FUNCTION

## 2.1 MEMORY CARD INPUT/OUTPUT OF PROGRAM

## 2.1.1 Memory Card Input/Output Screen of Program

| NEWPRG   | O LIST   | SRCH ↑   | SRCH ↓   | O SRCH   | COPY   | CUT   | DELETE   | KEYPST   | PASTE   |
|----------|----------|----------|----------|----------|--------|-------|----------|----------|---------|

Select EDIT mode on the machine operator's panel. Pressing soft key [O LIST] displays the program list window, programs registered in the CNC. Following soft-keys are displayed.

- (a) In case of Series 16 i /18 i /21 i , 30 i /31 i /32 i -A

| COPY NEW   | M SEARCH DELETE EDTCOM   | CLOSE OPEN SRTORD MLT DEL CARD   |
|------------|--------------------------|----------------------------------|

(b) In case of Series 30 i /31 i /32 i -B , 0 i -D(with USB interface )

| NEW   | SEARCH DELETE EDTCOM COPY   | CLOSE OPEN SRTORD MLT DEL IN/OUT   |
|-------|-----------------------------|------------------------------------|

Pressing  the  soft  key  [M  CARD]  or  the  soft  key  [IN/OUT]  on  the  program  list  screen  displays  the [INPUT/OUTPUT PROGRAM BY MEMORY CARD] screen.

Following soft-keys are displayed.

| INPUT   | INP.O   | SEARCH DELETE   | OUTPUT   | FORMAT   | RETURN USB   |
|---------|---------|-----------------|----------|----------|--------------|

[INPUT] :  Inputs a program from the memory card. [INP.O] :  Inputs a program from the memory card (by changing the O number). [DELETE]  : Deletes files on the memory card. [SEARCH]  : Searches for a file on the memory card. [OUTPUT]  : Displays the screen for output to the memory card. [FORMAT] : Formats the memory card. (Note) [USB] :  Displays the [INPUT/OUTPUT PROGRAM BY USB MEMORY] screen. (Note) [RETURN]  : Returns the screen display to the program list screen.

In order to delete a file in the memory card, place the cursor on the file name in the above window and press soft key [DELETE]. This soft key displays a message for checking if selected file may be deleted. Pressing soft key [YES] deletes the file in the memory card. Pressing soft key [NO] cancels the deletion of all programs.

| YES   | NO   |
|-------|------|

In  case  of  initializing  the  memory  card  such  as  deleting  all  files  in  the  memory  card,  press  soft  key [FORMAT].  This  soft  key  displays  a  message  for  checking  if  the  memory  card  may  be  initialized. Pressing soft key [YES] initializes the memory card and all files in the memory card are deleted. Pressing soft key [NO] cancels the deletion of all programs.

## NOTE

- 1 When the CNC screen display function is in use, neither of the following items is displayed.
- Soft key [FORMAT]
- Whether the memory area is in use or not
- 2 Soft key [USB] is displayed for Series 30 i /31 i /32 i -B and Series 0 i - TD /0 i - MD only . And, in case of Series 0 i - TD /0 i - MD, It is necessary to meet the following requirements.
- Using the following main boards with USB interface
- &lt;1&gt; main board B2 ( A20B-8200-0842 )
- &lt;2&gt; main board B3 ( A20B-8200-0843 )
- Using the following softwares
- &lt;1&gt; 19.0th edition or more of NC basic software ( D4F1/D6F1 )
- &lt;2&gt; 1.0th edition or more of USB software ( 659B )
- &lt;3&gt; 12.0th edition or more of MANUAL GUIDE i software ( BX32 )
- The parameter No.14854#0=1

## 2.1.2 Memory Card Output Operation for Program

Pressing  the  soft  key  [OUTPUT]  on  the  INPUT/OUTPUT  PROGRAM  BY  MEMORY  CARD  screen displays the OUTPUT PROGRAM TO MEMORY CARD screen.

The following soft-keys are displayed.

| SEARCH   | RETURN SRTORD ALLOUT MLTOUT OUTPUT   |
|----------|--------------------------------------|

[SEARCH]  : Searches for a program.

[OUTPUT]  : Output a selected program to the memory card.

[MLTOUT] : Output multi programs to the memory card.

[ALLOUT]  : Output all programs to the memory card.

[SRTORD]  : Switches  the  sort  order  for  displaying  a  program  list  between  ascending  order  and descending order.

[RETURN]  : Returns the screen display to the [INPUT/OUTPUT PROGRAM BY MEMORY CARD] screen.

Pressing soft key [SEARCH] displays the following window of program searching.

Enter the program number to be searched, then press soft key [SEARCH].

B-63874EN-2/04

2.MEMORY CARD

INPUT/OUTPUT FUNCTION

CONVENIENT

FUNCTIONS

## 2.4.3 Input Operation for Fixed Form Sentences

| NEW   | ALTER   | DELETE   | STAND.   | OUTPUT   | INPUT   | TO MNU   |
|-------|---------|----------|----------|----------|---------|----------|

Pressing [INPUT] displays the following window of the file list store in the memory card. Select the file in which fixed form sentences are stored and to be read to CNC by placing the cursor by

the cursor key.

Pressing [INPUT] begins reading the tool data to CNC form the memory card.

## 2.4.4 Format of Fixed Form Sentences

The following format can be input or output for fixed form sentences.

## &lt;Mode&gt;=\_,&lt;Tab&gt;=\_,&lt;Title&gt;=\_,&lt;Code&gt;=\_

Mode :

Setting the mode of Fixed form sentences (Milling or Turning).

1 :

Fixed Form Sentence for turning mode

2 :

Fixed Form Sentence for milling mode

3 :

Fixed Form Sentence for milling and turning mode

Tab  :

The number of tab(1 - 5)

Title :

Setting the name of Fixed Form Sentence

Code :

Setting Fixed Form Sentence

4 words, &lt;Mode&gt;=, &lt;Tab&gt;=, &lt;Title&gt;=, &lt;Code&gt;=, can't be input as the name of fixed form sentence or fixed form sentence.

## 3 USB MEMORY INPUT/OUTPUT FUNCTION (FOR Series 0 i -D,30 i /31 i /32 i -B)

## 3.1 USB MEMORY INPUT/OUTPUT OF PROGRAM

## 3.1.1 USB Memory Input/Output Screen of Program

| NEWPRG   | O LIST   | SRCH ↑   | SRCH ↓   | O SRCH   | COPY   | CUT   | DELETE   | KEYPST   | PASTE   |
|----------|----------|----------|----------|----------|--------|-------|----------|----------|---------|

Select EDIT mode on the machine operator's panel. Pressing soft key [O LIST] displays the program list window, programs registered in the CNC. Following soft-keys are displayed.

| NEW   | SEARCH DELETE EDTCOM COPY   | CLOSE OPEN SRTORD MLT DEL IN/OUT   |
|-------|-----------------------------|------------------------------------|

Pressing the soft key [IN/OUT] on the program list screen displays the [INPUT/OUTPUT PROGRAM BY USB MEMORY] screen.(Note)

Following soft-keys are displayed.

| INPUT   | INP.O   | DELETE   | RETURN M CARD OUTPUT   |
|---------|---------|----------|------------------------|

[INPUT] :  Inputs a program from the USB memory. [INP.O] :  Inputs a program from the USB memory (by changing the O number). [DELETE]  : Deletes files on the USB memory. [OUTPUT]  : Displays the screen for output to the USB memory. [M CARD]  : Displays the [INPUT/OUTPUT PROGRAM BY MEMORY CARD] screen. [RETURN]  : Returns the screen display to the program list screen.

In order to delete a file in the USB memory, place the cursor on the file name in the above window and press soft key [DELETE]. This soft key displays a message for checking if selected file may be deleted. Pressing soft key [YES] deletes the file in the USB memory. Pressing soft key [NO] cancels the deletion of all programs.

| YES   | NO   |
|-------|------|

|   NOTE | NOTE                                                                                                                                             |
|--------|--------------------------------------------------------------------------------------------------------------------------------------------------|
|      1 | When both the USB memory and memory card are inserted, pressing the soft key [IN/OUT] displays the [INPUT/OUTPUT PROGRAM BY MEMORY CARD] screen. |
|      2 | The item whether the memory area is in use or not is displayed on USB memory.                                                                    |

6.SHORTCUT KEY OPERATIONS

B-63874EN-2/04

CONVENIENT

FUNCTIONS

| Soft key   | Shortcut key   |
|------------|----------------|
| [SF5]      | [5]+[INPUT]    |
| [SF6]      | [6]+[INPUT]    |
| [SF7]      | [7]+[INPUT]    |
| [SF8]      | [8]+[INPUT]    |
| [SF9]      | [9]+[INPUT]    |
| [SF10]     | [0]+[INPUT]    |
| [>]        | [.]+[INPUT]    |

* By  setting  bit  1  (SFN)  of  parameter  No.  14703  to  1,  a  number  for  shortcut  operation  can  be displayed under each soft key.

## 6.6 SHORTCUT FOR STARTING THE CYCLE CHANGE SCREEN

| Soft key   | Shortcut key   |
|------------|----------------|
| [ALTER]    | [INPUT]        |

## 6.7 SHORTCUTS FOR THE MENU SELECTION SCREEN

| Soft key   | Shortcut key                |
|------------|-----------------------------|
| [SELECT]   | [INPUT] or numeral +[INPUT] |
| [CANCEL]   | [CAN]                       |

## 6.8 SHORTCUTS FOR THE REGULAR PROGRAM INSERTION SCREEN

| Soft key   | Shortcut key                |
|------------|-----------------------------|
| [INSERT]   | [INPUT] or numeral +[INPUT] |
| [CLOSE]    | [CAN]                       |

## 6.9 SHORTCUTS FOR THE M CODE INSERTION SCREEN

| Soft key   | Shortcut key   |
|------------|----------------|
| [INSERT]   | [INPUT]        |
| [CLOSE]    | [CAN]          |

## 6.10 SHORTCUTS FOR THE PROGRAM LIST SCREEN

| Soft key   | Shortcut key    |
|------------|-----------------|
| [OPEN]     | [INPUT] or [9]  |
| [CLOSE]    | [CAN] or [0]    |
| [DELETE]   | [DELETE] or [3] |
| [EDTCOM]   | [ALTER] or [4]  |
| [NEW]      | [1]             |
| [COPY]     | [2]             |
| [SEARCH]   | [5]             |
| [M CARD]   | [6]             |
| [ALLDEL]   | [7]             |

## 10.1.2 Condition

It is necessary for this function to satisfy the following conditions.

- (1) Parameter No.27313#0 = 0
- (2) Foreground operation is not executed.
- (3) A new program can be created.
- (4) Capacity of the unused program memory is enough.

## 10.1.3 Restriction

- (1) When the decomposed cycle display is executed during foreground operation, warning is displayed. However, foreground operation and machining simulation are not interrupted.
- (2) If  a  new  program  can  not  be  created  on  machining  simulation  of  the  decomposed  cycle  display, warning is displayed, when machining cycle is executed.
- (3) If  capacity  of  the  unused  program  memory  is  not  enough  on  machining  simulation  of  the decomposed cycle display, warning is displayed, when machining cycle is executed.

## 10.2 INPUT DATA CHECK BY SIMULATION

The operation of a cycle that is being edited can be checked by machining simulation (animation / tool path drawing ) while cycle data input screen is displayed.

<!-- image -->

## 10.2.1 Condition

It is possible to use this function on the following conditions.

- (1) MANUAL GUDIE i screen can be operated on only first path. Concretely, it is the case that one of following conditions is met.
2. &lt;1&gt;  'MANUAL GUIDE i Multi Path function' is invalid.
3. &lt;2&gt;  Parameter  No.14864  =  1  (MANUAL  GUIDE i is  valid  on  only  first  path.),  parameter No.27401#0 - #1 = 0 and parameter No.27402#0 - #1 = 0.(Turret 2 and 3 are unavailable.)
- (2) A program can be newly made.

## 1.6 CHANGING MACHINING CYCLE AND FIGURE DATA

To change the contents of a machining cycle and fixed form figure, place the cursor on the related block, and press soft key [ALTER]. To change the contents of an arbitrary figure and contour program, place the cursor at the first of the related blocks, and press soft key [ALTER]. In any case, a data entry window for these items appears. After making the necessary data changes, press soft  key  [CREATE]  in  the  same  manner  as  for  new  entry.  New  figures  are  written  to  the  machining program.

## 1.7 NOTES ON CREATING PROGRAMS

This section provides notes on creating programs. Read the notes before creating a program.

(1) Programmed commands required before machining cycle input (a) When using a tool database with a CNC of the M series, be sure to enter a D command (offset number). (b) Be sure to enter a spindle rotation command. At the same time, specify whether to enable or disable constant surface speed control. (c) No feedrate command needs to be specified, because a feedrate command is separately entered as a machining cycle command. However, specify a command for feed per revolution or feed per minute as required. For example, operator know-how on executing milling in pocketing by feed per revolution can be utilized. (d) Enter an M code command for switching between the spindle and C-axis, and a command for C-axis reference position return as required. (e) Enter M codes such as for coolant ON/OFF as required. (f) Upon completion of machining cycle, the tool always returns to the position before the start of the  machining  cycle.  By  setting  bit  7  (ESC)  of  parameter  No.  27002  to  1,  the  tool  can  be prevented from returning to the position before the start of the machining cycle. (g) For the machining cycle mentioned above, a similar command is repeatedly entered. So, such a command can be entered easily by registering a fixed form sentence beforehand. (2) Machining cycle (a) Specify an I point coordinate not as a distance from point R but as a coordinate value. (b) Figure  data  should  be  entered  as  a  subprogram  for  utilization  in  roughing,  finishing,  and chamfering. This eliminates the need to enter figure data each time. (c) In  machining  of  a  projected  portion  (island  figure),  efficient  machining  can  be  achieved  by using pocketing with an island instead of using contouring. In this case, specify a blank as the outer wall of a pocket. (d) In contouring (side facing), enter a start point figure and end point figure so that both figures contact  each  other.  This  means  that  by  starting  not  from  a  corner  of  a  figure  but  from  an intermediate point on a straight line, undercutting due to approaching the figure and retraction can be eliminated.