#!/usr/bin/env python3

# sudoku-solver-py is a program that solves sudoku puzzles
#   Copyright (C) 2021 Noah Stanford <noahstandingford@gmail.com>
#
#   sudoku-solver-py is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   sudoku-solver-py is distributed in the hope that it will be interesting and fun,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
The main module. This handles the overall logic of the project
"""

from typing import Any, Dict, List, Union
import copy
import random
import argparse

ESC = chr(27)
global max_guesses_per_roll
max_guesses_per_roll = 500


MAJOR_VERSION = '0'
MINOR_VERSION = '1'
MICRO_VERSION = '1'
VERSION = "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

ABOUT = f"""sudoku-solver-py {VERSION} is a program that solves sudoku puzzles
 
    Sudokus are entered through plain text files with periods for empty spaces and optional line separators
    Whitespace is ignored

    Example:

    -------------------------
    | 8 . . | . . . | . . . |
    | . . 3 | 6 . . | . . . |
    | . 7 . | . 9 . | 2 . . |
    -------------------------
    | . 5 . | . . 7 | . . . |
    | . . . | . 4 5 | 7 . . |
    | . . . | 1 . . | . 3 . |
    -------------------------
    | . . 1 | . . . | . 6 8 |
    | . . 8 | 5 . . | . 1 . |
    | . 9 . | . . . | 4 . . |
    -------------------------
    
  Copyright (C) 2021 Noah Stanford <noahstandingford@gmail.com>
  sudoku-solver-py is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  sudoku-solver-py is distributed in the hope that it will be interesting and fun,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# the value stored in E represents an empty space in the puzzle
E = '.'

def get_version() -> str:
    """Returns the current version of the package"""
    return VERSION

def wipe_screen() -> None:
    """Clears all text from the terminal"""
    print(ESC + "[H" + ESC + "[J", end="")

def square_single_members(i: int, j: int, board: List[List[Any]], squares: Dict[Any, Any]) -> List[Any]:
    """
    finds the solved elements in the sudoku that are in the same square as the given location and returns a list of their values
    squares is the hash table mapping each element to its square of nine
    """
    members = []
    for k in range(len(board)):
        for l in range(len(board[i])):
            if squares[f"{i}_{j}"] == squares[f"{k}_{l}"] and isinstance(board[k][l], int):
                members.append(board[k][l])
    return members


def list_diff(list1: List[Any], list2: List[Any]) -> List[Any]:
    """
    finds the difference of the unique elements in the given lists and returns it as a list
    returns list1 - list2
    """
    return list(set(list1) - set(list2))

def print_board(board: List[Any]) -> None:
    """
    prints out the given sudoku board in a pretty format
    """
    print("-" * 25)
    for i in range(len(board)):
        print("|", end=" ")
        for j in range(len(board[i])):
            if isinstance(board[i][j], int):
                print(board[i][j], end=" ")
            else:
                print(E, end=" ")
            if (j-2) % 3 == 0:
                print("|", end=" ")
        print()
        if (i-2) % 3 == 0:
            print("-" * 25)

def write_board_to_file(board: List[List[Any]], filename: str) -> None:
    """
    writes the given sudoku board to a file in a pretty format
    """
    
    out_file = open(filename, 'a')
    out_file.write("-" * 25)
    out_file.write("\n")
    for i in range(len(board)):
        out_file.write("| ")
        for j in range(len(board[i])):
            if isinstance(board[i][j], int):
                out_file.write(f"{board[i][j]} ")
            else:
                out_file.write(E + " ")
            if (j-2) % 3 == 0:
                out_file.write("| ")
        out_file.write("\n")
        if (i-2) % 3 == 0:
            out_file.write("-" * 25)
            out_file.write("\n")
    out_file.write("\n")
    out_file.close()

def verify_sudoku(board: List[List[Any]], squares: Dict[Any, Any]) -> bool:
    """
    Checks for whether or not the given sudoku board is solved. Returns True if solved, False if not
    squares is the hash table mapping each element to its square of nine
    """
    valid = True

    for i in range(len(board)):
        for j in range(len(board[i])):
            value = board[i][j]
            if not (isinstance(value, int) and 1 <= value <= 9):
                valid = False
                break

    if valid:  # check the small squares of 9 first
        for i in range(3):
            for j in range(3):
                neighbors = square_single_members(3*i, 3*j, board, squares)
                valid = len(neighbors) == len(set(neighbors))
                if not valid:
                    break

        if valid:  # if the squares pass checks rows next
            for i in range(len(board)):
                valid = len(board[i]) == len(set(board[i]))
                if not valid:
                    break
            if valid:  # if rows pass then check columns next
                for i in range(len(board[0])):
                    column = []
                    for j in range(len(board)):
                        column = column + [board[j][i]]
                    valid = len(column) == len(set(column))
                    if not valid:
                        break
    return valid

def try_to_solve_with_elimiation(board: List[List[Any]], squares: Dict[Any, Any], guess: int = -1, reroll: int = -1) -> List[Union[List[List[Any]], bool]]:
    """
    Attempts to solve a sudoku only making moves that must be correct given the intial board
    squares is the hash table mapping each element to its square of nine
    returns a list in the format [partialSudoku, solvedStatus] where partialSudoku is the attempted solution and solvedStatus is whether or not the sudoku is solved
    True means solved where False means unsolved
    """
    sudoku_board = copy.deepcopy(board)

    for i in range(len(sudoku_board)):
        # put together row list
        row_list = []
        for j in range(len(sudoku_board[i])):
            if isinstance(sudoku_board[i][j], int):
                row_list.append(sudoku_board[i][j])
        if len(row_list) != len(set(row_list)):
            return [sudoku_board, False]

    for j in range(len(sudoku_board[0])):
        # put together column list
        column_list = []
        for i in range(len(sudoku_board)):
            if isinstance(sudoku_board[i][j], int):
                column_list.append(sudoku_board[i][j])
        if len(column_list) != len(set(column_list)):
            return [sudoku_board, False]

    for i in range(len(sudoku_board)):
        for j in range(len(sudoku_board[i])):
            members = square_single_members(i, j, sudoku_board, squares)
            if len(members) != len(set(members)):
                return [sudoku_board, False]

    # print("I started solving")
    diffs = 1
    loop = 0
    while diffs > 0:
        diffs = 0
        for i in range(len(sudoku_board)):
            for j in range(len(sudoku_board[i])):
                # checks for multiple elements at that space
                if isinstance(sudoku_board[i][j], list) and len(sudoku_board[i][j]) > 1:
                    # eliminate an impossible value from the list

                    # use neighbor values to eliminate impossible values
                    members = square_single_members(i, j, sudoku_board, squares)
                    for member in members:
                        if member in sudoku_board[i][j]:
                            sudoku_board[i][j].remove(member)
                            diffs += 1
                    # use columns and rows also to eliminate
                    # use column to eliminate
                    for k in range(len(sudoku_board)):
                        if not isinstance(sudoku_board[k][j], list) and sudoku_board[k][j] in sudoku_board[i][j]:
                            sudoku_board[i][j].remove(sudoku_board[k][j])
                            diffs += 1
                    # use rows to eliminate
                    for k in range(len(sudoku_board[i])):
                        if not isinstance(sudoku_board[i][k], list) and sudoku_board[i][k] in sudoku_board[i][j]:
                            sudoku_board[i][j].remove(sudoku_board[i][k])
                            diffs += 1

                    # solve list based on based on being only one to hold an element relative to other lists

                    # put together column list
                    column_list = []
                    for k in range(len(sudoku_board)):
                        if isinstance(sudoku_board[k][j], list) and k != i:
                            column_list = column_list + sudoku_board[k][j]
                    # put together row list
                    row_list = []
                    for k in range(len(sudoku_board)):
                        if isinstance(sudoku_board[i][k], list) and k != j:
                            row_list = row_list + sudoku_board[i][k]

                    # put them all together
                    temp_list = members + column_list + row_list

                    # try one by one, then if that doesn't work just use a nonempty diff of all
                    element_diff = list_diff(sudoku_board[i][j], members)
                    if len(element_diff) == 1:
                        sudoku_board[i][j] = element_diff[0]
                        diffs += 1
                    else:
                        element_diff = list_diff(sudoku_board[i][j], column_list)
                        if len(element_diff) == 1:
                            sudoku_board[i][j] = element_diff[0]
                            diffs += 1
                        else:
                            element_diff = list_diff(sudoku_board[i][j], row_list)
                            if len(element_diff) == 1:
                                sudoku_board[i][j] = element_diff[0]
                                diffs += 1
                            else:
                                element_diff = list_diff(
                                    sudoku_board[i][j], temp_list)
                                if(len(element_diff) > 0):
                                    sudoku_board[i][j] = element_diff
                                    # diffs += 1

                # checks for list with single element at that space
                if isinstance(sudoku_board[i][j], list) and len(sudoku_board[i][j]) == 1:
                    sudoku_board[i][j] = sudoku_board[i][j][0]
                # if a space has no options, something must be wrong
                elif isinstance(sudoku_board[i][j], list) and len(sudoku_board[i][j]) == 0:
                    return [sudoku_board, False]
        
        # os.system("clear")
        wipe_screen() 
        print(f"Reroll {reroll}... Guess {guess}... Still solving... loop {loop}... {diffs} changes")
        loop += 1
        print_board(sudoku_board)
    print("Guess done")
    return [sudoku_board, verify_sudoku(sudoku_board, squares)]

def guess_sub_iterator(unknown_list: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
    """
    This function iterates over subguesses in the list of unknowns.
    """
    random.shuffle(unknown_list)
    for depth in range(len(unknown_list)+1):  # increase depth as needed
        depth_complete = False
        while not depth_complete:
            sub_unknowns = []
            # put together sublist for current depth and iteration
            for i in range(depth+1):
                sub_unknowns.append(copy.deepcopy(unknown_list[i]))

            # this is returning the current subguess and whether or not another guess is possible
            yield [copy.deepcopy(sub_unknowns), (unknown_list[-1]["iteration"]) < (unknown_list[-1]["count"] - 1)]

            for i in range(depth+1):
                if unknown_list[i]["iteration"] == (unknown_list[i]["count"] - 1):
                    unknown_list[i]["iteration"] = 0
                    if i == depth:
                        depth_complete = True
                        break
                elif unknown_list[i]["iteration"] < unknown_list[i]["count"]:
                    unknown_list[i]["iteration"] += 1
                    break
    yield [copy.deepcopy(sub_unknowns), False]


def guess_generator(in_board: List[List[Any]]) -> List[Union[List[List[Any]], bool]]:
    """
    Generates a board with a single element set as a guess that might be true. Returns a list with the guess and a boolean value in the format [board, True/False]
    The boolean value represents whether another guess exists after the current one. True means there is another, while False means there is not
    """
    board = copy.deepcopy(in_board)
    unknowns = []
    for i in range(len(board)):
        for j in range(len(board)):
            if isinstance(board[i][j], list):
                unknowns.append({"possible": board[i][j], "location": {"i": i, "j": j}, "count": len(board[i][j]), "iteration": 0})

    sub_iterator = guess_sub_iterator(copy.deepcopy(unknowns))

    has_next_guess = True
    while has_next_guess:
        [sub_guess, has_next_guess] = next(sub_iterator)
        for unknown in sub_guess:
            i = unknown["iteration"]
            board[unknown["location"]["i"]][unknown["location"]["j"]] = unknown["possible"][i]
        yield [board, True]
        board = copy.deepcopy(in_board)
    yield [board, False]


def solve_with_smart_guesses(board: List[List[Any]], squares: Dict[Any, Any]) -> List[Union[List[List[Any]], bool]]:
    """
    This function tries to solve a sudoku with a mix of guessing and elimination
    squares its the hash table mapping each element to its square of nine
    returns a list in the format [partialSudoku, solvedStatus] where partialSudoku is the attempted solution and solvedStatus is whether or not the sudoku is solved
    True means solved where False means unsolved
    """
    solved = False
    has_guess = True
    guesser = guess_generator(board)
    solution = board
    guess = 0
    reroll = 0
    while not solved and has_guess:
        # print(f"Guess {guess}")
        # make a feasible partial guess - better than naiive - reject obviously impossible options
        [temp_board, has_guess] = next(guesser)
        # attempt elimination solution
        [solution, solved] = try_to_solve_with_elimiation(temp_board, squares, guess, reroll)
        guess += 1
        
        if guess >= max_guesses_per_roll:
            reroll += 1
            guess = 0
            guesser = guess_generator(board)

    return [solution, solved]


def solve_reasonable_sudoku(board: List[List[Any]]) -> List[Union[List[List[Any]], bool]]:
    """
    Solves a sudoku that is reasonably solvable, with a smart mix of elimination and guessing
    returns a list in the format [partialSudoku, solvedStatus] where partialSudoku is the attempted solution and solvedStatus is whether or not the sudoku is solved
    True means solved where False means unsolved
    """
    squares = {}
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    squares[f"{3*i+k}_{3*j+l}"] = f"{i}_{j}"

    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] == E:
                board[i][j] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            elif not isinstance(board[i][j], int):
                return [board, False]
            elif board[i][j] < 1 or board[i][j] > 9:
                return [board, False]

    [partial_board, solved] = try_to_solve_with_elimiation(board, squares)
    final_board = partial_board
    if not solved:
        [final_board, solved] = solve_with_smart_guesses(partial_board, squares)
    return [final_board, solved]

def main():
    """
    The main function. The entry point of this program
    """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=ABOUT)
    parser.add_argument('file', type=str, help='The name of the sudoku text file')
    parser.add_argument('-o', '--out', type=str, help="Name of optional solution file output", default="")
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {VERSION}', help="Show program's version number and exit.")
    parser.add_argument('-m', '--max', type=int, help="Maximum number of guesses per roll", default=500)

    args = parser.parse_args()
   
    text_file = open(args.file, 'r')
    text_in = text_file.read()
    text_file.close()
    text_in = text_in.replace('-', '').replace('|', '') #Removes lines from input
    text_in = ''.join(text_in.split()) #Removes whitespace from input

    global max_guesses_per_roll 
    max_guesses_per_roll = args.max 
    original_sudoku_board = []
    i = 0
    for character in text_in:
        row = i // 9
        column = i % 9
        if column == 0:
            original_sudoku_board.append([])
        try:
            original_sudoku_board[row].append(int(character))
        except ValueError:
            original_sudoku_board[row].append(character)
        i += 1

    [final_board, solved] = solve_reasonable_sudoku(original_sudoku_board)

    print(f"Done... Solved: {solved}")
    if not solved:
        print("This puzzle is either unsolvable or infeasible to solve in reasonable time")
    print_board(final_board)
    if len(args.out) > 0:
        write_board_to_file(final_board, args.out)
    
if __name__ == '__main__':
    main()
