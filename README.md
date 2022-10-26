# Bachelor Thesis

## Dependencies
The only required dependency is an environment which is able to run docker containers and has access to docker-compose.

## Build instructions
- Make sure you are in the root of the project

### On Windows
- $ ./build.ps1

### On Linux
- $ ./build.sh

## Usage
- Make sure you are in the root of the project
- The run script converts everything within the "input" folder and the result will be found in the "output" folder.
- ! Attention ! The script clears the output folder for each run.
### On Windows
- $ ./run.ps1

### On Linux
- $ ./run.sh

### Running RQ Test
- $ ./run-tests.ps1 -rq <1-4>
- Input folders are named "rq<1-4>\_input"


