-- This file contains Lua code that is to be included in all compilations.

local function no_such_operator(left, operator, right)
    error(string.format('No such operator %s %s %s.', type(left), operator,
        type(right)))
end

local function no_such_function(name, arg)
    error(string.format('No such function %s(%s).', name, type(arg)))
end

local function no_such_type(type)
    error(string.format("No such type '%s'.", type))
end
