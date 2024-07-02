## Summary
- Users can use the platform Discord to interact with the program by using their application feature (A.K.A bot).
- The program will present the user with various functions related to Finite Automations when they input “/“ to a message field as commands.
- Each command will have different input parameters depends on the function.
- Some commands may save the user input and/or result in a database and link it to their Discord ID so they can be retrieved back later as histories.


## How to run

### Requirements

- Python 3.11+
- MySQL
- [Graphviz](https://graphviz.org/) (Put into PATH)
- A discord app token

### How to setup (Windows)
- Using `.env.example`. Create a `.env` file and fill it with the corresponding informations
- (Optional) Create a virtual enviroment
```bash
python venv .venv
```
- Enter the enviroment if you have created one
```bash
.venv/Scripts/activate
```
- Install the libraries in requirements.txt
```bash
pip install -r requirements.txt
```
- Run setup to setup the database
```bash
python setup.py
```
- Run the main file
```bash
python -O main.py
```


## Data Structure:
The FA data consist of 5 values:
- states (set[str]) : Finite set of states (Q{q})
- alphabets: (set[str]) : Finite set of input symbols (s)
- Initial_state (str) : The start state (q0)
- final_states (set[str]) : Finite set of accepted states
- transition_functions (dict[tuple, str]) : Tuple holds (q, s) = q’

We store Discord user id as an identification that links the user to their FA history (long int). And the time they entered or updated an FA.


## Detailed Guide for the Bot
Once you have entered a command in the message box. You can choose how to give FA data for the bot to process.
Most commands will have a optional `recent` option where you can choose past FA data you have entered to the bot.

![](storage\examples\command.png)
---
If you do not choose the recent option, a form will pop up asking you to enter each data of the FA you want to give to the bot.

![](storage\examples\modal.png)

Let's breakdown each of the elements.
### States
___
The names of all of the states in the FA. Must be separated by spaces, commas, etc.
```
// OK
q0 q1
q0,q1
q'0-q‘1
q_0,+-:|!@#$%^&*()`~ q'1

// Not OK
q0q1
q0_q1
q0'q1
q0‘q1
```

### Alphabets
___
The availible symbols to use in the FA. Does not need seperations. Does not accept non-alphabet characters.
```
// OK
abc
a b c
a, b, c
0, 1

// Not OK
@ # $ / ?...
```
### Initial State
___
The start state of the FA. Entered state must be one of the states in the `States` section above.
```
// OK
q0
q0 q1 // Only takes q0
```
### Final State(s)
___
Can be one or more states. Entered states must be a subset of the states in the `States` section above. Parse inputs the same as `States`.
### Transition Functions
___
Each function must be seperated by a newline. There are also multiple accepted separators too. States and symbols must exists in the `States` and `Alphabets` sections.

```
// OK
q0,a=q1
q0+b->q1
q1,=q2 // Epsilon

// Not OK
q0, ab = q1
...
```

#### Note: If the data entered is invalid, The form will show this generic error `Something went wrong. Try again.`. This is a Discord limitation.
---
If you choose the `recent` option. This will show up containing your recent FA datas you entered from the past, sorted by last used.
Selecting one and press enter will skip the form and take you to the result.

![](storage\examples\recent.png)

#### Please do not add or remove any characters from the selection.
