## @brief Preprocesses dynamo script's input parameters
# Takes user input (left side) as input and splits it into pre-refactoring and post-refactoring user parameters
# @In array of user input parameters
# @OUT Tuple of 
# A text file's name containing all pre-refactoring user parameters as part of the name
# List of all the pre-refactoring user parameters in their original type
# List of all the post-refactoring user parameters in their original type

#-----------------------------------------------------------------------------------------------------------------#
# Constants...
PRE_FACTORING_INPUT_LENGTH = 6
BOTTLENECK_INDEX = 5

## 4th index left empty to be consistent with pre-refactoring file name
INPUT_NAMES = [
    "siteX" , "siteY" , "CORRWIDTH" , "NUMROOMS" , "" , "INCBNECK"
]

#-----------------------------------------------------------------------------------------------------------------#
# Helper functions...

## Converts a string to an integer
# @param int_as_string:str string to be converted
# @returns argument converted to an integer
# @raises ValueError
def convert_to_int(int_as_string) : 
    try : 
        return int(int_as_string)
    except : 
        raise ValueError(f"{int_as_string} cannot be converted to integer")

## Converts str to boolean : 
# @param bool_as_string:str string to be converted
# @returns argument converted to a boolean
# @note converted to integer first to counter edge case: "0" is casted to True
# @raises ValueError
def convert_to_bool(bool_as_string) : 
    try : 
        return bool(convert_to_int(bool_as_string))
    except ValueError as e : 
        if "False" in str(e) or "True" in str(e) : return bool(bool_as_string)
        else : raise ValueError("Argument string cannot be converted to boolean")
    
## Converts str to float : 
# @param float_as_string:str string to be converted
# @returns argument converted to a float
# @raises ValueError
def convert_to_float(float_as_string) : 
    try : 
        return float(float_as_string)
    except : 
        raise ValueError("Argument string cannot be converted to float")
    
## Converts user input from string to original types
# Splits input parameters to pre-refactoring (first 6 inputs) and post-refactoring (additional_input_as_string; remaining inputs) user parameters
# @uses convert_to_int(), convert_to_bool() , convert_to_float()
# @param input_as_string:list<string> list of inputs to be converted
# @param include_bottleneck_index<int> index of INCLUDE_BOTTLENECK, the only user input of type: bool
# @returns list of pre-factoring user input in original types, list of post-refactoring user input in original types
# @note refer to start of dynamo script for original types
# @raises IndexError
def convert_input_from_string(input_as_string , include_bottleneck_index) : 
    pre_refactoring_input_as_string , additional_input_as_string = input_as_string[: PRE_FACTORING_INPUT_LENGTH] , input_as_string[PRE_FACTORING_INPUT_LENGTH :]

    if include_bottleneck_index > (len(pre_refactoring_input_as_string) - 1) : 
        raise IndexError("include_bootleneck_index is out of bounds")
    
    return [
        convert_to_int(user_input) if u != include_bottleneck_index else convert_to_bool(user_input) for u, user_input in enumerate(pre_refactoring_input_as_string) 
    ] , [
        convert_to_float(user_input) for user_input in additional_input_as_string
    ]

## Generates name of the text file from user input parameters
# Adds pairs of names and parameters to a string and then returns string
# @param user_input:list values of input parameters to be included in file name
# @param input_names:list<str> names of input parameters to be included in file name
# @returns filename:str final filename
# @raises ValueError
def generate_file_name(user_input , input_names) : 
    if len(user_input) != len(input_names) : 
        raise ValueError("Unequal list lengths")

    file_name = "floorplan"

    for i in range(len(user_input)) :
        input_as_string = user_input[i]
        name_input_pair_as_string = f"_{input_names[i]}_{input_as_string}" if i != 4 else f"_{input_as_string}"
        file_name += name_input_pair_as_string

    file_name += ".txt"

    return file_name
#-----------------------------------------------------------------------------------------------------------------#
# Script...
pre_factoring_user_input , additional_user_input = convert_input_from_string(IN , BOTTLENECK_INDEX)

OUT = generate_file_name(pre_factoring_user_input , INPUT_NAMES) , pre_factoring_user_input , additional_user_input

print(OUT)