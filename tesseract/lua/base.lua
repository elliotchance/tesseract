-- This file contains Lua code that is to be included in all compilations.

local function no_such_operator(left, operator, right)
    error(string.format('No such operator %s %s %s.', type(left), operator,
        type(right)))
end

local function no_such_mono_operator(operator, right)
    error(string.format('No such operator %s %s.', operator, type(right)))
end

local function no_such_function(name, arg)
    error(string.format('No such function %s(%s).', name, type(arg)))
end

local function no_such_type(type)
    error(string.format("No such type '%s'.", type))
end

-- Gets all fields from a hash as a dictionary.
-- https://gist.github.com/klovadis/5170446
local function hgetall(key)
  local bulk = redis.call('HGETALL', key)
	local result = {}
	local nextkey
	for i, v in ipairs(bulk) do
		if i % 2 == 1 then
			nextkey = v
		else
			result[nextkey] = v
		end
	end
	return result
end
