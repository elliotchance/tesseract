-- This file contains Lua code that is to be included in all compilations.

local function no_such_operator(left, operator, right)
    error(string.format('No such operator %s %s %s.', type(left), operator,
        type(right)))
end
