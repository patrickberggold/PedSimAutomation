## @brief Preprocesses input parameters
# Takes user input (left side) as input 
# Outputs filename (str) and input_params (list)

# Constants...
PRE_FACTORING_INPUT_LENGTH = 6
BOTTLENECK_INDEX = 5

# Helper functions...

## Converts a string to an integer
# @raises ValueError
def convert_to_int(int_as_string) : 
    try : 
        return int(int_as_string)
    except : 
        raise ValueError("Argument string cannot be converted to integer")

## Converts an integer to a string
def convert_to_string(string_as_int) : 
    return str(string_as_int)

## Converts str to boolean : 
# @raises ValueError
def convert_to_bool(bool_as_string) : 
    try : 
        return bool(int(bool_as_string))
    except : 
        raise ValueError("Argument string cannot be converted to boolean")
    
## Converts str to float : 
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
# @returns filename:str final filename
def generate_file_name(user_input) : 
    input_names = [
        "siteX" , "siteY" , "CORRWIDTH" , "NUMROOMS" , "" , "INCBNECK"
    ]

    file_name = "floorplan"

    for i in range(len(user_input)) :
        input_as_string = convert_to_string(user_input[i])
        name_input_pair_as_string = f"_{input_names[i]}_{input_as_string}" if i != 4 else f"_{input_as_string}"
        file_name += name_input_pair_as_string

    file_name += ".txt"

    return file_name

# Script...
pre_factoring_user_input , additional_user_input = convert_input_from_string(IN , BOTTLENECK_INDEX)

OUT = generate_file_name(pre_factoring_user_input) , pre_factoring_user_input , additional_user_input 