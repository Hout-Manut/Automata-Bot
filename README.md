## Summary
- Users can use the platform Discord to interact with the program by using their application feature (A.K.A bot).
- The program will present the user with various functions related to Finite Automations when they input “/“ to a message field as commands.
- Each command will have different input parameters depends on the function.
- Some commands may save the user input and/or result in a database and link it to their Discord ID so they can be retrieved back later as histories.


## How to run

### Requirements

- Python 3.11+
- mySQL
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
- Run setup
```bash
python setup.py
```
- Run the main file
```bash
python -O main.py
```


## Command Breakdowns
### design:
    - User input FA data and the program will message back a diagram image.
    - Args:
        - Form : Will be shown a form to enter the data after the command’s invocation
    - Returns:
        - Image of the diagram
    - Additional functions:
        - Save the data (optionally the image) with the user ID to database
        - Give the user options to use the output image further upon showing to them (convert or minimize)
### test fa:
    - User input FA data and the program will message back an answer whether the FA is deterministic or not.
    - Args:
        - Form : Will be shown a form to enter the data after the command’s invocation
    - Returns:
        - Boolean message
    - Additional functions:
        - Save the data with the user ID to database
        - Give the user options to use the output image further upon showing to them (generate a diagram)
### test string:
    - User input char/string and the program checks if it is accepted by an FA. FA will be asked after the command’s invocation. Then the strings will be taken from any messages the user sends afterward (i.e no /)
    - Args:
        - History (Optional) : Let the user select from their saved FA. If not, show a form to input a new FA
    - Returns:
        - Boolean message and the string that updates in realtime. Will delete the users input after confirming its to be used to test the string. (If user say “!stop”, stops the function)
    - Additional functions:
        - Idk yet
### Convert NFA to DFA:
    - Gets an NFA and converts to DFA, throw an error if passed a DFA.
    - Args:
        - History (Optional) : Let the user select from their saved NFA. If not, show a form to input a new NFA
    - Returns:
        - DFA data and diagram
    - Additional functions:
        - Save the data (optionally the image) with the user ID to database
        - Give the user options to use the output image further upon showing to them (minimize)
### minimize:
    - Gets a DFA and shorten it, throw an error if passed a NFA or it can not be shorten further.
    - Args:
        - History (Optional) : Let the user select from their saved DFA. If not, show a form to input a new DFA
    - Returns:
        - Minimized DFA data and diagram
    - Additional functions:
        - Save the data (optionally the image) with the user ID to database
### history:
    - Gets the user past FA, let them delete and maybe set a name.
    - Args:
        - History : The user’s FA history
    - Returns:
        - The FA data and Diagram, additional data such as FA types, FA is minimize-able, date and the option to delete.

## Data Structure:
 The FA data consist of 5 values:
 ⁃ states (set[str]) : Finite set of states (Q{q})
 ⁃ alphabets: (set[str]) : Finite set of input symbols (s)
 ⁃ Initial_state (str) : The start state (q0)
 ⁃ final_states (set[str]) : Finite set of accepted states
 ⁃ transition_functions (dict[tuple, str]) : Tuple holds (q, s) = q’

 We can add additional data such as is it a NDA or DFA, can be minimized or not etc. (bool?)

 We can use Discord user id as an identification that links the user to their FA history (long int). And the time they input the FA to be sorted by date.
