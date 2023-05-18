#-----------------------------------------------------------------------------------------------------------------#
# Helper functions...

## Converts str to float : 
# @param float_as_string:str string to be converted
# @returns argument converted to a float
# @raises ValueError
def convert_to_float(float_as_string) : 
    try : 
        return float(float_as_string)
    except : 
        raise ValueError("Argument string cannot be converted to float")

## Converts a list of values from meters to Revit units
# @param values_in_meter: list<float> list of values to be converted
# @returns values_in_revit_units: list<float> list of values in Revit units
# @note function works with a single float value as well, and returns a single value in that case
# @raises ValueError
def convert_to_revit_units(values_in_meter) : 
    if values_in_meter == None : 
        raise ValueError("Received a null value or list of values.")

    if not isinstance(values_in_meter , list) : 
        return convert_to_float(UnitUtils.ConvertToInternalUnits(values_in_meter , UnitTypeId.Meters))
    
    return [
        convert_to_float(UnitUtils.ConvertToInternalUnits(value, UnitTypeId.Meters)) for value in values_in_meter
    ]

